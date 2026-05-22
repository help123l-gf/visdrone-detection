<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">单图分析</h1>
      <p class="page-desc">上传无人机航拍图片，获取目标检测结果与交通态势评估报告</p>
    </div>

    <!-- Upload -->
    <div class="upload-zone" :class="{ 'has-file': originalSrc }" @click="triggerUpload"
      @dragover.prevent @drop.prevent="handleDrop">
      <input ref="fileInput" type="file" accept="image/*" class="file-hidden" @change="handleFileChange" />
      <template v-if="!originalSrc">
        <el-icon :size="40"><UploadFilled /></el-icon>
        <p class="upload-text">点击或拖拽图片到此处上传</p>
        <p class="upload-hint">支持 JPG / PNG / WEBP</p>
      </template>
      <template v-else>
        <div class="uploaded-info">
          <el-tag type="success" effect="light" round>已加载图片</el-tag>
          <span class="uploaded-size">{{ imageWidth }} × {{ imageHeight }} px</span>
          <el-button type="primary" size="small" plain @click.stop="reupload">重新上传</el-button>
        </div>
      </template>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">检测模型：</span>
        <el-select v-model="selectedModel" size="small" style="width:160px">
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

    <div class="detection-layout">
      <!-- ============ LEFT: image ============ -->
      <div class="image-panel card">
        <div class="card-header">
          <span class="card-title">检测画面</span>
          <el-tag v-if="result" type="success" effect="light" size="small"><el-icon><Check /></el-icon>检测完成</el-tag>
          <el-tag v-else-if="detecting" type="warning" effect="light" size="small">检测中...</el-tag>
        </div>
        <div class="image-viewer">
          <template v-if="viewMode === 'compare' && resultSrc">
            <div class="split-view">
              <div class="split-half"><img :src="originalSrc" class="split-img" /><span class="split-label">原图</span></div>
              <div class="split-divider"></div>
              <div class="split-half"><img :src="resultSrc" class="split-img" /><span class="split-label">标注</span></div>
            </div>
          </template>
          <img v-else-if="(viewMode === 'result' || viewMode === 'compare') && resultSrc" :src="resultSrc" class="main-image" />
          <img v-else-if="viewMode === 'original' && originalSrc" :src="originalSrc" class="main-image" />
          <img v-else-if="viewMode === 'compare' && originalSrc" :src="originalSrc" class="main-image" />
          <div v-else class="image-placeholder"><el-icon :size="64"><Picture /></el-icon><p>上传图片后预览</p></div>
        </div>
      </div>

      <!-- ============ RIGHT: dashboard ============ -->
      <div class="dashboard">

        <!-- ═══ 拥堵评级 ═══ -->
        <div class="card congestion-card" :class="congestion.level">
          <div class="congestion-main">
            <span class="congestion-emoji">{{ congestion.emoji }}</span>
            <div>
              <div class="congestion-level">{{ congestion.label }}</div>
              <div class="congestion-sub" v-if="result">
                {{ (clustering.ratio * 100).toFixed(0) }}% 车辆聚集 · {{ clustering.trafficClusterCount }} 个交通聚类 · 车距 {{ clustering.avgSpacing }}x
                <span v-if="clustering.clusterCount - clustering.trafficClusterCount > 0" style="color:var(--text-muted)">（已过滤 {{ clustering.clusterCount - clustering.trafficClusterCount }} 个疑似停车线）</span>
              </div>
              <div class="congestion-sub" v-else>等待检测</div>
            </div>
          </div>
          <div class="congestion-diagnosis" v-if="result && trafficDiagnosis">
            {{ trafficDiagnosis }}
          </div>
        </div>

        <!-- ═══ 车辆分布特征 ═══ -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">车辆分布特征</span>
            <el-tag v-if="result && clustering.level" :type="clustering.level === 'dense' ? 'danger' : clustering.level === 'moderate' ? 'warning' : 'success'" size="small" effect="dark">
              {{ clustering.label }}
            </el-tag>
          </div>
          <div v-if="result && totalVehicles > 0" class="dist-panel">
            <div class="dist-gauge">
              <div class="gauge-bar">
                <div class="gauge-fill" :style="{ width: (clustering.ratio * 100) + '%', background: clustering.level === 'dense' ? '#ef4444' : clustering.level === 'moderate' ? '#f59e0b' : '#22c55e' }"></div>
              </div>
              <div class="gauge-ticks">
                <span>0%</span><span>45%</span><span>75%</span><span>100%</span>
              </div>
              <div class="gauge-label">交通聚类率（已剔除线性排列的疑似路边停车）</div>
            </div>
            <div class="dist-metrics">
              <div class="dm-item">
                <span class="dm-val" :style="{ color: clustering.trafficClusterCount > 0 ? '#f59e0b' : '#22c55e' }">{{ clustering.trafficClusterCount }}</span>
                <span class="dm-lbl">交通聚类</span>
                <span v-if="clustering.clusterCount - clustering.trafficClusterCount > 0" class="dm-note">含{{ clustering.clusterCount - clustering.trafficClusterCount }}停车线</span>
              </div>
              <div class="dm-item">
                <span class="dm-val">{{ clustering.avgSpacing }}x</span>
                <span class="dm-lbl">平均车距</span>
              </div>
              <div class="dm-item">
                <span class="dm-val">{{ totalVehicles }}</span>
                <span class="dm-lbl">车辆总数</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-inline">暂无检测数据</div>
        </div>

        <!-- ═══ 车辆类型分布 ═══ -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">车辆类型分布</span>
            <span v-if="result" class="card-count">共 {{ totalVehicles }} 辆</span>
          </div>
          <div v-if="result && totalVehicles > 0" class="bar-chart">
            <div v-for="cat in vehicleCats" :key="cat.key" class="bar-row">
              <span class="bar-label" :style="{ color: cat.count > 0 ? cat.color : '#cbd5e1' }">{{ cat.label }}</span>
              <div class="bar-track"><div class="bar-fill" :style="{ width: totalVehicles ? (cat.count/totalVehicles*100)+'%' : '0%', background: cat.color }"></div></div>
              <span class="bar-value" :style="{ color: cat.count > 0 ? cat.color : '#cbd5e1' }">{{ cat.count }} <span class="bar-pct">{{ totalVehicles ? (cat.count/totalVehicles*100).toFixed(0) : 0 }}%</span></span>
            </div>
          </div>
          <div v-else class="empty-inline">暂无检测数据</div>
        </div>

        <!-- ═══ 车辆规模构成 ═══ -->
        <div class="card">
          <div class="card-header"><span class="card-title">车辆规模构成</span></div>
          <div v-if="result && totalVehicles > 0">
            <div class="size-row" v-for="g in sizeGroups" :key="g.label">
              <span class="size-label">{{ g.label }}</span>
              <span class="size-desc">{{ g.desc }}</span>
              <div class="size-track"><div class="size-fill" :style="{ width: totalVehicles ? (g.count/totalVehicles*100)+'%' : '0%', background: g.color }"></div></div>
              <span class="size-num" :style="{ color: g.color }">{{ g.count }}</span>
            </div>
          </div>
          <div v-else class="empty-inline">暂无检测数据</div>
        </div>

        <!-- ═══ 目标明细 ═══ -->
        <div class="card">
          <div class="card-header"><span class="card-title">目标明细</span></div>
          <div v-if="result && result.boxes.length > 0" class="detail-table-wrapper">
            <table class="detail-table">
              <thead><tr><th>类别</th><th>数量</th><th>占比</th><th>均置信度</th></tr></thead>
              <tbody>
                <tr v-for="row in groupedDetails" :key="row.name">
                  <td><span class="detail-dot" :style="{ background: row.color }"></span>{{ row.label }}</td>
                  <td class="td-num">{{ row.count }}</td>
                  <td class="td-num">{{ row.pct }}%</td>
                  <td class="td-num">{{ row.avgConf }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-inline">暂无检测目标</div>
        </div>

        <!-- ═══ 检测信息 ═══ -->
        <div class="card" v-if="result">
          <div class="info-row"><span class="info-label">检测耗时</span><span class="info-val">{{ result.detection_time }}s</span></div>
          <div class="info-row"><span class="info-label">模型版本</span><span class="info-val">{{ result.model_name }}</span></div>
          <div class="info-row"><span class="info-label">图片分辨率</span><span class="info-val">{{ imageWidth }} × {{ imageHeight }}</span></div>
          <div class="info-row"><span class="info-label">交通聚类率</span><span class="info-val">{{ (clustering.ratio * 100).toFixed(0) }}%</span></div>
          <div class="info-row" v-if="clustering.clusterCount - clustering.trafficClusterCount > 0"><span class="info-label">已过滤停车线</span><span class="info-val">{{ clustering.clusterCount - clustering.trafficClusterCount }} 组</span></div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
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

/* ── Constants ── */
const CAT_COLORS = {
  car:"#3b82f6", van:"#8b5cf6", truck:"#f59e0b", bus:"#ef4444",
  motor:"#06b6d4", bicycle:"#10b981", tricycle:"#ec4899",
  "awning-tricycle":"#f97316", pedestrian:"#6366f1", people:"#84cc16",
};
const CAT_LABELS = {
  car:"汽车", van:"面包车", truck:"卡车", bus:"公交车",
  motor:"摩托车", bicycle:"自行车", tricycle:"三轮车",
  "awning-tricycle":"遮阳三轮车", pedestrian:"行人", people:"人群",
};

/* ── Vehicle cats for bar chart ── */
const vehicleCats = computed(() => {
  const keys = ["car","van","truck","bus","motor","bicycle","tricycle","awning-tricycle"];
  if (!result.value) return keys.map(k=>({ key:k, label:CAT_LABELS[k]||k, count:0, color:CAT_COLORS[k]||"#cbd5e1" }));
  return keys.map(k=>{
    const count = result.value.boxes.filter(b=>b.class_name===k).length;
    return { key:k, label:CAT_LABELS[k]||k, count, color:CAT_COLORS[k]||"#cbd5e1" };
  });
});
const totalVehicles = computed(()=> vehicleCats.value.reduce((s,c)=>s+c.count,0));

/* ── Grouped detail table ── */
const groupedDetails = computed(()=>{
  if (!result.value) return [];
  const boxes = result.value.boxes;
  const map = {};
  for (const b of boxes) {
    if (!map[b.class_name]) map[b.class_name] = { count:0, confSum:0 };
    map[b.class_name].count++;
    map[b.class_name].confSum += b.confidence;
  }
  return Object.entries(map).map(([name,v])=>({
    name, label:CAT_LABELS[name]||name, color:CAT_COLORS[name]||"#6b7280",
    count:v.count, pct:((v.count/boxes.length)*100).toFixed(1),
    avgConf:((v.confSum/v.count)*100).toFixed(1),
  }));
});

/* ── Clustering: pairwise width normalization + linear cluster filter ── */
const clustering = computed(() => {
  if (!result.value || result.value.boxes.length < 2) {
    return { ratio: 0, clusterCount: 0, avgSpacing: 0, trafficClusterCount: 0, label: "无数据", level: "" };
  }
  const boxes = result.value.boxes;
  const n = boxes.length;

  const widths = boxes.map(b => Math.max(b.x2 - b.x1, 1));
  const centerX = boxes.map(b => (b.x1 + b.x2) / 2);
  const centerY = boxes.map(b => (b.y1 + b.y2) / 2);

  // Nearest-neighbor: normalize by pairwise average width
  const nnDistances = [];
  for (let i = 0; i < n; i++) {
    let minDist = Infinity;
    for (let j = 0; j < n; j++) {
      if (i === j) continue;
      const d = Math.hypot(centerX[i] - centerX[j], centerY[i] - centerY[j]);
      const ref = (widths[i] + widths[j]) / 2;
      const normalized = d / ref;
      if (normalized < minDist) minDist = normalized;
    }
    nnDistances.push(minDist);
  }

  // Build clusters
  const CLUSTER_THRESHOLD = 2.5;
  const visited = new Array(n).fill(false);
  const clusters = []; // each: { indices[], isLinear }

  for (let i = 0; i < n; i++) {
    if (visited[i]) continue;
    const queue = [i];
    visited[i] = true;
    const members = [];
    while (queue.length) {
      const cur = queue.pop();
      members.push(cur);
      for (let j = 0; j < n; j++) {
        if (visited[j]) continue;
        const pixelDist = Math.hypot(centerX[cur] - centerX[j], centerY[cur] - centerY[j]);
        const ref = (widths[cur] + widths[j]) / 2;
        if (pixelDist / ref < CLUSTER_THRESHOLD) {
          visited[j] = true;
          queue.push(j);
        }
      }
    }
    if (members.length >= 3) {
      clusters.push(members);
    }
  }

  // Filter: detect linear clusters (parked cars along curb/street)
  // Use PCA: ratio of eigenvalues of covariance matrix > 4 → linear (parked)
  const trafficClusters = [];
  for (const members of clusters) {
    if (members.length < 5) { trafficClusters.push(members); continue; } // too small to judge

    const xs = members.map(k => centerX[k]);
    const ys = members.map(k => centerY[k]);
    const mx = xs.reduce((a, x) => a + x, 0) / xs.length;
    const my = ys.reduce((a, y) => a + y, 0) / ys.length;

    let covXX = 0, covYY = 0, covXY = 0;
    for (let k = 0; k < xs.length; k++) {
      const dx = xs[k] - mx, dy = ys[k] - my;
      covXX += dx * dx;
      covYY += dy * dy;
      covXY += dx * dy;
    }
    covXX /= xs.length; covYY /= xs.length; covXY /= xs.length;

    // Eigenvalues of [[covXX, covXY], [covXY, covYY]]
    const trace = covXX + covYY;
    const det = covXX * covYY - covXY * covXY;
    const discriminant = Math.sqrt(Math.max(trace * trace - 4 * det, 0));
    const lambda1 = (trace + discriminant) / 2;
    const lambda2 = (trace - discriminant) / 2;
    // Elongation ratio (handle degenerate cases)
    const elongation = lambda2 > 1e-6 ? lambda1 / lambda2 : 999;

    if (elongation > 4) {
      // Linear cluster — likely parked, not traffic
      continue;
    }
    trafficClusters.push(members);
  }

  // Count only traffic clusters (non-linear)
  const trafficClusterCount = trafficClusters.length;
  let trafficClusteredVehicles = 0;
  const trafficSet = new Set(trafficClusters.flat());
  for (const members of trafficClusters) {
    trafficClusteredVehicles += members.length;
  }

  const ratio = n > 0 ? trafficClusteredVehicles / n : 0;
  const allClusteredCount = clusters.reduce((s, c) => s + c.length, 0);
  const rawRatio = n > 0 ? allClusteredCount / n : 0;
  const avgSpacing = nnDistances.reduce((a, d) => a + d, 0) / nnDistances.length;

  let label, level;
  if (ratio >= 0.75)      { label = "密集聚集"; level = "dense"; }
  else if (ratio >= 0.45) { label = "局部聚集"; level = "moderate"; }
  else                     { label = "均匀分散"; level = "sparse"; }

  return { ratio, clusterCount: clusters.length, trafficClusterCount, avgSpacing: Math.round(avgSpacing * 10) / 10, label, level, rawRatio };
});

/* ── Congestion: relaxed + linear cluster excluded ── */
const congestion = computed(() => {
  if (!result.value) return { level: "", label: "就绪", emoji: "—" };
  const { ratio, clusterCount, trafficClusterCount } = clustering.value;
  if (ratio >= 0.75) return { level: "congested", label: "严重拥堵", emoji: "🚨" };
  if (ratio >= 0.45) return { level: "slow",      label: "交通缓行", emoji: "⚠️" };
  if (totalVehicles.value > 0) return { level: "clear", label: "道路畅通", emoji: "✅" };
  return { level: "", label: "无车辆", emoji: "🔘" };
});

/* ── Traffic diagnosis text ── */
const trafficDiagnosis = computed(() => {
  if (!result.value || totalVehicles.value === 0) return "";
  const { ratio, clusterCount, trafficClusterCount, avgSpacing, rawRatio } = clustering.value;
  const parts = [];
  const parkedFiltered = clusterCount - trafficClusterCount;

  if (ratio >= 0.75) {
    parts.push(`${(ratio*100).toFixed(0)}% 车辆形成非线性的交通聚类（${trafficClusterCount} 个），车距仅 ${avgSpacing}x，存在拥堵风险。`);
  } else if (ratio >= 0.45) {
    parts.push(`约 ${(ratio*100).toFixed(0)}% 车辆呈团状聚集（${trafficClusterCount} 个交通聚类），部分区域车流较密。`);
  } else if (totalVehicles.value > 0) {
    parts.push(`车辆间距充足（平均 ${avgSpacing}x 车宽），分布均匀，通行顺畅。`);
  }

  if (parkedFiltered > 0) {
    parts.push(`已过滤 ${parkedFiltered} 个线性排列的聚类（疑似路边停车），不计入拥堵评估。`);
  }

  if (totalVehicles.value > 30 && ratio < 0.45) {
    parts.push(`画面车辆较多（${totalVehicles.value}辆），但间距合理，未形成拥堵。`);
  }

  return parts.join(" ");
});

/* ── Vehicle size groups (bbox area in px²) ── */
const sizeGroups = computed(()=>{
  if (!result.value) return [];
  const boxes = result.value.boxes;
  const groups = { small: { label:"小型目标", desc:"远处/小型车辆 (< 2000px²)", count:0, color:"#3b82f6" },
                   medium:{ label:"中型目标", desc:"中距车辆 (2000–8000px²)",  count:0, color:"#f59e0b" },
                   large: { label:"大型目标", desc:"近处/大型车辆 (> 8000px²)", count:0, color:"#ef4444" } };
  for (const b of boxes) {
    const area = (b.x2-b.x1)*(b.y2-b.y1);
    if (area<2000) groups.small.count++;
    else if (area<8000) groups.medium.count++;
    else groups.large.count++;
  }
  return [groups.small, groups.medium, groups.large].filter(g=>g.count>0);
});

/* ── File handling ── */
const triggerUpload = ()=> fileInput.value?.click();
const reupload = ()=> fileInput.value?.click();
const handleDrop = (e)=>{ const f=e.dataTransfer.files[0]; if(f) processFile(f); };
const handleFileChange = (e)=>{ const f=e.target.files[0]; if(f) processFile(f); e.target.value=""; };

const processFile = (file)=>{
  if(!file.type.startsWith("image/")){ ElMessage.warning("请上传图片文件"); return; }
  const img=new Image();
  img.onload=()=>{ imageWidth.value=img.naturalWidth; imageHeight.value=img.naturalHeight; URL.revokeObjectURL(img.src); };
  img.src=URL.createObjectURL(file);
  originalSrc.value=URL.createObjectURL(file);
  resultSrc.value=""; result.value=null;
  fileInput.value._pendingFile=file;
};

/* ── Detection ── */
const startDetection = async ()=>{
  const file=fileInput.value?._pendingFile; if(!file) return;
  detecting.value=true;
  const loading=ElLoading.service({ lock:true, text:"正在分析中...", background:"rgba(0,0,0,0.6)" });
  try {
    const fd=new FormData(); fd.append("file",file); fd.append("model_name",selectedModel.value);
    const res=await detectSingleImage(fd);
    if(res.success&&res.data){
      result.value=res.data; resultSrc.value="http://localhost:8000"+res.data.result_image_url;
      viewMode.value="compare";
      ElMessage.success(`检测完成，发现 ${res.data.total_objects} 个目标`);
    }else{ ElMessage.error(res.message||"检测失败"); }
  }catch{ ElMessage.error("检测请求失败，请检查后端是否运行"); }
  finally{ detecting.value=false; loading.close(); }
};
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.page-header { margin-bottom: 16px; flex-shrink: 0; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* Upload */
.upload-zone { border:2px dashed #d1d5db; border-radius:10px; padding:20px; text-align:center; cursor:pointer; transition:all .2s; margin-bottom:12px; background:#fff; flex-shrink:0; }
.upload-zone:hover { border-color:var(--primary); background:var(--primary-bg); }
.upload-zone.has-file { padding:12px 20px; border-style:solid; border-color:var(--primary); }
.upload-text { font-size:14px; font-weight:500; margin-top:8px; }
.upload-hint { font-size:12px; color:var(--text-muted); margin-top:4px; }
.uploaded-info { display:flex; align-items:center; gap:12px; }
.uploaded-size { font-size:13px; color:var(--text-secondary); }
.file-hidden { display:none; }

/* Toolbar */
.toolbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; flex-shrink:0; }
.toolbar-left { display:flex; align-items:center; gap:12px; }
.toolbar-label { font-size:13px; color:var(--text-secondary); }

/* Layout — fills remaining viewport, no page-level scroll */
.detection-layout { flex: 1; display: flex; gap: 20px; min-height: 0; overflow: hidden; }
.image-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; }
.image-panel .card-header { flex-shrink: 0; }
.dashboard { width: 380px; flex-shrink: 0; overflow-y: auto; overflow-x: hidden; display: flex; flex-direction: column; gap: 14px; padding-right: 4px; }

/* Image viewer — fills remaining space in left panel */
.image-viewer { flex: 1; min-height: 200px; background: #111827; border-radius: 8px; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.main-image { width:100%; height:100%; object-fit:contain; }
.image-placeholder { text-align:center; color:#6b7280; }
.image-placeholder p { margin-top:12px; font-size:13px; }
.split-view { display:flex; width:100%; height:100%; }
.split-half { flex:1; position:relative; display:flex; align-items:center; justify-content:center; }
.split-img { width:100%; height:100%; object-fit:contain; }
.split-label { position:absolute; bottom:8px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,.6); color:#fff; font-size:12px; padding:3px 12px; border-radius:4px; }
.split-divider { width:2px; background:#374151; flex-shrink:0; }

/* Cards */
.card { background:#fff; border-radius:10px; box-shadow:var(--card-shadow); padding:18px; }
.card-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.card-title { font-size:14px; font-weight:600; }
.card-count { font-size:12px; color:var(--text-muted); }

/* ── Congestion ── */
.congestion-card.clear  { background:var(--traffic-bg-clear);  border:1px solid rgba(34,197,94,.25); }
.congestion-card.slow   { background:var(--traffic-bg-slow);   border:1px solid rgba(245,158,11,.25); }
.congestion-card.congested { background:var(--traffic-bg-congested); border:1px solid rgba(239,68,68,.25); }
.congestion-main { display:flex; align-items:center; gap:14px; margin-bottom:10px; }
.congestion-emoji { font-size:36px; }
.congestion-level { font-size:20px; font-weight:700; }
.congestion-sub { font-size:12px; color:var(--text-secondary); margin-top:2px; }
.congestion-diagnosis { font-size:12px; color:var(--text-secondary); line-height:1.6; padding:8px 12px; background:rgba(255,255,255,.6); border-radius:6px; }

/* ── Distribution panel ── */
.dist-panel { display:flex; flex-direction:column; gap:14px; }
.dist-gauge { }
.gauge-bar { height:10px; background:#e5e7eb; border-radius:5px; overflow:hidden; }
.gauge-fill { height:100%; border-radius:5px; transition:width .3s; }
.gauge-ticks { display:flex; justify-content:space-between; font-size:10px; color:var(--text-muted); margin-top:4px; padding:0 2px; }
.gauge-label { font-size:11px; color:var(--text-muted); margin-top:6px; text-align:center; }
.dist-metrics { display:flex; gap:8px; }
.dm-item { flex:1; text-align:center; background:#f9fafb; border-radius:8px; padding:10px 4px; }
.dm-val { font-size:20px; font-weight:700; }
.dm-lbl { font-size:10px; color:var(--text-muted); margin-top:2px; }
.dm-note { font-size:9px; color:var(--text-muted); display:block; margin-top:1px; }

/* ── Bar chart ── */
.bar-chart { display:flex; flex-direction:column; gap:8px; }
.bar-row { display:flex; align-items:center; gap:8px; }
.bar-label { width:64px; font-size:12px; font-weight:500; flex-shrink:0; }
.bar-track { flex:1; height:16px; background:#f3f4f6; border-radius:4px; overflow:hidden; }
.bar-fill { height:100%; border-radius:4px; transition:width .3s; }
.bar-value { width:52px; font-size:12px; font-weight:600; text-align:right; flex-shrink:0; }
.bar-pct { font-weight:400; opacity:.6; }

/* ── Size breakdown ── */
.size-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.size-label { font-size:12px; font-weight:600; width:56px; flex-shrink:0; }
.size-desc { font-size:10px; color:var(--text-muted); width:130px; flex-shrink:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.size-track { flex:1; height:10px; background:#f3f4f6; border-radius:3px; overflow:hidden; }
.size-fill { height:100%; border-radius:3px; transition:width .3s; }
.size-num { width:28px; font-size:13px; font-weight:700; text-align:right; flex-shrink:0; }

/* ── Detail table ── */
.detail-table-wrapper { max-height:200px; overflow-y:auto; }
.detail-table { width:100%; border-collapse:collapse; font-size:13px; }
.detail-table th { text-align:left; padding:6px 4px 8px; font-size:11px; color:var(--text-muted); font-weight:500; border-bottom:1px solid var(--border-color); }
.detail-table th:not(:first-child) { text-align:center; }
.detail-table td { padding:7px 4px; border-bottom:1px solid #f3f4f6; }
.detail-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }
.td-num { text-align:center; font-variant-numeric:tabular-nums; }

/* ── Info ── */
.info-row { display:flex; justify-content:space-between; padding:6px 0; font-size:13px; }
.info-label { color:var(--text-secondary); }
.info-val { font-weight:500; }

.empty-inline { text-align:center; font-size:12px; color:var(--text-muted); padding:24px 0; }
</style>
