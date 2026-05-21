<template>
  <div class="container">
    <h2>🎯 无人机视觉检测平台</h2>
    
    <div class="test-box">
      <button class="test-btn" @click="testConnect">⚡ 测试前后端连接</button>
      <div class="result" v-if="res">{{ res }}</div>
    </div>

    <hr style="margin: 30px 0;">

    <div v-if="compareMode === 'slider'" class="slider-container">
      <SliderCompare 
        :before="originalImage" 
        :after="annotatedImage" 
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SliderCompare from '../components/SliderCompare.vue'

// 连通性测试的相关变量和函数
const res = ref("")
const testConnect = async () => {
  try {
    // 【修复Bug处】补全了完整的正确路径 /api/test/connect
    const response = await fetch("http://localhost:8000/health");
    const data = await response.json();
    res.value = data.status;
  } catch (e) {
    res.value = "❌ 连接后端失败，请检查后端终端是否正在运行 uvicorn";
  }
};

// 滑块组件的相关变量
const compareMode = ref('slider')
const originalImage = ref('')
const annotatedImage = ref('')
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}
.test-box {
  margin: 20px 0;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}
.test-btn {
  padding: 10px 20px;
  font-size: 16px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.test-btn:hover {
  background-color: #66b1ff;
}
.result {
  font-size: 18px;
  color: #67c23a;
  font-weight: bold;
  margin-top: 15px;
}
.slider-container {
  width: 100%;
  margin: 0 auto;
}
</style>