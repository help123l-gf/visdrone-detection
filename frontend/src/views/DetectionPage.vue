<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">单图分析</h1>
      <p class="page-desc">上传无人机航拍图片，获取目标检测结果与交通态势评估报告</p>
    </div>

    <!-- Upload zone -->
    <div
      class="upload-zone"
      :class="{ 'has-file': originalSrc }"
      @click="triggerUpload"
      @dragover.prevent
      @drop.prevent="handleDrop"
    >
      <input ref="fileInput" type="file" accept="image/*" class="file-hidden" @change="handleFileChange" />
      <template v-if="!originalSrc">
        <el-icon :size="40"><UploadFilled /></el-icon>
        <p class="upload-text">点击或拖拽图片到此处上传</p>
        <p class="upload-hint">支持 JPG / PNG / WEBP，建议分辨率 ≥ 1920×1080</p>
      </template>
      <template v-else>
        <div class="uploaded-info">
          <el-tag type="success" effect="light" round>已加载图片</el-tag>
          <span class="uploaded-size">{{ imageWidth }} × {{ imageHeight }} px</span>
          <el-button type="primary" size="small" plain @click.stop="reupload">重新上传</el-button>
        </div>
      </template>
    </div>

    <!-- Model selector bar -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">检测模型：</span>
        <el-select v-model="selectedModel" size="small" style="width: 160px">
          <el-option label="visdrone-v1 (YOLO11m)" value="visdrone-v1" />
          <el-option label="visdrone-v2 (待上线)" value="visdrone-v2" disabled />
        </el-select>
        <el-button type="primary" size="small" :loading="detecting" :disabled="!originalSrc" @click="startDetection">
          <el-icon><Search /></el-icon>开始检测
        </el-button>
      </div>
      <div class="toolbar-right" v-if="originalSrc">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button value="compare"><el-icon><Switch /></el-icon>对比</el-radio-button>
          <el-radio-button value="result">标注</el-radio-button>
          <el-radio-button value="original">原图</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- Main content -->
    <div class="detection-layout">
      <!-- Left: image area -->
      <div class="image-panel card">
        <div class="card-header">
          <span class="card-title">检测画面</span>
          <el-tag v-if="result" type="success" effect="light" size="small">
            <el-icon><Check /></el-icon>检测完成
          </el-tag>
          <el-tag v-else-if="detecting" type="warning" effect="light" size="small">检测中...</el-tag>
        </div>

        <div class="image-viewer">
          <!-- 对比模式：左右分屏 -->
          <template v-if="viewMode === 'compare' && resultSrc">
            <div class="split-view">
              <div class="split-half">
                <img :src="originalSrc" class="split-img" />
                <span class="split-label">原图</span>
              </div>
              <div class="split-divider"></div>
              <div class="split-half">
                <img :src="resultSrc" class="split-img" />
                <span class="split-label">检测结果</span>
              </div>
            </div>
          </template>
          <!-- 标注结果 -->
          <img
            v-else-if="(viewMode === 'result' || viewMode === 'compare') && resultSrc"
            :src="resultSrc"
            class="main-image"
          />
          <!-- 原图 -->
          <img
            v-else-if="viewMode === 'original' && originalSrc"
            :src="originalSrc"
            class="main-image"
          />
          <!-- 分隔模式下只有原图没结果 -->
          <img
            v-else-if="viewMode === 'compare' && originalSrc"
            :src="originalSrc"
            class="main-image"
          />
          <!-- 占位 -->
          <div v-else class="image-placeholder">
            <el-icon :size="64"><Picture /></el-icon>
            <p>上传图片后预览</p>
          </div>
        </div>
      </div>

      <!-- Right: dashboard -->
      <div class="dashboard">
        <!-- ===== 拥堵评级 ===== -->
        <div class="card congestion-card" :class="congestion.level">
          <div class="congestion-badge">
            <span class="congestion-emoji">{{ congestion.emoji }}</span>
            <div>
              <div class="congestion-level">{{ congestion.label }}</div>
              <div class="congestion-desc" v-if="result">
                {{ totalVehicles }} 辆车 · 覆盖率 {{ (coverageRatio * 100).toFixed(1) }}%
              </div>
              <div class="congestion-desc" v-else>等待检测</div>
            </div>
          </div>
          <!-- 覆盖率指示条 -->
          <div v-if="result" class="coverage-bar">
            <div class="coverage-fill" :style="{ width: Math.min(coverageRatio * 100 * 6, 100) + '%', background: coverageColor }"></div>
            <div class="coverage-ticks">
              <span style="left: 20%">5%</span>
              <span style="left: 50%">15%</span>
              <span style="left: 80%">30%</span>
            </div>
          </div>
        </div>

        <!-- ===== 车辆类型分布（条形图） ===== -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">车辆类型分布</span>
            <span v-if="result" class="card-count">共 {{ totalVehicles }} 辆</span>
          </div>

          <div v-if="result && totalVehicles > 0" class="bar-chart">
            <div v-for="cat in vehicleCats" :key="cat.key" class="bar-row">
              <span class="bar-label" :style="{ color: cat.count > 0 ? cat.color : '#cbd5e1' }">{{ cat.label }}</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{
                    width: totalVehicles > 0 ? (cat.count / totalVehicles * 100) + '%' : '0%',
                    background: cat.color,
                  }"
                ></div>
              </div>
              <span class="bar-value" :style="{ color: cat.count > 0 ? cat.color : '#cbd5e1' }">
                {{ cat.count }} <span class="bar-pct">{{ totalVehicles > 0 ? (cat.count / totalVehicles * 100).toFixed(0) : 0 }}%</span>
              </span>
            </div>
          </div>
          <div v-else class="empty-inline">暂无检测数据</div>
        </div>

        <!-- ===== 目标明细（按类别聚合） ===== -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">目标明细</span>
          </div>
          <div v-if="result && result.boxes.length > 0" class="detail-table-wrapper">
            <table class="detail-table">
              <thead>
                <tr>
                  <th>类别</th>
                  <th>数量</th>
                  <th>占比</th>
                  <th>平均置信度</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in groupedDetails" :key="row.name">
                  <td>
                    <span class="detail-dot" :style="{ background: row.color }"></span>
                    {{ row.label }}
                  </td>
                  <td class="td-num">{{ row.count }}</td>
                  <td class="td-num">{{ row.pct }}%</td>
                  <td class="td-num">{{ row.avgConf }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-inline">暂无检测目标</div>
        </div>

        <!-- ===== 检测信息 ===== -->
        <div class="card" v-if="result">
          <div class="info-row">
            <span class="info-label">检测耗时</span>
            <span class="info-val">{{ result.detection_time }}s</span>
          </div>
          <div class="info-row">
            <span class="info-label">模型版本</span>
            <span class="info-val">{{ result.model_name }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">图片分辨率</span>
            <span class="info-val">{{ imageWidth }} × {{ imageHeight }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">车辆覆盖面积</span>
            <span class="info-val">{{ (coverageRatio * 100).toFixed(2) }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from "vue";
import { ElMessage, ElLoading } from "element-plus";
import { UploadFilled, Picture, Search, Check, Switch } from "@element-plus/icons-vue";
import { detectSingleImage } from "../api/detection";

const selectedModel = ref("visdrone-v1");
const fileInput = ref(null);
const originalSrc = ref("");
const resultSrc = ref("");
const result = ref(null);
const detecting = ref(false);
const viewMode = ref("compare");
const imageWidth = ref(0);
const imageHeight = ref(0);

/* ───────── image toggle fix ───────── */
// viewMode: "compare" | "result" | "original"
// image display logic handled purely in template via v-if chains

/* ── Vehicle category color map ── */
const CAT_COLORS = {
  car:        "#3b82f6",
  van:        "#8b5cf6",
  truck:      "#f59e0b",
  bus:        "#ef4444",
  motor:      "#06b6d4",
  bicycle:    "#10b981",
  tricycle:   "#ec4899",
  "awning-tricycle": "#f97316",
  pedestrian: "#6366f1",
  people:     "#84cc16",
};

const CAT_LABELS = {
  car: "汽车", van: "面包车", truck: "卡车", bus: "公交车",
  motor: "摩托车", bicycle: "自行车", tricycle: "三轮车",
  "awning-tricycle": "遮阳三轮车", pedestrian: "行人", people: "人群",
};

/* ── Vehicle categories for bar chart ── */
const vehicleCats = computed(() => {
  const keys = ["car", "van", "truck", "bus", "motor", "bicycle", "tricycle", "awning-tricycle"];
  if (!result.value) return keys.map(k => ({ key: k, label: CAT_LABELS[k] || k, count: 0, color: CAT_COLORS[k] || "#cbd5e1" }));

  return keys.map(k => {
    const count = result.value.boxes.filter(b => b.class_name === k).length;
    return { key: k, label: CAT_LABELS[k] || k, count, color: CAT_COLORS[k] || "#cbd5e1" };
  });
});

const totalVehicles = computed(() => vehicleCats.value.reduce((s, c) => s + c.count, 0));

/* ── Grouped detail table ── */
const groupedDetails = computed(() => {
  if (!result.value) return [];
  const boxes = result.value.boxes;
  const map = {};
  for (const b of boxes) {
    if (!map[b.class_name]) {
      map[b.class_name] = { count: 0, confSum: 0 };
    }
    map[b.class_name].count++;
    map[b.class_name].confSum += b.confidence;
  }
  return Object.entries(map).map(([name, v]) => ({
    name,
    label: CAT_LABELS[name] || name,
    color: CAT_COLORS[name] || "#6b7280",
    count: v.count,
    pct: ((v.count / boxes.length) * 100).toFixed(1),
    avgConf: ((v.confSum / v.count) * 100).toFixed(1),
  }));
});

/* ── Coverage ratio (bbox area / image area) ── */
const coverageRatio = computed(() => {
  if (!result.value || !imageWidth.value || !imageHeight.value) return 0;
  const imgArea = imageWidth.value * imageHeight.value;
  if (imgArea === 0) return 0;
  let bboxArea = 0;
  for (const b of result.value.boxes) {
    const w = b.x2 - b.x1;
    const h = b.y2 - b.y1;
    if (w > 0 && h > 0) bboxArea += w * h;
  }
  return bboxArea / imgArea;
});

const coverageColor = computed(() => {
  const r = coverageRatio.value;
  if (r > 0.30) return "#ef4444";
  if (r > 0.15) return "#f59e0b";
  return "#22c55e";
});

/* ── Density-based congestion ── */
const congestion = computed(() => {
  if (!result.value) return { level: "", label: "就绪", emoji: "—" };
  const ratio = coverageRatio.value;
  if (ratio > 0.30) return { level: "congested", label: "严重拥堵", emoji: "🚨" };
  if (ratio > 0.15) return { level: "slow",      label: "交通缓行", emoji: "⚠️" };
  if (totalVehicles.value > 0) return { level: "clear", label: "道路畅通", emoji: "✅" };
  return { level: "", label: "无车辆", emoji: "🔘" };
});

/* ── File handling ── */
const triggerUpload = () => fileInput.value?.click();
const reupload = () => fileInput.value?.click();

const handleDrop = (e) => {
  const file = e.dataTransfer.files[0];
  if (file) processFile(file);
};

const handleFileChange = (e) => {
  const file = e.target.files[0];
  if (file) processFile(file);
  e.target.value = "";
};

const processFile = (file) => {
  if (!file.type.startsWith("image/")) { ElMessage.warning("请上传图片文件"); return; }

  // 读取原始图片尺寸
  const img = new Image();
  img.onload = () => {
    imageWidth.value = img.naturalWidth;
    imageHeight.value = img.naturalHeight;
    URL.revokeObjectURL(img.src);
  };
  img.src = URL.createObjectURL(file);

  // 预览
  originalSrc.value = URL.createObjectURL(file);
  resultSrc.value = "";
  result.value = null;
  fileInput.value._pendingFile = file;
};

/* ── Detection ── */
const startDetection = async () => {
  const file = fileInput.value?._pendingFile;
  if (!file) return;

  detecting.value = true;
  const loading = ElLoading.service({ lock: true, text: "正在分析中...", background: "rgba(0,0,0,0.6)" });

  try {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("model_name", selectedModel.value);

    const res = await detectSingleImage(fd);
    if (res.success && res.data) {
      result.value = res.data;
      resultSrc.value = "http://localhost:8000" + res.data.result_image_url;
      viewMode.value = "compare";
      ElMessage.success(`检测完成，发现 ${res.data.total_objects} 个目标`);
    } else {
      ElMessage.error(res.message || "检测失败");
    }
  } catch {
    ElMessage.error("检测请求失败，请检查后端是否运行");
  } finally {
    detecting.value = false;
    loading.close();
  }
};
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* Upload */
.upload-zone {
  border: 2px dashed #d1d5db; border-radius: 10px; padding: 32px;
  text-align: center; cursor: pointer; transition: all 0.2s; margin-bottom: 16px; background: #fff;
}
.upload-zone:hover { border-color: var(--primary); background: var(--primary-bg); }
.upload-zone.has-file { padding: 16px 24px; border-style: solid; border-color: var(--primary); }
.upload-text { font-size: 15px; font-weight: 500; margin-top: 12px; }
.upload-hint { font-size: 12px; color: var(--text-muted); margin-top: 6px; }
.uploaded-info { display: flex; align-items: center; gap: 12px; }
.uploaded-size { font-size: 13px; color: var(--text-secondary); }
.file-hidden { display: none; }

/* Toolbar */
.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.toolbar-left { display: flex; align-items: center; gap: 12px; }
.toolbar-label { font-size: 13px; color: var(--text-secondary); }

/* Layout */
.detection-layout { display: flex; gap: 20px; }
.image-panel { flex: 1; min-width: 0; }
.dashboard { width: 360px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }

/* Image viewer */
.image-viewer {
  aspect-ratio: 16/10; background: #111827; border-radius: 8px;
  overflow: hidden; display: flex; align-items: center; justify-content: center;
}
.main-image { width: 100%; height: 100%; object-fit: contain; }
.image-placeholder { text-align: center; color: #6b7280; }
.image-placeholder p { margin-top: 12px; font-size: 13px; }

/* Split view */
.split-view { display: flex; width: 100%; height: 100%; }
.split-half { flex: 1; position: relative; display: flex; align-items: center; justify-content: center; }
.split-img { width: 100%; height: 100%; object-fit: contain; }
.split-label {
  position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%);
  background: rgba(0,0,0,.6); color: #fff; font-size: 12px; padding: 3px 12px; border-radius: 4px;
}
.split-divider { width: 2px; background: #374151; flex-shrink: 0; }

/* Cards */
.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 18px; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-size: 14px; font-weight: 600; }
.card-count { font-size: 12px; color: var(--text-muted); }

/* ── Congestion ── */
.congestion-card { text-align: center; padding: 20px; }
.congestion-card.clear  { background: var(--traffic-bg-clear);  border: 1px solid rgba(34,197,94,.25); }
.congestion-card.slow   { background: var(--traffic-bg-slow);   border: 1px solid rgba(245,158,11,.25); }
.congestion-card.congested { background: var(--traffic-bg-congested); border: 1px solid rgba(239,68,68,.25); }
.congestion-badge { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 12px; }
.congestion-emoji { font-size: 32px; }
.congestion-level { font-size: 18px; font-weight: 700; }
.congestion-desc { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

/* Coverage indicator bar */
.coverage-bar { position: relative; height: 6px; background: #e5e7eb; border-radius: 3px; margin: 0 12px; }
.coverage-fill { height: 100%; border-radius: 3px; transition: width 0.3s; max-width: 100%; }
.coverage-ticks {
  display: flex; justify-content: space-between; margin-top: 4px; padding: 0 6px;
  font-size: 10px; color: var(--text-muted);
}

/* ── Bar chart ── */
.bar-chart { display: flex; flex-direction: column; gap: 8px; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-label { width: 64px; font-size: 12px; font-weight: 500; flex-shrink: 0; }
.bar-track { flex: 1; height: 16px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; min-width: 0; }
.bar-value { width: 52px; font-size: 12px; font-weight: 600; text-align: right; flex-shrink: 0; }
.bar-pct { font-weight: 400; opacity: 0.6; }

/* ── Detail table ── */
.detail-table-wrapper { max-height: 220px; overflow-y: auto; }
.detail-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.detail-table th {
  text-align: left; padding: 6px 4px 8px; font-size: 11px; color: var(--text-muted);
  font-weight: 500; border-bottom: 1px solid var(--border-color);
}
.detail-table th:not(:first-child) { text-align: center; }
.detail-table td { padding: 7px 4px; border-bottom: 1px solid #f3f4f6; }
.detail-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.td-num { text-align: center; font-variant-numeric: tabular-nums; }

/* ── Info ── */
.info-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; }
.info-label { color: var(--text-secondary); }
.info-val { font-weight: 500; }

.empty-inline { text-align: center; font-size: 12px; color: var(--text-muted); padding: 24px 0; }
</style>
