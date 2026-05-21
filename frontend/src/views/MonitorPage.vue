<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">实时监控</h1>
      <p class="page-desc">调用本地摄像头，实时检测画面中的目标并提供异常告警</p>
    </div>

    <!-- Alert bar -->
    <div class="alert-bar" :class="{ active: isAlerting }">
      <span class="alert-icon">{{ isAlerting ? '🚨' : '✅' }}</span>
      <span class="alert-text" v-if="isAlerting">⚠️ 警告：当前监控区域出现异常拥堵</span>
      <span class="alert-text" v-else>系统正常运行中，当前未触发告警阈值</span>
      <span class="alert-count">阈值: {{ alertThreshold }} 个目标</span>
    </div>

    <!-- Main monitor -->
    <div class="monitor-layout">
      <!-- Camera feed -->
      <div class="monitor-main card">
        <div class="monitor-header">
          <span class="monitor-title">
            <span class="live-indicator" :class="{ active: isMonitoring }"></span>
            {{ isMonitoring ? '实时画面' : '摄像头未开启' }}
          </span>
          <div class="monitor-controls">
            <el-input-number v-model="alertThreshold" :min="5" :max="100" :step="5" size="small" style="width:130px" />
            <el-button :type="isMonitoring ? 'danger' : 'primary'" size="small" @click="toggleMonitor">
              <el-icon><component :is="isMonitoring ? 'VideoPause' : 'VideoPlay'" /></el-icon>
              {{ isMonitoring ? '关闭监控' : '启动监控' }}
            </el-button>
          </div>
        </div>
        <div class="camera-feed">
          <video ref="camera" autoplay playsinline class="camera-video"></video>
          <div v-if="!isMonitoring" class="camera-off">
            <el-icon :size="56"><VideoCamera /></el-icon>
            <p>点击"启动监控"开启摄像头</p>
          </div>
        </div>
      </div>

      <!-- Side metrics -->
      <div class="monitor-side">
        <!-- Real-time stats -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">实时指标</span>
          </div>
          <div class="realtime-grid">
            <div class="rt-item">
              <div class="rt-value" :class="{ alert: isAlerting }">{{ liveCount }}</div>
              <div class="rt-label">当前目标数</div>
            </div>
            <div class="rt-item">
              <div class="rt-value">{{ fps }}</div>
              <div class="rt-label">FPS</div>
            </div>
            <div class="rt-item">
              <div class="rt-value">{{ elapsed }}</div>
              <div class="rt-label">运行时长(s)</div>
            </div>
            <div class="rt-item">
              <div class="rt-value">{{ totalDetections }}</div>
              <div class="rt-label">累计检测</div>
            </div>
          </div>
        </div>

        <!-- Alert log -->
        <div class="card alert-log-card">
          <div class="card-header">
            <span class="card-title">告警记录</span>
            <el-tag :type="isAlerting ? 'danger' : 'success'" size="small" effect="dark">
              {{ isAlerting ? '告警中' : '正常' }}
            </el-tag>
          </div>
          <div class="log-list">
            <div v-if="alertLogs.length === 0" class="log-empty">暂无告警记录</div>
            <div v-for="(log, i) in alertLogs" :key="i" class="log-item">
              <span class="log-time">{{ log.time }}</span>
              <span class="log-msg">{{ log.count }} 个目标 — 触发告警</span>
            </div>
            <!-- TODO: 接入 WebSocket 实时推送告警事件 -->
          </div>
        </div>
      </div>
    </div>

    <!-- Device status bar -->
    <div class="status-bar">
      <span class="status-item">
        <span class="s-dot green"></span>摄像头: {{ isMonitoring ? '已连接' : '未连接' }}
      </span>
      <span class="status-item">
        <span class="s-dot green"></span>模型: visdrone-v1
      </span>
      <span class="status-item">
        <span class="s-dot" :class="isAlerting ? 'red' : 'green'"></span>
        告警状态: {{ isAlerting ? '触发' : '正常' }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from "vue";
import { ElMessage } from "element-plus";
import { VideoPlay, VideoPause, VideoCamera } from "@element-plus/icons-vue";

let stream = null;
let timer = null;

const camera = ref(null);
const isMonitoring = ref(false);
const isAlerting = ref(false);
const alertThreshold = ref(20);
const liveCount = ref(0);
const fps = ref(0);
const elapsed = ref(0);
const totalDetections = ref(0);
const alertLogs = ref([]);

const toggleMonitor = async () => {
  if (isMonitoring.value) {
    stopMonitor();
  } else {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
      if (camera.value) camera.value.srcObject = stream;
      isMonitoring.value = true;
      ElMessage.success("摄像头已启动");
      startSimulation();
      // TODO: 将摄像头帧发送到后端 POST /api/detection/monitor/frame 获取检测结果
    } catch {
      ElMessage.error("无法访问摄像头，请检查权限设置");
    }
  }
};

