<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">历史台账</h1>
      <p class="page-desc">查看和管理所有历史检测记录</p>
    </div>

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
        <el-button type="primary" size="default" @click="fetchRecords">
          <el-icon><Search /></el-icon>查询
        </el-button>
        <el-button size="default" @click="resetQuery">重置</el-button>
      </div>
    </div>

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
            <el-tag :type="congestionTag(row.congestion)" size="small" effect="dark">{{ row.congestion }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detection_time_sec" label="耗时(s)" width="90" align="center" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewRecord(row)">详情</el-button>
            <el-button type="danger" link size="small" @click="delRecord(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <el-pagination v-if="total > 0" :total="total" :page-size="query.pageSize"
          :current-page="query.page" @current-change="(p) => { query.page = p; fetchRecords(); }"
          layout="total, prev, pager, next" size="default" />
      </div>
    </div>

    <el-dialog v-model="detailVisible" title="检测详情" width="700px">
      <div v-if="detail" class="detail-body">
        <div class="detail-image">
          <img v-if="detail.result_url" :src="getImageUrl(detail.result_url)" class="detail-img" />
          <div v-else class="detail-noimg">
            <el-icon :size="48"><Picture /></el-icon>
            <p>无结果图片</p>
            <span>{{ detail.type === 'video' ? '视频标注文件未入库' : detail.type === 'batch' ? '批量结果未单独保存' : detail.type === 'monitor' ? '实时监控不保存图片' : '暂无图片' }}</span>
          </div>
        </div>
        <div class="detail-info">
          <div class="di-row"><span>检测类型</span><span>{{ typeLabel(detail.type) }}</span></div>
          <div class="di-row"><span>模型</span><span>{{ detail.model_name }}</span></div>
          <div class="di-row"><span>目标总数</span><span>{{ detail.total_objects }}</span></div>
          <div class="di-row"><span>耗时</span><span>{{ detail.detection_time }}s</span></div>
          <div class="di-row"><span>时间</span><span>{{ detail.created_at }}</span></div>
        </div>
        <div v-if="detail.boxes && detail.boxes.length > 0" class="detail-boxes">
          <span class="section-label">检测目标 ({{ detail.boxes.length }})</span>
          <div class="boxes-grid">
            <el-tag v-for="(b, i) in detail.boxes" :key="i" size="small" style="margin:2px">
              {{ b.class_name }} {{ (b.confidence * 100).toFixed(0) }}%
            </el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { ElMessage } from "element-plus";
import { Search } from "@element-plus/icons-vue";
import { ElMessageBox } from "element-plus";
import { getDetectionHistory, getDetectionDetail, deleteRecord } from "../api/detection";

const loading = ref(false);
const records = ref([]);
const total = ref(0);
const detailVisible = ref(false);
const detail = ref(null);

const query = reactive({ keyword: "", type: "", page: 1, pageSize: 10 });

const typeTag = (t) => ({ single: "success", batch: "warning", video: "primary", monitor: "danger" }[t] || "info");
const typeLabel = (t) => ({ single: "单图分析", batch: "批量归档", video: "视频分析", monitor: "实时监控" }[t] || t);
const congestionTag = (c) => {
  if (c?.includes("严重")) return "danger";
  if (c?.includes("缓行")) return "warning";
  return "success";
};

const fetchRecords = async () => {
  loading.value = true;
  try {
    const res = await getDetectionHistory({ page: query.page, page_size: query.pageSize, keyword: query.keyword, type: query.type });
    if (res.success) { records.value = res.data; total.value = res.total; }
  } catch { /* handled */ }
  finally { loading.value = false; }
};

const resetQuery = () => { query.keyword = ""; query.type = ""; query.page = 1; fetchRecords(); };

const getImageUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http")) return url; // MinIO direct URL
  return "http://localhost:8000/static/results/" + url;
};

const viewRecord = async (row) => {
  try {
    const res = await getDetectionDetail(row.id);
    if (res.success) {
      detail.value = res.data;
      detailVisible.value = true;
    }
  } catch { /* ignore */ }
};

const delRecord = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${row.filename}" 吗？`, "确认删除", { type: "warning" });
    const res = await deleteRecord(row.id);
    if (res.success) {
      ElMessage.success("已删除");
      fetchRecords();
    }
  } catch { /* cancelled or error */ }
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

.detail-body { display: flex; flex-direction: column; gap: 16px; }
.detail-image { background: #111; border-radius: 8px; overflow: hidden; display: flex; align-items: center; justify-content: center; min-height: 200px; }
.detail-img { max-width: 100%; max-height: 400px; object-fit: contain; }
.detail-noimg { text-align: center; color: var(--text-muted); padding: 40px; }
.detail-noimg p { margin: 12px 0 4px; font-size: 14px; }
.detail-noimg span { font-size: 12px; }
.detail-info { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.di-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
.di-row span:first-child { color: var(--text-secondary); }
.section-label { font-size: 13px; font-weight: 600; margin-bottom: 8px; display: block; }
.boxes-grid { display: flex; flex-wrap: wrap; gap: 4px; max-height: 240px; overflow-y: auto; }
</style>
