<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">单图分析</h1>
      <p class="page-desc">上传无人机航拍图片，获取目标检测结果与交通态势评估报告</p>
    </div>

    <!-- 上传区域 -->
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

    <!-- 工具栏 -->
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
      <!-- ============ 左侧：图片区域 ============ -->
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

      <!-- ============ 右侧：数据仪表盘 ============ -->
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
/* ============================================================
   单图分析 — 核心脚本
   数据流：用户选图 → POST /api/detection/single → YOLO推理
   → 返回 DetectionResult → 计算拥堵/聚类/规模 → 渲染面板
   ============================================================ */
import { ref, computed } from "vue";
import { ElMessage, ElLoading } from "element-plus";
import { UploadFilled, Picture, Search, Check, Switch } from "@element-plus/icons-vue";
import { detectSingleImage } from "../api/detection";

// ── 状态变量 ──
const selectedModel = ref("visdrone-v1");   // 当前选中的检测模型
const fileInput = ref(null);                 // 隐藏的 <input type=file> 引用
const originalSrc = ref("");                 // 原图 blob URL
const resultSrc = ref("");                   // 标注图 URL（MinIO 或本地）
const result = ref(null);                    // 后端返回的 DetectionResult 对象
const detecting = ref(false);                // 是否正在请求后端
const viewMode = ref("compare");             // 左侧画面模式: compare | result | original
const imageWidth = ref(0);                   // 上传图片的自然宽度
const imageHeight = ref(0);                  // 上传图片的自然高度

// ── 类别颜色与中文名映射 ──
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

// ── 车辆类型分布（水平条形图数据） ──
const vehicleCats = computed(() => {
  const keys = ["car","van","truck","bus","motor","bicycle","tricycle","awning-tricycle"];
  if (!result.value) return keys.map(k=>({ key:k, label:CAT_LABELS[k]||k, count:0, color:CAT_COLORS[k]||"#cbd5e1" }));
  return keys.map(k=>{
    const count = result.value.boxes.filter(b=>b.class_name===k).length;
    return { key:k, label:CAT_LABELS[k]||k, count, color:CAT_COLORS[k]||"#cbd5e1" };
  });
});
const totalVehicles = computed(()=> vehicleCats.value.reduce((s,c)=>s+c.count,0));

// ── 目标明细表（按类别聚合） ──
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

// ── 从 API 响应中直接读取聚类与拥堵数据（后端已算好） ──
const clustering = computed(() => result.value?.clustering || { ratio: 0, clusterCount: 0, avgSpacing: 0, trafficClusterCount: 0, label: "无数据", level: "" });
const congestion = computed(() => result.value?.congestion || { level: "", label: "就绪", emoji: "—" });

