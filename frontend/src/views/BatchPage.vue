<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">批量归档</h1>
      <p class="page-desc">批量处理多张航拍图片或 ZIP 压缩包，生成巡航分析报告</p>
    </div>

    <!-- Upload & control -->
    <div class="batch-upload card">
      <div class="batch-upload-area" @dragover.prevent @drop.prevent="handleDrop">
        <input ref="batchInput" type="file" accept="image/*,.zip" multiple class="file-hidden" @change="handleFiles" />
        <el-icon :size="44"><FolderOpened /></el-icon>
        <p class="batch-text">拖拽图片或 ZIP 压缩包到此处</p>
        <p class="batch-hint">支持多选 JPG/PNG，或上传 .zip 压缩包</p>
        <el-button type="primary" size="default" @click.stop="$refs.batchInput.click()">
          <el-icon><Plus /></el-icon>选择文件
        </el-button>
      </div>
    </div>

    <!-- Processing bar -->
    <div v-if="isProcessing" class="card">
      <div class="card-header">
        <span class="card-title">处理进度</span>
        <span class="progress-text">{{ processed }} / {{ total }} 张</span>
      </div>
      <el-progress :percentage="Math.round((processed / total) * 100)" :stroke-width="16" :text-inside="true" />
      <!-- TODO: 接入真实批量检测API后替换 processed/total -->
    </div>

    <!-- Report section (shown after processing) -->
    <div v-if="reportReady" class="report-section">
      <h2 class="section-title">巡航分析报告</h2>

      <div class="report-grid">
        <!-- ECharts pie chart -->
        <div class="card chart-card">
          <div class="card-header">
            <span class="card-title">目标类别分布</span>
          </div>
          <div ref="pieChartRef" class="chart-container"></div>
          <!-- TODO: 接入 ECharts 饼图 (vue-echarts 已安装) -->
        </div>

        <!-- Peak congestion -->
        <div class="card peak-card">
          <div class="card-header">
            <span class="card-title">车流密度极值</span>
            <el-tag type="danger" size="small">拥堵峰值</el-tag>
          </div>
          <div class="peak-content">
            <div class="peak-thumb">
              <el-icon :size="48"><Picture /></el-icon>
              <!-- TODO: 替换为实际最拥堵图片缩略图 -->
            </div>
            <div class="peak-info">
              <div class="peak-number">—</div>
              <div class="peak-label">峰值车辆数</div>
              <!-- TODO: 从批量检测结果中选出 max(total_objects) -->
            </div>
          </div>
        </div>
      </div>

      <!-- Download button -->
      <div class="download-area">
        <el-button type="primary" size="large">
          <el-icon><Download /></el-icon>打包下载检测结果
        </el-button>
        <!-- TODO: 实现后端 ZIP 打包 + MinIO 存储 + 下载链接 -->
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!isProcessing && !reportReady" class="card empty-batch">
      <el-icon :size="56"><Box /></el-icon>
      <p class="empty-title">等待批量任务</p>
      <p class="empty-desc">上传多张图片或 ZIP 压缩包后，点击"开始批量处理"即可生成巡航报告</p>
    </div>

    <!-- Start button -->
    <div class="action-bar" v-if="fileCount > 0 && !isProcessing && !reportReady">
      <el-button type="primary" size="large" :disabled="fileCount === 0" @click="startBatch">
        <el-icon><VideoPlay /></el-icon>开始批量处理
      </el-button>
      <span class="file-count">已选择 {{ fileCount }} 个文件</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { FolderOpened, Plus, Picture, Download, Box, VideoPlay } from "@element-plus/icons-vue";

const batchInput = ref(null);
const isProcessing = ref(false);
const reportReady = ref(false);
const processed = ref(0);
const total = ref(0);
const fileCount = ref(0);

const handleDrop = (e) => {
  const files = e.dataTransfer.files;
  if (files.length) loadFiles(files);
};

const handleFiles = (e) => {
  const files = e.target.files;
  if (files.length) loadFiles(files);
  e.target.value = "";
};

const loadFiles = (files) => {
  fileCount.value = files.length;
  total.value = files.length;
  ElMessage.info(`已加载 ${files.length} 个文件`);
  // TODO: 存储文件列表，调用批量检测 API
};

const startBatch = () => {
  isProcessing.value = true;
  processed.value = 0;
  reportReady.value = false;
  // TODO: 逐张调用 POST /api/detection/batch，更新 processed
  // 模拟进度
  const timer = setInterval(() => {
    if (processed.value >= total.value) {
      clearInterval(timer);
      isProcessing.value = false;
      reportReady.value = true;
      ElMessage.success("批量处理完成");
      // TODO: 汇总数据，渲染 ECharts 饼图
    } else {
      processed.value++;
    }
  }, 200);
};
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.batch-upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 10px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.batch-upload-area:hover { border-color: var(--primary); background: var(--primary-bg); }
.batch-text { font-size: 15px; font-weight: 500; margin-top: 12px; }
.batch-hint { font-size: 12px; color: var(--text-muted); margin: 6px 0 16px; }
.file-hidden { display: none; }

.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 18px; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-size: 14px; font-weight: 600; }
.progress-text { font-size: 13px; color: var(--text-secondary); }

.section-title { font-size: 16px; font-weight: 600; margin: 24px 0 16px; }

.report-grid { display: grid; grid-template-columns: 1fr 360px; gap: 20px; margin-bottom: 20px; }

.chart-container { height: 300px; }
/* TODO: 使用 <v-chart :option="pieOption" /> 渲染 ECharts */

.peak-content { display: flex; align-items: center; gap: 20px; }
.peak-thumb {
  width: 120px; height: 90px; background: #f3f4f6;
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
}
.peak-number { font-size: 36px; font-weight: 700; color: var(--danger); }
.peak-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.download-area { text-align: center; padding: 20px; }

.empty-batch { text-align: center; padding: 60px 20px; }
.empty-title { font-size: 15px; font-weight: 500; margin-top: 16px; }
.empty-desc { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }

.action-bar { display: flex; align-items: center; gap: 16px; margin-top: 20px; }
.file-count { font-size: 13px; color: var(--text-secondary); }
</style>
