<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-grid"></div>
    </div>

    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1>无人机交通态势感知系统</h1>
        <p>VisDrone · Intelligent Traffic Situation Awareness</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" @keyup.enter="handleLogin">
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <div class="form-extra">
            <el-checkbox v-model="form.remember">记住我</el-checkbox>
            <router-link to="/forgot-password">忘记密码？</router-link>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
            登 录 系 统
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span>还没有账号？</span>
        <router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { User, Lock } from "@element-plus/icons-vue";

const router = useRouter();
const loading = ref(false);
const formRef = ref(null);

const form = reactive({
  username: "",
  password: "",
  remember: false,
});

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const handleLogin = () => {
  formRef.value?.validate((valid) => {
    if (valid) {
      loading.value = true;
      setTimeout(() => {
        localStorage.setItem("token", "authenticated");
        router.push("/detection");
        loading.value = false;
      }, 600);
    }
  });
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0c1419 0%, #1a2d3d 50%, #0f1923 100%);
}

.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px);
  background-size: 60px 60px;
  animation: grid-drift 20s linear infinite;
}
@keyframes grid-drift {
  from { transform: translate(0, 0); }
  to { transform: translate(60px, 60px); }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 44px 40px 36px;
  background: rgba(255,255,255,0.97);
  border-radius: 16px;
  box-shadow: 0 24px 80px rgba(0,0,0,0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}
.login-logo {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  background: var(--primary);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.login-logo svg { width: 28px; height: 28px; }
.login-header h1 {
  font-size: 19px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.login-header p {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.form-extra {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.form-extra a { font-size: 13px; }

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 2px;
  border-radius: 8px;
}

.login-footer {
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary);
}
.login-footer a { margin-left: 4px; }
</style>