// ── 智能诊断文本 ──
const trafficDiagnosis = computed(() => {
  if (!result.value || totalVehicles.value === 0) return "";
  const { ratio, clusterCount, trafficClusterCount, avgSpacing } = clustering.value;
  const parts = [];
  const parkedFiltered = (clusterCount || 0) - (trafficClusterCount || 0);

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

// ── 车辆规模构成（按 bbox 面积三分） ──
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

// ── 文件上传与拖拽 ──
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

// ── 发起检测请求 ──
const startDetection = async ()=>{
  const file=fileInput.value?._pendingFile; if(!file) return;
  detecting.value=true;
  const loading=ElLoading.service({ lock:true, text:"正在分析中...", background:"rgba(0,0,0,0.6)" });
  try {
    const fd=new FormData(); fd.append("file",file); fd.append("model_name",selectedModel.value);
    const res=await detectSingleImage(fd);
    if(res.success&&res.data){
      result.value=res.data;
      // result 是 Vue 响应式变量，赋值后所有依赖它的 computed 自动重新计算，页面即时更新
      const ru = res.data.result_image_url;
      resultSrc.value = ru.startsWith("http") ? ru : "http://localhost:8000" + ru;
      viewMode.value="compare";
      ElMessage.success(`检测完成，发现 ${res.data.total_objects} 个目标`);
    }else{ ElMessage.error(res.message||"检测失败"); }
  }catch{ ElMessage.error("检测请求失败，请检查后端是否运行"); }
  finally{ detecting.value=false; loading.close(); }
};
</script>

<style scoped>
/* ===== 页面容器：Flex 列布局，撑满视口，禁止整页滚动 ===== */
.page-container { padding: 24px; height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.page-header { margin-bottom: 16px; flex-shrink: 0; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* ===== 上传区域 ===== */
.upload-zone { border:2px dashed #d1d5db; border-radius:10px; padding:20px; text-align:center; cursor:pointer; transition:all .2s; margin-bottom:12px; background:#fff; flex-shrink:0; }
.upload-zone:hover { border-color:var(--primary); background:var(--primary-bg); }
.upload-zone.has-file { padding:12px 20px; border-style:solid; border-color:var(--primary); }
.upload-text { font-size:14px; font-weight:500; margin-top:8px; }
.upload-hint { font-size:12px; color:var(--text-muted); margin-top:4px; }
.uploaded-info { display:flex; align-items:center; gap:12px; }
.uploaded-size { font-size:13px; color:var(--text-secondary); }
.file-hidden { display:none; }

/* ===== 工具栏 ===== */
.toolbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; flex-shrink:0; }
.toolbar-left { display:flex; align-items:center; gap:12px; }
.toolbar-label { font-size:13px; color:var(--text-secondary); }

/* ===== 左右分栏：图片区自适应填充，仪表盘固定宽度且内部滚动 ===== */
.detection-layout { flex: 1; display: flex; gap: 20px; min-height: 0; overflow: hidden; }
.image-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; }
.image-panel .card-header { flex-shrink: 0; }
.dashboard { width: 380px; flex-shrink: 0; overflow-y: auto; overflow-x: hidden; display: flex; flex-direction: column; gap: 14px; padding-right: 4px; }

/* ===== 图片查看器：自适应撑满左侧剩余高度 ===== */
.image-viewer { flex: 1; min-height: 200px; background: #111827; border-radius: 8px; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.main-image { width:100%; height:100%; object-fit:contain; }
.image-placeholder { text-align:center; color:#6b7280; }
.image-placeholder p { margin-top:12px; font-size:13px; }
.split-view { display:flex; width:100%; height:100%; }
.split-half { flex:1; position:relative; display:flex; align-items:center; justify-content:center; }
.split-img { width:100%; height:100%; object-fit:contain; }
.split-label { position:absolute; bottom:8px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,.6); color:#fff; font-size:12px; padding:3px 12px; border-radius:4px; }
.split-divider { width:2px; background:#374151; flex-shrink:0; }

/* ===== 通用卡片 ===== */
.card { background:#fff; border-radius:10px; box-shadow:var(--card-shadow); padding:18px; }
.card-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.card-title { font-size:14px; font-weight:600; }
.card-count { font-size:12px; color:var(--text-muted); }

/* ===== 拥堵评级卡片（三色主题） ===== */
.congestion-card.clear  { background:var(--traffic-bg-clear);  border:1px solid rgba(34,197,94,.25); }
.congestion-card.slow   { background:var(--traffic-bg-slow);   border:1px solid rgba(245,158,11,.25); }
.congestion-card.congested { background:var(--traffic-bg-congested); border:1px solid rgba(239,68,68,.25); }
.congestion-main { display:flex; align-items:center; gap:14px; margin-bottom:10px; }
.congestion-emoji { font-size:36px; }
.congestion-level { font-size:20px; font-weight:700; }
.congestion-sub { font-size:12px; color:var(--text-secondary); margin-top:2px; }
.congestion-diagnosis { font-size:12px; color:var(--text-secondary); line-height:1.6; padding:8px 12px; background:rgba(255,255,255,.6); border-radius:6px; }

/* ===== 车辆分布特征面板 ===== */
.dist-panel { display:flex; flex-direction:column; gap:14px; }
.gauge-bar { height:10px; background:#e5e7eb; border-radius:5px; overflow:hidden; }
.gauge-fill { height:100%; border-radius:5px; transition:width .3s; }
.gauge-ticks { display:flex; justify-content:space-between; font-size:10px; color:var(--text-muted); margin-top:4px; padding:0 2px; }
.gauge-label { font-size:11px; color:var(--text-muted); margin-top:6px; text-align:center; }
.dist-metrics { display:flex; gap:8px; }
.dm-item { flex:1; text-align:center; background:#f9fafb; border-radius:8px; padding:10px 4px; }
.dm-val { font-size:20px; font-weight:700; }
.dm-lbl { font-size:10px; color:var(--text-muted); margin-top:2px; }
.dm-note { font-size:9px; color:var(--text-muted); display:block; margin-top:1px; }

/* ===== 车辆类型分布（水平条形图） ===== */
.bar-chart { display:flex; flex-direction:column; gap:8px; }
.bar-row { display:flex; align-items:center; gap:8px; }
.bar-label { width:64px; font-size:12px; font-weight:500; flex-shrink:0; }
.bar-track { flex:1; height:16px; background:#f3f4f6; border-radius:4px; overflow:hidden; }
.bar-fill { height:100%; border-radius:4px; transition:width .3s; }
.bar-value { width:52px; font-size:12px; font-weight:600; text-align:right; flex-shrink:0; }
.bar-pct { font-weight:400; opacity:.6; }

/* ===== 车辆规模构成（小/中/大型） ===== */
.size-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.size-label { font-size:12px; font-weight:600; width:56px; flex-shrink:0; }
.size-desc { font-size:10px; color:var(--text-muted); width:130px; flex-shrink:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.size-track { flex:1; height:10px; background:#f3f4f6; border-radius:3px; overflow:hidden; }
.size-fill { height:100%; border-radius:3px; transition:width .3s; }
.size-num { width:28px; font-size:13px; font-weight:700; text-align:right; flex-shrink:0; }

/* ===== 目标明细聚合表格 ===== */
.detail-table-wrapper { max-height:200px; overflow-y:auto; }
.detail-table { width:100%; border-collapse:collapse; font-size:13px; }
.detail-table th { text-align:left; padding:6px 4px 8px; font-size:11px; color:var(--text-muted); font-weight:500; border-bottom:1px solid var(--border-color); }
.detail-table th:not(:first-child) { text-align:center; }
.detail-table td { padding:7px 4px; border-bottom:1px solid #f3f4f6; }
.detail-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }
.td-num { text-align:center; font-variant-numeric:tabular-nums; }

/* ===== 检测信息 ===== */
.info-row { display:flex; justify-content:space-between; padding:6px 0; font-size:13px; }
.info-label { color:var(--text-secondary); }
.info-val { font-weight:500; }

.empty-inline { text-align:center; font-size:12px; color:var(--text-muted); padding:24px 0; }
</style>
