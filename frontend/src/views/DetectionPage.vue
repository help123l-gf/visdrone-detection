<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">单图分析</h1>
      <p class="page-desc">上传无人机航拍图片，获取目标检测结果与交通态势评估报告</p>
    </div>

    <!-- Upload zone -->
    <div class="upload-zone" :class="{ 'has-file': originalImage }" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
      <input ref="fileInput" type="file" accept="image/*" class="file-hidden" @change="handleFileChange" />
      <template v-if="!originalImage">
        <el-icon :size="40"><UploadFilled /></el-icon>
        <p class="upload-text">点击或拖拽图片到此处上传</p>
        <p class="upload-hint">支持 JPG / PNG / WEBP，建议分辨率 ≥ 1920×1080</p>
      </template>
      <template v-else>
        <div class="uploaded-info">
          <el-tag type="success" effect="light" round>已加载图片</el-tag>
          <el-button type="primary" size="small" plain @click.stop="reupload">重新上传</el-button>
        </div>
      </template>
    </div>

    <!-- Model selector bar -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">检测模型：</span>
        <el-select v-model="selectedModel" size="small" style="width:160px">
          <el-option label="visdrone-v1 (YOLO11m)" value="visdrone-v1" />
          <el-option label="visdrone-v2 (待上线)" value="visdrone-v2" disabled />
        </el-select>
        <el-button type="primary" size="small" :loading="isDetecting" :disabled="!originalImage" @click="startDetection">
          <el-icon><Search /></el-icon>开始检测
        </el-button>
      </div>
    </div>

    <!-- Main content: left image + right dashboard -->
    <div class="detection-layout">
      <!-- Left: image -->
      <div class="image-panel card">
        <div class="card-header">
          <span class="card-title">检测画面</span>
          <el-tag v-if="detectionResult" type="success" effect="light" size="small">
            <el-icon><Check /></el-icon>检测完成
          </el-tag>
        </div>
        <div class="image-viewer">
          <img v-if="resultImage" :src="resultImage" alt="检测结果" class="main-image" />
          <img v-else-if="originalImage" :src="originalImage" alt="原始图片" class="main-image" />
          <div v-else class="image-placeholder">
            <el-icon :size="64"><Picture /></el-icon>
            <p>上传图片后预览</p>
          </div>
        </div>
        <div class="image-toggle" v-if="resultImage">
          <el-radio-group v-model="imageView" size="small">
            <el-radio-button value="result">检测结果</el-radio-button>
            <el-radio-button value="original">原图</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- Right: dashboard -->
      <div class="dashboard">
        <!-- Congestion rating -->
        <div class="card congestion-card" :class="congestionClass">
          <div class="congestion-badge">
            <span class="congestion-icon">{{ congestionIcon }}</span>
            <div>
              <div class="congestion-level">{{ congestionLabel }}</div>
              <div class="congestion-desc" v-if="detectionResult">
                检测到 {{ totalVehicles }} 辆车
              </div>
              <div class="congestion-desc" v-else>等待检测</div>
            </div>
          </div>
        </div>

        <!-- Category stats -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">分类统计</span>
          </div>
          <div class="stats-grid">
            <div v-for="cat in vehicleCategories" :key="cat.key" class="stat-item">
              <div class="stat-num" :style="{ color: cat.color }">{{ cat.count }}</div>
              <div class="stat-name">{{ cat.label }}</div>
            </div>
          </div>
          <div v-if="!detectionResult" class="empty-inline">上传图片并点击检测</div>
        </div>

        <!-- Detection list -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">识别清单</span>
            <span v-if="detectionResult" class="card-count">共 {{ detectionResult.total_objects }} 项</span>
          </div>
          <div v-if="detectionResult && detectionResult.boxes.length > 0" class="object-list">
            <div v-for="(box, i) in detectionResult.boxes.slice(0, 10)" :key="i" class="object-row">
              <span class="obj-name">{{ box.class_name }}</span>
              <el-progress :percentage="Math.round(box.confidence * 100)" :stroke-width="6" :show-text="false" class="obj-bar" />
              <span class="obj-conf">{{ (box.confidence * 100).toFixed(0) }}%</span>
            </div>
            <div v-if="detectionResult.boxes.length > 10" class="list-more">
              还有 {{ detectionResult.boxes.length - 10 }} 个目标...
            </div>
          </div>
          <div v-else class="empty-inline">暂无检测数据</div>
        </div>

        <!-- Detection info -->
        <div class="card" v-if="detectionResult">
          <div class="info-row">
            <span class="info-label">检测耗时</span>
            <span class="info-val">{{ detectionResult.detection_time }}s</span>
          </div>
          <div class="info-row">
            <span class="info-label">模型版本</span>
            <span class="info-val">{{ detectionResult.model_name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { ElMessage, ElLoading } from "element-plus";
import { UploadFilled, Picture, Search, Check } from "@element-plus/icons-vue";
import { detectSingleImage } from "../api/detection";

const selectedModel = ref("visdrone-v1");
const fileInput = ref(null);
const originalImage = ref("");
const resultImage = ref("");
const detectionResult = ref(null);
const isDetecting = ref(false);
const imageView = ref("result");

// Vehicle categories for stats
const vehicleCategories = computed(() => {
  const cats = [
    { key: "car", label: "汽车", color: "#3b82f6" },
    { key: "van", label: "面包车", color: "#8b5cf6" },
    { key: "truck", label: "卡车", color: "#f59e0b" },
    { key: "bus", label: "公交车", color: "#ef4444" },
  ];
  if (!detectionResult.value) return cats.map(c => ({ ...c, count: 0 }));

  return cats.map(c => ({
    ...c,
    count: detectionResult.value.boxes.filter(b =>
      b.class_name === c.key ||
      (c.key === "car" && ["car", "motor"].includes(b.class_name))
    ).length,
  }));
});

const totalVehicles = computed(() => {
  return vehicleCategories.value.reduce((s, c) => s + c.count, 0);
});

const congestionClass = computed(() => {
  if (!detectionResult.value) return "";
  const n = totalVehicles.value;
  if (n > 20) return "congested";
  if (n >= 10) return "slow";
  if (n > 0) return "clear";
  return "";
});

const congestionLabel = computed(() => {
  if (!detectionResult.value) return "就绪";
  const n = totalVehicles.value;
  if (n > 20) return "严重拥堵";
  if (n >= 10) return "交通缓行";
  if (n > 0) return "道路畅通";
  return "无车辆";
});

const congestionIcon = computed(() => {
  if (!detectionResult.value) return "—";
  const n = totalVehicles.value;
  if (n > 20) return "🚨";
  if (n >= 10) return "⚠️";
  return "✅";
});

const triggerUpload = () => fileInput.value?.click();
const reupload = () => { fileInput.value?.click(); };

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
  if (!file.type.startsWith("image/")) {
    ElMessage.warning("请上传图片文件");
    return;
  }
  originalImage.value = URL.createObjectURL(file);
  resultImage.value = "";
  detectionResult.value = null;
  // Store file for detection
  fileInput.value._pendingFile = file;
};

const startDetection = async () => {
  const file = fileInput.value?._pendingFile;
  if (!file) return;

  isDetecting.value = true;
  const loading = ElLoading.service({ lock: true, text: "正在分析中...", background: "rgba(0,0,0,0.6)" });

  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", selectedModel.value);

    const res = await detectSingleImage(formData);
    if (res.success && res.data) {
      detectionResult.value = res.data;
      resultImage.value = "http://localhost:8000" + res.data.result_image_url;
      imageView.value = "result";
      ElMessage.success(`检测完成，发现 ${res.data.total_objects} 个目标`);
    } else {
      ElMessage.error(res.message || "检测失败");
    }
  } catch (e) {
    ElMessage.error("检测请求失败，请检查后端是否运行");
  } finally {
    isDetecting.value = false;
    loading.close();
  }
};
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* Upload zone */
.upload-zone {
  border: 2px dashed #d1d5db;
  border-radius: 10px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 16px;
  background: #fff;
}
.upload-zone:hover { border-color: var(--primary); background: var(--primary-bg); }
.upload-zone.has-file { padding: 16px 24px; border-style: solid; border-color: var(--primary); }
.upload-text { font-size: 15px; font-weight: 500; margin-top: 12px; }
.upload-hint { font-size: 12px; color: var(--text-muted); margin-top: 6px; }
.uploaded-info { display: flex; align-items: center; justify-content: space-between; }
.file-hidden { display: none; }