const stopMonitor = () => {
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
  if (timer) { clearInterval(timer); timer = null; }
  isMonitoring.value = false;
  liveCount.value = 0;
};

const startSimulation = () => {
  // TODO: 替换为真实的 WebSocket 或轮询后端检测结果
  timer = setInterval(() => {
    elapsed.value++;
    liveCount.value = Math.floor(Math.random() * 30);
    totalDetections.value += liveCount.value;
    fps.value = Math.floor(Math.random() * 10 + 20);
    if (liveCount.value > alertThreshold.value && !isAlerting.value) {
      isAlerting.value = true;
      const now = new Date().toLocaleTimeString();
      alertLogs.value.unshift({ time: now, count: liveCount.value });
    } else if (liveCount.value <= alertThreshold.value && isAlerting.value) {
      isAlerting.value = false;
    }
  }, 1000);
};

onUnmounted(() => stopMonitor());
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* Alert bar */
.alert-bar {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;
  background: #f0fdf4; border: 1px solid rgba(34,197,94,.2);
  transition: all 0.3s;
}
.alert-bar.active {
  background: #fef2f2; border-color: rgba(239,68,68,.3);
  animation: alert-flash 1s infinite;
}
@keyframes alert-flash { 0%,100%{opacity:1} 50%{opacity:.8} }
.alert-icon { font-size: 20px; }
.alert-text { flex: 1; font-size: 14px; font-weight: 500; }
.alert-bar.active .alert-text { color: var(--danger); }
.alert-count { font-size: 12px; color: var(--text-muted); }

/* Monitor layout */
.monitor-layout { display: flex; gap: 20px; }
.monitor-main { flex: 1; min-width: 0; }
.monitor-side { width: 300px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }

.monitor-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.monitor-title { font-size: 15px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.live-indicator { width: 9px; height: 9px; border-radius: 50%; background: #9ca3af; }
.live-indicator.active { background: var(--danger); animation: pulse-dot 1.5s infinite; }
.monitor-controls { display: flex; align-items: center; gap: 10px; }

.camera-feed {
  background: #000; border-radius: 8px; aspect-ratio: 16/9;
  display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
}
.camera-video { width: 100%; height: 100%; object-fit: contain; }
.camera-off { text-align: center; color: #4a5568; }
.camera-off p { margin-top: 12px; }

/* Cards */
.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 18px; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-size: 14px; font-weight: 600; }

/* Real-time grid */
.realtime-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.rt-item { text-align: center; padding: 14px 4px; background: #f9fafb; border-radius: 8px; }
.rt-value { font-size: 28px; font-weight: 700; color: var(--primary); }
.rt-value.alert { color: var(--danger); }
.rt-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

/* Log */
.alert-log-card { flex: 1; }
.log-list { max-height: 200px; overflow-y: auto; }
.log-empty { text-align: center; color: var(--text-muted); padding: 24px; font-size: 13px; }
.log-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6; font-size: 12px; }
.log-time { color: var(--text-muted); }
.log-msg { color: var(--danger); }

/* Status bar */
.status-bar {
  display: flex; gap: 32px; margin-top: 20px;
  padding: 10px 20px; background: #fff; border-radius: 8px; box-shadow: var(--card-shadow);
}
.status-item { font-size: 12px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
.s-dot { width: 7px; height: 7px; border-radius: 50%; }
.s-dot.green { background: var(--success); }
.s-dot.red { background: var(--danger); animation: pulse-dot 1s infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:.3} }
</style>
