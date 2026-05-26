<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">实时监控</h1>
      <p class="page-desc">调用本地摄像头，实时检测画面中的目标并提供异常告警</p>
    </div>

    <!-- 告警栏 -->
    <div class="alert-bar" :class="{ active: isAlerting }">
      <span class="alert-icon">{{ isAlerting ? '🚨' : '✅' }}</span>
      <span class="alert-text" v-if="isAlerting">⚠️ 警告：目标数超过阈值（{{ alertThreshold }}）</span>
      <span class="alert-text" v-else>系统正常 · 当前未触发告警</span>
      <span class="alert-count">阈值: {{ alertThreshold }} | 模型: visdrone-v1</span>
    </div>

    <!-- 监控主区域 -->
    <div class="monitor-layout">
      <div class="monitor-main card">
        <div class="monitor-header">
          <span class="monitor-title">
            <span class="live-indicator" :class="{ active: isMonitoring }"></span>
            {{ isMonitoring ? '实时画面' : '摄像头未开启' }}
          </span>
          <div class="monitor-controls">
            <el-input-number v-model="alertThreshold" :min="3" :max="50" size="small" style="width:110px" />
            <el-select v-model="monitorModel" size="small" style="width:150px" :disabled="isMonitoring">
              <el-option label="COCO (通用)" value="coco" />
              <el-option label="VisDrone (航拍)" value="visdrone-v1" />
            </el-select>
            <span style="font-size:12px;color:var(--text-muted)">FPS: {{ fps }}</span>
            <el-button :type="isMonitoring ? 'danger' : 'primary'" size="small" @click="toggleMonitor">
              <el-icon><component :is="isMonitoring ? 'VideoPause' : 'VideoPlay'" /></el-icon>
              {{ isMonitoring ? '关闭监控' : '启动监控' }}
            </el-button>
          </div>
        </div>

        <div class="camera-feed" ref="feedRef">
          <video ref="cameraEl" autoplay playsinline muted class="camera-video" />
          <canvas ref="overlayEl" class="overlay-canvas" />
          <div v-if="!isMonitoring" class="camera-off">
            <el-icon :size="56"><VideoCamera /></el-icon>
            <p>点击"启动监控"开启摄像头</p>
          </div>
        </div>
      </div>

      <!-- 侧边指标 -->
      <div class="monitor-side">
        <div class="card counter-card">
          <div class="live-dot" :class="{ active: isMonitoring }"></div>
          <div class="counter-value" :class="{ alert: isAlerting }">{{ liveCount }}</div>
          <div class="counter-label">当前目标数</div>
          <div class="counter-time">{{ elapsed }}s</div>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-title">实时指标</span></div>
          <div class="realtime-grid">
            <div class="rt-item">
              <div class="rt-value">{{ fps }}</div>
              <div class="rt-label">FPS</div>
            </div>
            <div class="rt-item">
              <div class="rt-value">{{ totalDetections }}</div>
              <div class="rt-label">累计检测</div>
            </div>
            <div class="rt-item">
              <div class="rt-value">{{ alertCount }}</div>
              <div class="rt-label">告警次数</div>
            </div>
            <div class="rt-item">
              <div class="rt-value">{{ currentFrameData ? Object.keys(currentFrameData.category_counts).length : 0 }}</div>
              <div class="rt-label">检出类别</div>
            </div>
          </div>
        </div>

        <!-- 当前帧明细 -->
        <div class="card">
          <div class="card-header"><span class="card-title">帧级明细</span></div>
          <div v-if="currentFrameData && Object.keys(currentFrameData.category_counts).length" class="frame-detail">
            <div v-for="(count, cls) in currentFrameData.category_counts" :key="cls" class="fd-row">
              <span class="fd-name">{{ CAT_LABELS[cls] || cls }}</span>
              <span class="fd-count">{{ count }}</span>
            </div>
          </div>
          <div v-else class="empty-inline">{{ isMonitoring ? '等待检测结果...' : '启动监控后显示' }}</div>
        </div>

        <!-- 告警日志 -->
        <div class="card alert-log-card">
          <div class="card-header">
            <span class="card-title">告警记录</span>
            <el-tag :type="isAlerting ? 'danger' : 'success'" size="small" effect="dark">
              {{ isAlerting ? '告警中' : '正常' }}
            </el-tag>
          </div>
          <div class="log-list">
            <div v-if="alertLogs.length === 0" class="log-empty">暂无告警</div>
            <div v-for="(log, i) in alertLogs" :key="i" class="log-item">
              <span class="log-time">{{ log.time }}</span>
              <span class="log-msg">{{ log.count }} 个目标</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick, watch } from "vue";
