<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">批量归档</h1>
      <p class="page-desc">批量处理多张航拍图片，生成巡航分析报告</p>
    </div>

    <!-- Upload & control -->
    <div class="card batch-upload-card">
      <div
        class="batch-upload-area"
        :class="{ dragging }"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="handleDrop"
      >
        <input
          ref="batchInput"
          type="file"
          accept="image/*"
          multiple
          class="file-hidden"
          @change="handleFiles"
        />
        <template v-if="files.length === 0">
          <el-icon :size="44"><FolderOpened /></el-icon>
          <p class="batch-text">拖拽多张图片到此处，或点击选择</p>
          <p class="batch-hint">支持同时选择多张 JPG/PNG</p>
          <el-button type="primary" size="default" @click.stop="$refs.batchInput.click()">
            <el-icon><Plus /></el-icon>选择文件
          </el-button>
        </template>
        <template v-else>
          <div class="files-loaded">
            <el-icon :size="28" color="#27ae60"><CircleCheckFilled /></el-icon>
            <span>已加载 <strong>{{ files.length }}</strong> 张图片</span>
            <el-button size="small" plain @click.stop="clearFiles">清空</el-button>
            <el-button size="small" plain @click.stop="$refs.batchInput.click()">追加</el-button>
          </div>
        </template>
      </div>

      <div class="batch-actions" v-if="files.length > 0 && !batchData">
        <el-button type="primary" size="large" :loading="processing" @click="startBatch">
          <el-icon><VideoPlay /></el-icon>
          {{ processing ? '正在处理...' : '开始批量处理' }}
        </el-button>
      </div>
    </div>

    <!-- Progress (shown during processing) -->
    <div v-if="processing" class="card">
      <div class="card-header">
        <span class="card-title">处理进度</span>
        <span class="progress-text">请等待，GPU 正在加速推理...</span>
      </div>
      <el-progress :percentage="100" :indeterminate="true" :stroke-width="14" />
    </div>

    <!-- Report section (shown after processing) -->
    <div v-if="batchData" class="report-section">
      <h2 class="section-title">巡航分析报告</h2>

      <!-- Top stats -->
      <div class="report-stats-row">
        <div class="report-stat">
          <div class="rs-num">{{ batchData.total_images }}</div>
          <div class="rs-label">处理图片数</div>
        </div>
        <div class="report-stat">
          <div class="rs-num">{{ batchData.total_objects }}</div>
          <div class="rs-label">检测目标总数</div>
        </div>
        <div class="report-stat">
          <div class="rs-num">{{ batchData.total_time }}s</div>
          <div class="rs-label">总耗时</div>
        </div>
        <div class="report-stat">
          <div class="rs-num">{{ (batchData.total_objects / batchData.total_images).toFixed(1) }}</div>
          <div class="rs-label">平均目标数/图</div>
        </div>
      </div>

      <div class="report-grid">
        <!-- Pie chart: category distribution -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">目标类别分布</span>
          </div>
          <div class="chart-wrapper">
            <v-chart v-if="pieOption" :option="pieOption" autoresize class="pie-chart" />
            <div v-else class="empty-chart">暂无数据</div>
          </div>
        </div>

        <!-- Peak congestion -->
        <div class="card peak-card">
          <div class="card-header">
            <span class="card-title">车流密度极值</span>
            <el-tag v-if="batchData.peak_image" :type="peakTagType" size="small">
              {{ batchData.peak_image.congestion_level }}
            </el-tag>
          </div>
          <div v-if="batchData.peak_image" class="peak-content">
            <div class="peak-thumb" @click="previewPeakImage">
              <img
                v-if="peakImageSrc"
                :src="peakImageSrc"
                class="peak-thumb-img"
              />
              <el-icon v-else :size="40"><Picture /></el-icon>
            </div>
            <div class="peak-info">
              <div class="peak-number">{{ batchData.peak_image.total_objects }}</div>
              <div class="peak-label">峰值车辆数</div>
              <div class="peak-file">{{ batchData.peak_image.filename }}</div>
            </div>
          </div>
          <div v-else class="empty-inline">无检测目标</div>
        </div>
      </div>

      <!-- Image grid -->
      <h3 class="section-subtitle">检测结果详情</h3>
      <div class="result-grid">
        <div v-for="(item, i) in batchData.results" :key="i" class="result-card">
          <div class="rc-thumb">
            <img
              v-if="item.result_image_url"
              :src="item.result_image_url?.startsWith('http') ? item.result_image_url : 'http://localhost:8000' + item.result_image_url"
              class="rc-img"
            />
            <el-icon v-else :size="32"><Picture /></el-icon>
          </div>
          <div class="rc-info">
            <div class="rc-name">{{ item.filename }}</div>
            <div class="rc-meta">{{ item.total_objects }} 目标 · {{ item.detection_time }}s</div>
          </div>
        </div>
      </div>

      <!-- Download -->
      <div class="download-area">
        <el-button type="primary" size="large" @click="downloadReport">
          <el-icon><Download /></el-icon>打包下载检测结果
        </el-button>
        <p class="download-hint">TODO: 后端提供 ZIP 打包下载接口</p>
      </div>
    </div>

    <!-- Peak image preview dialog -->
    <el-dialog v-model="peakDialog" title="车流密度极值" width="800px">
      <img v-if="peakImageSrc" :src="peakImageSrc" class="peak-preview" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from "vue";
