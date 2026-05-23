<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">视频分析</h1>
      <p class="page-desc">上传无人机航拍视频，逐帧检测目标并绘制流量变化趋势</p>
    </div>

    <!-- Upload -->
    <div v-if="!videoData" class="upload-block">
      <div class="upload-inner" @dragover.prevent @drop.prevent="handleDrop">
        <input ref="videoInput" type="file" accept="video/*" class="file-hidden" @change="handleVideo" />
        <el-icon :size="48"><VideoCamera /></el-icon>
        <p class="up-title">上传无人机航拍视频</p>
        <p class="up-hint">支持 MP4 / AVI / MOV</p>
        <div class="upload-ctrls">
          <span class="ctrl-lbl">帧采样间隔：</span>
          <el-input-number v-model="frameInterval" :min="1" :max="30" size="small" />
          <span class="ctrl-hint">每隔 N 帧检测一次</span>
        </div>
        <el-button type="primary" size="large" @click.stop="$refs.videoInput.click()">
          <el-icon><FolderOpened /></el-icon>选择视频
        </el-button>
        <div v-if="selectedFile" class="file-ready">
          <el-icon color="#27ae60"><CircleCheckFilled /></el-icon>
          {{ selectedFile.name }}
          <el-button type="primary" :loading="processing" @click.stop="startAnalysis" style="margin-left:12px">
            {{ processing ? '分析中...' : '开始分析' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="videoData" class="analysis-layout">
      <div class="left-col">
        <!-- Video player -->
        <div class="card player-card">
          <div class="card-header">
            <span class="card-title">检测画面</span>
            <div class="badges">
              <el-tag type="success" size="small" effect="dark">{{ videoData.processed_frames }} 帧</el-tag>
              <el-tag type="info" size="small">{{ videoData.duration_sec }}s</el-tag>
            </div>
          </div>
          <div class="player-wrapper">
            <video
              v-if="annotatedSrc"
              ref="player"
              :src="annotatedSrc"
              class="video-el"
              controls
              @timeupdate="onTick"
              @play="isPlaying = true"
              @pause="isPlaying = false"
            />
            <div v-else class="no-video">
              <el-icon :size="40"><WarningFilled /></el-icon>
              <p>标注视频生成失败，请查看图表数据</p>
            </div>
          </div>
          <div class="player-actions">
            <el-button size="small" @click="reupload">重新上传</el-button>
          </div>
        </div>

        <!-- Chart -->
        <div class="card chart-card">
          <div class="card-header">
            <span class="card-title">流量趋势图</span>
          </div>
          <div class="chart-wrapper">
            <v-chart v-if="lineOption" :option="lineOption" autoresize class="line-chart" />
            <div v-else class="empty-chart">暂无数据</div>
          </div>
        </div>
      </div>

      <div class="right-col">
        <!-- Counter -->
        <div class="card counter-card">
          <div class="live-dot" :class="{ active: isPlaying }"></div>
          <div class="counter-value">{{ currentCount }}</div>
          <div class="counter-label">当前帧目标数</div>
          <div class="counter-time">{{ isPlaying ? currentTime.toFixed(1) + 's' : '等待播放' }}</div>
        </div>

        <!-- Stats -->
        <div class="card">
          <div class="card-header"><span class="card-title">统计数据</span></div>
          <div class="stats-col">
            <div class="mini-stat">
              <div class="mini-num" style="color:#ef4444">{{ videoData.peak_frame?.total_objects || 0 }}</div>
              <div class="mini-label">峰值目标数</div>
            </div>
            <div class="mini-stat">
              <div class="mini-num">{{ videoData.avg_objects_per_frame }}</div>
              <div class="mini-label">平均/帧</div>
            </div>
            <div class="mini-stat">
              <div class="mini-num">{{ videoData.processed_frames }}</div>
              <div class="mini-label">已处理帧</div>
            </div>
            <div class="mini-stat">
              <div class="mini-num">{{ videoData.duration_sec }}s</div>
              <div class="mini-label">视频时长</div>
            </div>
          </div>
        </div>

        <!-- Frame detail -->
        <div class="card">
          <div class="card-header"><span class="card-title">帧级明细</span></div>
          <div v-if="currentFrameData && Object.keys(currentFrameData.category_counts).length" class="frame-detail">
            <div v-for="(count, cls) in currentFrameData.category_counts" :key="cls" class="fd-row">
              <span class="fd-name">{{ CAT_LABELS[cls] || cls }}</span>
              <span class="fd-count">{{ count }}</span>
            </div>
          </div>
          <div v-else class="empty-inline">播放视频查看</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { VideoCamera, FolderOpened, CircleCheckFilled, WarningFilled } from "@element-plus/icons-vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { LineChart } from "echarts/charts";
import { TitleComponent, TooltipComponent, GridComponent, MarkLineComponent, LegendComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import request from "../utils/request";

use([LineChart, TitleComponent, TooltipComponent, GridComponent, MarkLineComponent, LegendComponent, CanvasRenderer]);

const videoInput = ref(null);
const player = ref(null);
const selectedFile = ref(null);
const processing = ref(false);
const isPlaying = ref(false);
const currentCount = ref(0);
const currentTime = ref(0);
const frameInterval = ref(5);
const videoData = ref(null);

const CAT_LABELS = {
  car:"汽车", van:"面包车", truck:"卡车", bus:"公交车", motor:"摩托车",
  bicycle:"自行车", tricycle:"三轮车", "awning-tricycle":"遮阳三轮车",
  pedestrian:"行人", people:"人群",
};

/* ── Annotated video URL ── */
const annotatedSrc = computed(() => {
  const url = videoData.value?.annotated_video_url;
  if (!url) return null;
  return url.startsWith("http") ? url : "http://localhost:8000" + url;
});

/* ── Nearest frame data ── */
const currentFrameData = computed(() => {
  if (!videoData.value?.frame_data?.length) return null;
  const frames = videoData.value.frame_data;
  const t = currentTime.value;
  let best = frames[0];
  for (const f of frames) { if (f.timestamp_sec <= t + 0.05) best = f; else break; }
  return best;
});

/* ── Video playback sync ── */
const onTick = () => {
  if (!player.value || !currentFrameData.value) return;
  currentTime.value = player.value.currentTime;
  currentCount.value = currentFrameData.value.total_objects;
};

/* ── ECharts ── */
const lineOption = computed(() => {
  if (!videoData.value?.frame_data?.length) return null;
  const frames = videoData.value.frame_data;
  const times = frames.map(f => f.timestamp_sec);
  const counts = frames.map(f => f.total_objects);
  const avg = videoData.value.avg_objects_per_frame;

  const allCats = new Set();
  frames.forEach(f => Object.keys(f.category_counts).forEach(c => allCats.add(c)));
  const catSeries = [...allCats].map(cls => ({
    name: CAT_LABELS[cls] || cls, type: "line", stack: "total",
    data: frames.map(f => f.category_counts[cls] || 0),
    smooth: true, symbol: "none", lineStyle: { width: 1 }, areaStyle: { opacity: 0.05 },
  }));

  return {
    tooltip: { trigger: "axis" },
    legend: { bottom: 0, textStyle: { fontSize: 10 }, type: "scroll" },
    grid: { left: 42, right: 16, top: 16, bottom: 35 },
    xAxis: { type: "category", data: times, name: "时间(s)", nameLocation: "middle", nameGap: 25, nameTextStyle: { fontSize: 10 }, axisLabel: { fontSize: 9 } },
    yAxis: { type: "value", name: "目标数", axisLabel: { fontSize: 9 } },
    series: [
      { name: "总计", type: "line", data: counts, smooth: true, symbol: "none", lineStyle: { width: 2, color: "#27ae60" },
        markLine: { silent: true, data: [{ yAxis: avg, name: "均值", label: { formatter: `均值 ${avg}` } }], lineStyle: { color: "#f59e0b", type: "dashed" } } },
      ...catSeries,
    ],
  };
});

/* ── File handling ── */
const handleDrop = (e) => { const f = e.dataTransfer.files[0]; if (f) selectFile(f); };
const handleVideo = (e) => { const f = e.target.files[0]; if (f) selectFile(f); e.target.value = ""; };
const selectFile = (f) => { if (!f.type.startsWith("video/")) { ElMessage.warning("请上传视频文件"); return; } selectedFile.value = f; };

const startAnalysis = async () => {
  if (!selectedFile.value) return;
  processing.value = true;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    fd.append("model_name", "visdrone-v1");
    fd.append("frame_interval", String(frameInterval.value));

    const res = await request({
      url: "/detection/video", method: "post", data: fd,
      headers: { "Content-Type": "multipart/form-data" }, timeout: 600000,
    });

    if (res.success && res.data) {
      videoData.value = res.data;
      ElMessage.success(res.message);
    } else {
      ElMessage.error(res.message || "分析失败");
    }
  } catch { ElMessage.error("分析失败，请检查后端"); }
  finally { processing.value = false; }
};

const reupload = () => {
  videoData.value = null; selectedFile.value = null;
  currentCount.value = 0; currentTime.value = 0;
};
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* Upload */
.upload-block { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 0; }
.upload-inner { padding: 40px; text-align: center; border: 2px dashed #d1d5db; border-radius: 10px; transition: all .2s; }
.upload-inner:hover { border-color: var(--primary); background: var(--primary-bg); }
.up-title { font-size: 16px; font-weight: 500; margin-top: 16px; }
.up-hint { font-size: 12px; color: var(--text-muted); margin: 6px 0 18px; }
.file-hidden { display: none; }
.upload-ctrls { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 16px; }
.ctrl-lbl { font-size: 13px; color: var(--text-secondary); }
.ctrl-hint { font-size: 11px; color: var(--text-muted); }
.file-ready { margin-top: 16px; display: flex; align-items: center; justify-content: center; font-size: 13px; gap: 4px; }

/* Layout */
.analysis-layout { display: flex; gap: 20px; }
.left-col { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 16px; }
.right-col { width: 300px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }

.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 18px; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-size: 14px; font-weight: 600; }
.badges { display: flex; gap: 6px; }

/* Player */
.player-wrapper { background: #000; border-radius: 8px; overflow: hidden; }
.video-el { width: 100%; display: block; }
.no-video { text-align: center; color: #6b7280; padding: 48px; }
.no-video p { margin-top: 12px; font-size: 13px; }
.player-actions { margin-top: 10px; text-align: right; }

/* Chart */
.chart-card { flex: 1; }
.chart-wrapper { height: 260px; }
.line-chart { width: 100%; height: 100%; }
.empty-chart { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-muted); font-size: 13px; }

/* Counter */
.counter-card { text-align: center; padding: 24px; position: relative; }
.live-dot { width: 10px; height: 10px; border-radius: 50%; background: #9ca3af; position: absolute; top: 16px; right: 16px; }
.live-dot.active { background: var(--danger); animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.counter-value { font-size: 48px; font-weight: 700; color: var(--primary); line-height: 1.1; }
.counter-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.counter-time { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* Stats */
.stats-col { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.mini-stat { text-align: center; background: #f9fafb; border-radius: 8px; padding: 12px 4px; }
.mini-num { font-size: 24px; font-weight: 700; }
.mini-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

/* Frame detail */
.frame-detail { display: flex; flex-direction: column; gap: 6px; }
.fd-row { display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; border-bottom: 1px solid #f3f4f6; }
.fd-name { color: var(--text-secondary); }
.fd-count { font-weight: 600; }
.empty-inline { text-align: center; font-size: 12px; color: var(--text-muted); padding: 24px; }
</style>