import { ElMessage } from "element-plus";
import { VideoPlay, VideoPause, VideoCamera } from "@element-plus/icons-vue";

const monitorModel = ref("coco");

const CAT_LABELS = {
  car:"汽车", van:"面包车", truck:"卡车", bus:"公交车", motor:"摩托车",
  bicycle:"自行车", tricycle:"三轮车", "awning-tricycle":"遮阳三轮车",
  pedestrian:"行人", people:"人群",
  person:"人", motorcycle:"摩托车", airplane:"飞机", train:"火车",
  boat:"船", "traffic light":"红绿灯", bench:"长椅", bird:"鸟",
  cat:"猫", dog:"狗", horse:"马", sheep:"羊", cow:"牛",
  elephant:"大象", bear:"熊", zebra:"斑马", giraffe:"长颈鹿",
  backpack:"背包", umbrella:"雨伞", handbag:"手提包", tie:"领带",
  suitcase:"行李箱", frisbee:"飞盘", skis:"滑雪板", snowboard:"滑雪板",
  "sports ball":"球", kite:"风筝", "baseball bat":"球棒",
  "baseball glove":"手套", skateboard:"滑板", surfboard:"冲浪板",
  "tennis racket":"球拍", bottle:"瓶子", "wine glass":"酒杯",
  cup:"杯子", fork:"叉子", knife:"刀", spoon:"勺子", bowl:"碗",
  banana:"香蕉", apple:"苹果", sandwich:"三明治", orange:"橙子",
  broccoli:"西兰花", carrot:"胡萝卜", "hot dog":"热狗", pizza:"披萨",
  donut:"甜甜圈", cake:"蛋糕", chair:"椅子", couch:"沙发",
  "potted plant":"盆栽", bed:"床", "dining table":"餐桌", toilet:"马桶",
  tv:"电视", laptop:"笔记本", mouse:"鼠标", remote:"遥控器",
  keyboard:"键盘", "cell phone":"手机", microwave:"微波炉",
  oven:"烤箱", toaster:"烤面包机", sink:"水槽", refrigerator:"冰箱",
  book:"书", clock:"钟", vase:"花瓶", scissors:"剪刀",
  "teddy bear":"泰迪熊", "hair drier":"吹风机", toothbrush:"牙刷",
};
const CAT_COLORS = {
  car:"#3b82f6", van:"#8b5cf6", truck:"#f59e0b", bus:"#ef4444",
  motor:"#06b6d4", bicycle:"#10b981", tricycle:"#ec4899",
  "awning-tricycle":"#f97316", pedestrian:"#6366f1", people:"#84cc16",
  // COCO 通用类别
  person:"#ef4444", motorcycle:"#f59e0b", airplane:"#8b5cf6",
  train:"#6366f1", boat:"#06b6d4", "traffic light":"#f97316",
  bench:"#84cc16", bird:"#ec4899", cat:"#3b82f6", dog:"#10b981",
  horse:"#f59e0b", sheep:"#8b5cf6", cow:"#6366f1",
  elephant:"#06b6d4", bear:"#ef4444", zebra:"#ec4899",
  giraffe:"#f97316", backpack:"#3b82f6", umbrella:"#6366f1",
  handbag:"#ef4444", tie:"#8b5cf6", suitcase:"#06b6d4",
  frisbee:"#10b981", skis:"#ec4899", snowboard:"#f59e0b",
  "sports ball":"#3b82f6", kite:"#f97316",
  "baseball bat":"#84cc16", "baseball glove":"#6366f1",
  skateboard:"#06b6d4", surfboard:"#10b981",
  "tennis racket":"#8b5cf6", bottle:"#ef4444",
  "wine glass":"#f59e0b", cup:"#3b82f6", fork:"#6366f1",
  knife:"#06b6d4", spoon:"#ec4899", bowl:"#10b981",
  banana:"#f97316", apple:"#ef4444", sandwich:"#f59e0b",
  orange:"#3b82f6", broccoli:"#10b981", carrot:"#8b5cf6",
  "hot dog":"#6366f1", pizza:"#ec4899", donut:"#f97316",
  cake:"#ef4444", chair:"#3b82f6", couch:"#06b6d4",
  "potted plant":"#10b981", bed:"#8b5cf6",
  "dining table":"#6366f1", toilet:"#ec4899",
  tv:"#3b82f6", laptop:"#f59e0b", mouse:"#84cc16",
  remote:"#06b6d4", keyboard:"#10b981",
  "cell phone":"#ef4444", microwave:"#8b5cf6",
  oven:"#f97316", toaster:"#6366f1", sink:"#3b82f6",
  refrigerator:"#06b6d4", book:"#ec4899", clock:"#10b981",
  vase:"#84cc16", scissors:"#f59e0b",
  "teddy bear":"#ef4444", "hair drier":"#8b5cf6", toothbrush:"#6366f1",
  // fallback generator
};