import { ElMessage } from "element-plus";
import { FolderOpened, Plus, Picture, Download, CircleCheckFilled, VideoPlay } from "@element-plus/icons-vue";
import VChart, { THEME_KEY } from "vue-echarts";
import { use } from "echarts/core";
import { PieChart, BarChart } from "echarts/charts";
import { TitleComponent, TooltipComponent, LegendComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { downloadResults } from "../api/detection";
import request from "../utils/request";

use([PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

const batchInput = ref(null);
const files = ref([]);
const processing = ref(false);
const batchData = ref(null);
const dragging = ref(false);
const peakDialog = ref(false);

/* ── Pie chart option ── */
const pieOption = computed(() => {
  if (!batchData.value?.category_distribution?.length) return null;
  const items = batchData.value.category_distribution;
  const LABELS = {
    car: "汽车", van: "面包车", truck: "卡车", bus: "公交车",
    motor: "摩托车", bicycle: "自行车", tricycle: "三轮车",
    "awning-tricycle": "遮阳三轮车", pedestrian: "行人", people: "人群",
  };
  const COLORS = ["#3b82f6","#8b5cf6","#f59e0b","#ef4444","#06b6d4","#10b981","#ec4899","#f97316","#6366f1","#84cc16"];
  return {
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    legend: { orient: "vertical", right: 10, top: "center", textStyle: { fontSize: 11 } },
    color: COLORS,
    series: [{
      type: "pie",
      radius: ["45%", "75%"],
      center: ["40%", "50%"],
      emphasis: { label: { fontSize: 16, fontWeight: "bold" } },
      label: {
        show: true,
        formatter: "{b}\n{d}%",
        fontSize: 10,
      },
      data: items.map(d => ({ name: LABELS[d.class_name] || d.class_name, value: d.count })),
    }],
  };
});

/* ── Peak image URL ── */
const peakImageSrc = computed(() => {
  if (!batchData.value?.peak_image) return null;
  const r = batchData.value.results.find(r => r.filename === batchData.value.peak_image.filename);
  const ru = r ? r.result_image_url : null;
  return ru ? (ru.startsWith("http") ? ru : "http://localhost:8000" + ru) : null;
});

const peakTagType = computed(() => {
  const l = batchData.value?.peak_image?.congestion_level;
  if (!l) return "info";
  if (l.includes("严重")) return "danger";
  if (l.includes("缓行")) return "warning";
  return "success";
});

/* ── File handling ── */
const handleDrop = (e) => {
  dragging.value = false;
  addFiles(Array.from(e.dataTransfer.files));
};

const handleFiles = (e) => {
  addFiles(Array.from(e.target.files));
  e.target.value = "";
};

const addFiles = (newFiles) => {
  const images = newFiles.filter(f => f.type.startsWith("image/"));
  if (images.length === 0) { ElMessage.warning("请选择图片文件"); return; }
  files.value = [...files.value, ...images];
};

const clearFiles = () => {
  files.value = [];
  batchData.value = null;
};

/* ── Batch detection ── */
const startBatch = async () => {
  if (files.value.length === 0) return;

  processing.value = true;
  batchData.value = null;

  try {
    const fd = new FormData();
    for (const f of files.value) {
      fd.append("files", f);
    }
    fd.append("model_name", "visdrone-v1");

    const res = await request({
      url: "/detection/batch",
      method: "post",
      data: fd,
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 300000,
    });

    if (res.success && res.data) {
      batchData.value = res.data;
      ElMessage.success(res.message);
    } else {
      ElMessage.error(res.message || "批量处理失败");
    }
  } catch (e) {
    ElMessage.error("批量处理失败，请检查后端是否运行");
  } finally {
    processing.value = false;
  }
};

const previewPeakImage = () => { peakDialog.value = true; };

const downloadReport = async () => {
  try {
    const blob = await downloadResults("");
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "detection_results.zip"; a.click();
    URL.revokeObjectURL(url);
    ElMessage.success("下载开始");
  } catch { ElMessage.error("下载失败"); }
};
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 18px; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-size: 14px; font-weight: 600; }

/* Upload */
.batch-upload-card { padding: 0; }
.batch-upload-area {
  padding: 40px; text-align: center; cursor: pointer;
  border: 2px dashed #d1d5db; border-radius: 10px; transition: all 0.2s;
}
.batch-upload-area:hover, .batch-upload-area.dragging { border-color: var(--primary); background: var(--primary-bg); }
.batch-text { font-size: 15px; font-weight: 500; margin-top: 12px; }
.batch-hint { font-size: 12px; color: var(--text-muted); margin: 6px 0 16px; }
.file-hidden { display: none; }
.files-loaded { display: flex; align-items: center; justify-content: center; gap: 12px; font-size: 14px; }

.batch-actions { padding: 0 20px 20px; text-align: center; }

/* Progress */
.progress-text { font-size: 13px; color: var(--text-secondary); }

/* Report */
.section-title { font-size: 18px; font-weight: 600; margin: 24px 0 16px; }
.section-subtitle { font-size: 15px; font-weight: 600; margin: 24px 0 12px; }

.report-stats-row { display: flex; gap: 16px; margin-bottom: 20px; }
.report-stat {
  flex: 1; background: #fff; border-radius: 10px; box-shadow: var(--card-shadow);
  padding: 16px 20px; text-align: center;
}
.rs-num { font-size: 26px; font-weight: 700; color: var(--primary); }
.rs-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

.report-grid { display: grid; grid-template-columns: 1fr 360px; gap: 20px; margin-bottom: 20px; }

/* Chart */
.chart-wrapper { height: 300px; display: flex; align-items: center; justify-content: center; }
.pie-chart { width: 100%; height: 100%; }
.empty-chart { color: var(--text-muted); font-size: 13px; }

/* Peak */
.peak-content { display: flex; align-items: center; gap: 16px; }
.peak-thumb {
  width: 120px; height: 90px; background: #f3f4f6; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; cursor: pointer; overflow: hidden;
}
.peak-thumb-img { width: 100%; height: 100%; object-fit: cover; }
.peak-number { font-size: 36px; font-weight: 700; color: var(--danger); line-height: 1.1; }
.peak-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.peak-file { font-size: 11px; color: var(--text-muted); margin-top: 2px; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Result grid */
.result-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.result-card {
  background: #fff; border-radius: 8px; box-shadow: var(--card-shadow);
  overflow: hidden; transition: box-shadow 0.2s; cursor: pointer;
}
.result-card:hover { box-shadow: var(--card-shadow-hover); }
.rc-thumb {
  height: 120px; background: #f9fafb; display: flex; align-items: center; justify-content: center; overflow: hidden;
}
.rc-img { width: 100%; height: 100%; object-fit: cover; }
.rc-info { padding: 10px 12px; }
.rc-name { font-size: 13px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rc-meta { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

/* Download */
.download-area { text-align: center; padding: 20px; }
.download-hint { font-size: 12px; color: var(--text-muted); margin-top: 8px; }

.peak-preview { width: 100%; border-radius: 6px; }
.empty-inline { text-align: center; font-size: 12px; color: var(--text-muted); padding: 24px; }
</style>
