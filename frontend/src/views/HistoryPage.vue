<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">历史台账</h1>
      <p class="page-desc">查看和管理所有历史检测记录，支持按类型、日期、拥堵评级筛选</p>
    </div>

    <!-- Filters -->
    <div class="filter-bar card">
      <div class="filter-row">
        <el-input v-model="query.keyword" placeholder="搜索文件名..." size="default" style="width:220px" clearable>
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="query.type" placeholder="检测类型" size="default" style="width:140px" clearable>
          <el-option label="全部" value="" />
          <el-option label="单图分析" value="single" />
          <el-option label="批量归档" value="batch" />
          <el-option label="视频分析" value="video" />
          <el-option label="实时监控" value="monitor" />
        </el-select>
        <el-select v-model="query.congestion" placeholder="拥堵评级" size="default" style="width:140px" clearable>
          <el-option label="全部" value="" />
          <el-option label="严重拥堵" value="high" />
          <el-option label="交通缓行" value="medium" />
          <el-option label="道路畅通" value="low" />
        </el-select>
        <el-date-picker v-model="query.dateRange" type="daterange" range-separator="至"
          start-placeholder="开始日期" end-placeholder="结束日期" size="default" style="width:260px" />
        <el-button type="primary" size="default" @click="fetchRecords">
          <el-icon><Search /></el-icon>查询
        </el-button>
        <el-button size="default" @click="resetQuery">重置</el-button>
      </div>
    </div>

    <!-- Data table -->
    <div class="card table-card">
      <el-table :data="records" stripe style="width:100%" v-loading="loading" empty-text="暂无检测记录">
        <el-table-column prop="detection_time" label="检测时间" width="170" sortable />
        <el-table-column prop="type" label="检测类型" width="110">
          <template #default="{ row }">
            <el-tag :type="typeTag(row.type)" size="small" effect="light">{{ typeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="filename" label="文件名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="model_name" label="模型" width="120" />
        <el-table-column prop="max_objects" label="最大目标数" width="110" sortable align="center" />
        <el-table-column prop="congestion" label="拥堵评级" width="110">
          <template #default="{ row }">
            <el-tag :type="congestionTag(row.congestion)" size="small" effect="dark">
              {{ row.congestion }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detection_time_sec" label="耗时(s)" width="90" align="center" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleDetail(row)">查看详情</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.pageSize"
          :total="total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next" size="default" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { Search } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import request from "../utils/request";

const loading = ref(false);
const records = ref([]);
const total = ref(0);

const query = reactive({
  keyword: "",
  type: "",
  congestion: "",
  dateRange: null,
  page: 1,
  pageSize: 10,
});

const typeTag = (t) => ({ single: "success", batch: "warning", video: "primary", monitor: "danger" }[t] || "info");
const typeLabel = (t) => ({ single: "单图分析", batch: "批量归档", video: "视频分析", monitor: "实时监控" }[t] || t);

const congestionTag = (c) => {
  if (c && c.includes("严重")) return "danger";
  if (c && c.includes("缓行")) return "warning";
  return "success";
};

const fetchRecords = async () => {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (query.keyword) params.append("keyword", query.keyword);
    if (query.type) params.append("type", query.type);
    if (query.congestion) params.append("congestion", query.congestion);
    if (query.dateRange && query.dateRange.length === 2) {
      params.append("startDate", query.dateRange[0].toISOString());
      params.append("endDate", query.dateRange[1].toISOString());
    }
    params.append("page", query.page);
    params.append("pageSize", query.pageSize);

    const res = await request.get("/detection/history?" + params.toString());
    records.value = res.data || [];
    total.value = res.total || 0;
  } catch (e) {
    records.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm("确定要删除这条检测记录吗？", "确认删除", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
    await request.delete(`/detection/history/${row.id}`);
    ElMessage.success("删除成功");
    fetchRecords();
  } catch (e) {
    if (e !== "cancel") {
      // error handled by interceptor
    }
  }
};

const handleDetail = async (row) => {
  try {
    const res = await request.get(`/detection/detail/${row.id}`);
    const detail = res.data;
    if (!detail) return;

    let detailHtml = `
      <div style="line-height:2;font-size:14px">
        <p><b>检测时间：</b>${detail.detection_time || ""}</p>
        <p><b>检测类型：</b>${typeLabel(detail.type)}</p>
        <p><b>文件名：</b>${detail.filename || "-"}</p>
        <p><b>模型：</b>${detail.model_name}</p>
        <p><b>总目标数：</b>${detail.total_objects}</p>
        <p><b>最大目标数：</b>${detail.max_objects}</p>
        <p><b>拥堵评级：</b>${detail.congestion}</p>
        <p><b>耗时：</b>${detail.detection_time_sec}s</p>
        ${detail.category_summary ? '<p><b>类别统计：</b>' + JSON.stringify(detail.category_summary) + '</p>' : ''}
      </div>`;

    ElMessageBox.alert(detailHtml, "检测详情", {
      dangerouslyUseHTMLString: true,
      confirmButtonText: "关闭",
    });
  } catch (e) {
    // handled
  }
};

const resetQuery = () => {
  query.keyword = "";
  query.type = "";
  query.congestion = "";
  query.dateRange = null;
  query.page = 1;
  fetchRecords();
};

fetchRecords();
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 18px; }

.filter-bar { margin-bottom: 16px; }
.filter-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

.table-card { padding: 0; }
.table-card .el-table { --el-table-header-bg-color: #f8fafc; }
.table-footer { display: flex; justify-content: flex-end; padding: 16px 18px; border-top: 1px solid var(--border-color); }
</style>