const cameraEl = ref(null);
const overlayEl = ref(null);
const feedRef = ref(null);
const isMonitoring = ref(false);
const isAlerting = ref(false);
const alertThreshold = ref(8);
const liveCount = ref(0);
const fps = ref(0);
const elapsed = ref(0);
const totalDetections = ref(0);
const alertCount = ref(0);
const alertLogs = ref([]);
const currentFrameData = ref(null);

let stream = null;
let ws = null;
let captureTimer = null;
let elapsedTimer = null;
let lastFrameTime = 0;
let frameTimestamps = [];

const toggleMonitor = async () => {
  if (isMonitoring.value) { stopMonitor(); } else { startMonitor(); }
};

const startMonitor = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    cameraEl.value.srcObject = stream;
    await nextTick();

    // 建立 WebSocket 连接
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${window.location.host}/api/detection/ws/monitor?model_name=${monitorModel.value}`;
    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      isMonitoring.value = true;
      ElMessage.success("监控已启动");
      startCaptureLoop();
      startElapsedTimer();
    };

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (!data.success) return;
      currentFrameData.value = data;
      liveCount.value = data.total_objects;
      totalDetections.value += data.total_objects;
      drawBoxes(data.boxes, data.frame_w, data.frame_h);

      // 告警逻辑
      if (data.alert && !isAlerting.value) {
        isAlerting.value = true;
        alertCount.value++;
        const now = new Date().toLocaleTimeString();
        alertLogs.value.unshift({ time: now, count: data.total_objects });
        if (alertLogs.value.length > 50) alertLogs.value.pop();
      } else if (!data.alert && isAlerting.value) {
        isAlerting.value = false;
      }

      // 计算 FPS
      const now = performance.now();
      if (lastFrameTime > 0) {
        frameTimestamps.push(now - lastFrameTime);
        if (frameTimestamps.length > 10) frameTimestamps.shift();
        fps.value = Math.round(1000 / (frameTimestamps.reduce((a, b) => a + b, 0) / frameTimestamps.length));
      }
      lastFrameTime = now;
    };

    ws.onerror = () => { ElMessage.error("WebSocket 连接失败"); stopMonitor(); };
    ws.onclose = () => { if (isMonitoring.value) { ElMessage.warning("连接已断开"); stopMonitor(); } };

  } catch (e) {
    ElMessage.error("无法访问摄像头: " + (e.message || "权限被拒绝"));
    stopMonitor();
  }
};

const startCaptureLoop = () => {
  const sendFrame = () => {
    if (!isMonitoring.value || !ws || ws.readyState !== WebSocket.OPEN) return;
    const video = cameraEl.value;
    if (!video || video.readyState < 2) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      if (blob && ws && ws.readyState === WebSocket.OPEN) {
        blob.arrayBuffer().then(buf => { if (ws.readyState === WebSocket.OPEN) ws.send(buf); });
      }
    }, "image/jpeg", 0.7);
  };

  captureTimer = setInterval(sendFrame, 120);
};

const startElapsedTimer = () => {
  elapsed.value = 0;
  elapsedTimer = setInterval(() => { elapsed.value++; }, 1000);
};

/* ── Canvas 画检测框 ── */
const drawBoxes = (boxes, fw, fh) => {
  const cvs = overlayEl.value;
  const feed = feedRef.value;
  if (!cvs || !feed || !fw || !fh) return;

  const rect = feed.getBoundingClientRect();
  cvs.width = rect.width;
  cvs.height = rect.height;

  const sx = rect.width / fw;
  const sy = rect.height / fh;
  const ctx = cvs.getContext("2d");
  ctx.clearRect(0, 0, cvs.width, cvs.height);
  if (boxes.length === 0) return;

  ctx.lineWidth = 2;
  ctx.font = "bold 12px sans-serif";
  ctx.textBaseline = "top";

  for (const b of boxes) {
    const x = b.x1 * sx, y = b.y1 * sy, w = (b.x2 - b.x1) * sx, h = (b.y2 - b.y1) * sy;
    let color = CAT_COLORS[b.class_name];
    if (!color) {
      // fallback: hash the class name to a color
      let hash = 0;
      for (let i = 0; i < b.class_name.length; i++) hash = b.class_name.charCodeAt(i) + ((hash << 5) - hash);
      color = `hsl(${Math.abs(hash) % 360}, 70%, 55%)`;
    }
    ctx.strokeStyle = color;
    ctx.strokeRect(x, y, w, h);

    const label = `${CAT_LABELS[b.class_name] || b.class_name} ${(b.confidence * 100).toFixed(0)}%`;
    const tw = ctx.measureText(label).width;
    const lh = 16;
    let ly = y - lh - 2;
    if (ly < 0) ly = y + h + 2; // label below if box at top edge

    ctx.fillStyle = color;
    ctx.fillRect(x, ly, tw + 8, lh);
    ctx.fillStyle = "#fff";
    ctx.fillText(label, x + 4, ly + 2);
  }
};

/* ── 停止监控 ── */
const stopMonitor = () => {
  if (ws) { ws.close(); ws = null; }
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
  if (captureTimer) { clearInterval(captureTimer); captureTimer = null; }
  if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null; }

  isMonitoring.value = false;
  isAlerting.value = false;
  liveCount.value = 0;
  fps.value = 0;
  currentFrameData.value = null;

  // 清空画布
  const cvs = overlayEl.value;
  if (cvs) { const ctx = cvs.getContext("2d"); ctx.clearRect(0, 0, cvs.width, cvs.height); }
};

onUnmounted(() => stopMonitor());
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* ===== 告警栏 ===== */
.alert-bar {
  display: flex; align-items: center; gap: 12px; padding: 10px 18px;
  border-radius: 8px; margin-bottom: 16px;
  background: #f0fdf4; border: 1px solid rgba(34,197,94,.2);
  transition: all .3s;
}
.alert-bar.active { background: #fef2f2; border-color: rgba(239,68,68,.3); animation: flash 1s infinite; }
@keyframes flash { 0%,100%{opacity:1} 50%{opacity:.85} }
.alert-icon { font-size: 18px; }
.alert-text { flex: 1; font-size: 13px; font-weight: 500; }
.alert-bar.active .alert-text { color: var(--danger); }
.alert-count { font-size: 11px; color: var(--text-muted); }

/* ===== 布局 ===== */
.monitor-layout { display: flex; gap: 20px; }
.monitor-main { flex: 1; min-width: 0; }
.monitor-side { width: 300px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }

.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 18px; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-size: 14px; font-weight: 600; }

/* ===== 监控头栏 ===== */
.monitor-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.monitor-title { font-size: 15px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.live-indicator { width: 9px; height: 9px; border-radius: 50%; background: #9ca3af; }
.live-indicator.active { background: var(--danger); animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.monitor-controls { display: flex; align-items: center; gap: 10px; }

/* ===== 摄像头画面 ===== */
.camera-feed {
  background: #000; border-radius: 8px; position: relative; overflow: hidden;
  aspect-ratio: 16/10; display: flex; align-items: center; justify-content: center;
}
.camera-video { width: 100%; height: 100%; object-fit: contain; display: block; }
.overlay-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: transparent; pointer-events: none; z-index: 2; }
.camera-off { text-align: center; color: #6b7280; }
.camera-off p { margin-top: 12px; }

/* ===== 实时计数 ===== */
.counter-card { text-align: center; padding: 24px; position: relative; }
.live-dot { width: 10px; height: 10px; border-radius: 50%; background: #9ca3af; position: absolute; top: 16px; right: 16px; }
.live-dot.active { background: var(--danger); animation: pulse 1.5s infinite; }
.counter-value { font-size: 48px; font-weight: 700; color: var(--primary); line-height: 1.1; }
.counter-value.alert { color: var(--danger); }
.counter-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.counter-time { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* ===== 实时指标 ===== */
.realtime-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.rt-item { text-align: center; background: #f9fafb; border-radius: 8px; padding: 12px 4px; }
.rt-value { font-size: 22px; font-weight: 700; color: var(--primary); }
.rt-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

/* ===== 帧明细 ===== */
.frame-detail { display: flex; flex-direction: column; gap: 6px; max-height: 180px; overflow-y: auto; }
.fd-row { display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; border-bottom: 1px solid #f3f4f6; }
.fd-name { color: var(--text-secondary); }
.fd-count { font-weight: 600; }

/* ===== 告警日志 ===== */
.alert-log-card { flex: 1; }
.log-list { max-height: 200px; overflow-y: auto; }
.log-empty { text-align: center; color: var(--text-muted); padding: 24px; font-size: 13px; }
.log-item { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f3f4f6; font-size: 12px; }
.log-time { color: var(--text-muted); }
.log-msg { color: var(--danger); }

.empty-inline { text-align: center; font-size: 12px; color: var(--text-muted); padding: 24px 0; }
</style>
