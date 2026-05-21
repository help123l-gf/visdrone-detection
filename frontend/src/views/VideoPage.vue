<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">视频分析</h1>
      <p class="page-desc">上传无人机航拍视频，逐帧检测目标并绘制流量变化趋势</p>
    </div>

    <div v-if="!videoSrc" class="card upload-block">
      <div class="upload-inner" @dragover.prevent @drop.prevent="handleDrop">
        <input ref="videoInput" type="file" accept="video/mp4,video/avi,video/mov" class="file-hidden" @change="handleVideo" />
        <el-icon :size="48"><VideoCamera /></el-icon>
        <p class="up-title">上传无人机航拍视频</p>
        <p class="up-hint">支持 MP4 / AVI / MOV 格式，建议分辨率 1080p+</p>
        <el-button type="primary" @click.stop="$refs.videoInput.click()">
          <el-icon><FolderOpened /></el-icon>选择视频文件
        </el-button>
      </div>
    </div>

    <div v-else class="analysis-layout">
      <!-- Video player -->
      <div class="video-panel card">
        <div class="card-header">
          <span class="card-title">视频播放</span>
          <el-tag v-if="isAnalyzing" type="warning" size="small">分析中...</el-tag>
          <el-tag v-else type="success" size="small">就绪</el-tag>
        </div>
        <div class="player-wrapper">
          <video ref="player" :src="videoSrc" controls class="video-player" @timeupdate="onTimeUpdate" @play="onPlay" @pause="onPause">
            您的浏览器不支持视频播放
          </video>
        </div>
        <!-- TODO: 在视频帧上叠加 YOLO 检测框 (Canvas overlay) -->
      </div>

      <!-- Side dashboard -->
      <div class="side-panel">
        <!-- Real-time counter -->
        <div class="card counter-card">
          <div class="live-dot"></div>
          <div class="counter-value">{{ currentCount }}</div>
          <div class="counter-label">当前帧目标数</div>
          <!-- TODO: 接入后端逐帧检测结果 -->
        </div>

        <!-- Dynamic line chart -->
        <div class="card chart-card">
          <div class="card-header">
            <span class="card-title">流量趋势</span>
            <span class="card-sub">车流量随时间变化</span>
          </div>
          <div ref="lineChartRef" class="chart-area"></div>
          <!-- TODO: 使用 ECharts 动态折线图，横轴=时间，纵轴=目标数 -->
        </div>

        <!-- Stats -->
        <div class="card">
          <div class="stats-row">
            <div class="mini-stat">
              <div class="mini-num">{{ maxCount }}</div>
              <div class="mini-label">峰值目标数</div>
            </div>
            <div class="mini-stat">
              <div class="mini-num">{{ avgCount }}</div>
              <div class="mini-label">平均目标数</div>
            </div>
            <div class="mini-stat">
              <div class="mini-num">{{ duration }}</div>
              <div class="mini-label">视频时长(s)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { VideoCamera, FolderOpened } from "@element-plus/icons-vue";

const videoInput = ref(null);
const videoSrc = ref("");
const isAnalyzing = ref(false);
const currentCount = ref(0);
const maxCount = ref(0);
const avgCount = ref(0);
const duration = ref(0);

const handleDrop = (e) => {
  const file = e.dataTransfer.files[0];
  if (file) loadVideo(file);
};

const handleVideo = (e) => {
  const file = e.target.files[0];
  if (file) loadVideo(file);
  e.target.value = "";
};

const loadVideo = (file) => {
  if (!file.type.startsWith("video/")) { ElMessage.warning("请上传视频文件"); return; }
  videoSrc.value = URL.createObjectURL(file);
  ElMessage.success("视频已加载，点击播放开始分析");
  // TODO: 视频加载成功后，启动后端视频分析任务
};

const onTimeUpdate = () => {
  // TODO: 同步当前播放时间 → 获取对应帧的检测结果
  // currentCount.value = frames[currentTime].count
};

const onPlay = () => { /* TODO: 开始逐帧分析 */ };
const onPause = () => { /* TODO: 暂停分析 */ };
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.upload-block { padding: 0; }
.upload-inner {
  padding: 52px; text-align: center; cursor: pointer;
  border: 2px dashed #d1d5db; border-radius: 10px; transition: all 0.2s;
}
.upload-inner:hover { border-color: var(--primary); background: var(--primary-bg); }
.up-title { font-size: 16px; font-weight: 500; margin-top: 16px; }
.up-hint { font-size: 12px; color: var(--text-muted); margin: 6px 0 18px; }
.file-hidden { display: none; }

.analysis-layout { display: flex; gap: 20px; }
.video-panel { flex: 1; min-width: 0; }
.side-panel { width: 340px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }

.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 18px; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-size: 14px; font-weight: 600; }
.card-sub { font-size: 12px; color: var(--text-muted); }

.player-wrapper { background: #000; border-radius: 8px; overflow: hidden; }
.video-player { width: 100%; display: block; }

/* Counter */
.counter-card { text-align: center; padding: 24px; position: relative; }
.live-dot {
  width: 10px; height: 10px; border-radius: 50%; background: var(--danger);
  position: absolute; top: 16px; right: 16px;
  animation: pulse-dot 1.5s infinite;
}
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:.3} }
.counter-value { font-size: 42px; font-weight: 700; color: var(--primary); line-height: 1.2; }
.counter-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.chart-card { flex: 1; }
.chart-area { height: 200px; }
/* TODO: 使用 <v-chart :option="lineOption" autoresize /> */

.stats-row { display: flex; gap: 12px; }
.mini-stat { flex: 1; text-align: center; padding: 12px 4px; background: #f9fafb; border-radius: 8px; }
.mini-num { font-size: 22px; font-weight: 700; color: var(--primary); }
.mini-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
</style>