/* Toolbar */
.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.toolbar-left { display: flex; align-items: center; gap: 12px; }
.toolbar-label { font-size: 13px; color: var(--text-secondary); }

/* Layout */
.detection-layout { display: flex; gap: 20px; }
.image-panel { flex: 1; min-width: 0; }
.dashboard { width: 340px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }

/* Image viewer */
.image-viewer {
  aspect-ratio: 16/10;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.main-image { width: 100%; height: 100%; object-fit: contain; }
.image-placeholder { text-align: center; color: #4a5568; }
.image-placeholder p { margin-top: 12px; font-size: 13px; }
.image-toggle { margin-top: 12px; text-align: center; }

/* Cards */
.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 18px; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-size: 14px; font-weight: 600; }
.card-count { font-size: 12px; color: var(--text-muted); }

/* Congestion card */
.congestion-card { text-align: center; padding: 24px; }
.congestion-card.clear { background: var(--traffic-bg-clear); border: 1px solid rgba(34,197,94,.3); }
.congestion-card.slow { background: var(--traffic-bg-slow); border: 1px solid rgba(245,158,11,.3); }
.congestion-card.congested { background: var(--traffic-bg-congested); border: 1px solid rgba(239,68,68,.3); }
.congestion-badge { display: flex; align-items: center; justify-content: center; gap: 12px; }
.congestion-icon { font-size: 32px; }
.congestion-level { font-size: 18px; font-weight: 700; }
.congestion-desc { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

/* Stats grid */
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.stat-item { text-align: center; padding: 10px 4px; background: #f9fafb; border-radius: 8px; }
.stat-num { font-size: 24px; font-weight: 700; }
.stat-name { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

/* Object list */
.object-list { display: flex; flex-direction: column; gap: 8px; }
.object-row { display: flex; align-items: center; gap: 10px; }
.obj-name { width: 72px; font-size: 12px; font-weight: 500; flex-shrink: 0; }
.obj-bar { flex: 1; }
.obj-conf { font-size: 12px; color: var(--text-secondary); width: 32px; text-align: right; }
.list-more { font-size: 12px; color: var(--text-muted); text-align: center; }

/* Info rows */
.info-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; }
.info-label { color: var(--text-secondary); }
.info-val { font-weight: 500; }

.empty-inline { text-align: center; font-size: 12px; color: var(--text-muted); padding: 24px 0; }
</style>
