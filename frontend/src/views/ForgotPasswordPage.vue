<template>
  <div class="auth-page">
    <div class="auth-bg"><div class="bg-grid"></div></div>
    <div class="auth-card">
      <div class="auth-header">
        <div class="auth-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1>找回密码</h1>
        <p>输入注册邮箱，我们将发送重置链接</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large">
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="注册邮箱"><template #prefix><el-icon><Message /></el-icon></template></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="auth-btn" :loading="loading" @click="handleSubmit">发送重置链接</el-button>
        </el-form-item>
      </el-form>
      <div class="auth-footer"><span>想起密码了？</span><router-link to="/login">返回登录</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { Message, Lock } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request from "../utils/request";

const router = useRouter();
const loading = ref(false);
const formRef = ref(null);
const form = reactive({ email: "" });
const rules = { email: [{ required: true, message: "请输入邮箱", trigger: "blur" }] };

const handleSubmit = async () => {
  formRef.value?.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    try {
      const res = await request.post("/auth/forgot-password", { email: form.email });
      if (res.success) {
        ElMessage.success(res.message || "重置令牌已发送至您的邮箱");
        if (res.data?.reset_token) {
          ElMessage.info("开发模式：重置令牌 " + res.data.reset_token.substring(0, 8) + "...");
        }
        router.push("/login");
      }
    } catch (e) {
      // error handled by interceptor
    } finally {
      loading.value = false;
    }
  });
};
</script>

<style scoped>
.auth-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; background: linear-gradient(135deg, #0c1419 0%, #1a2d3d 50%, #0f1923 100%); }
.auth-bg { position: absolute; inset: 0; overflow: hidden; }
.bg-grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px); background-size: 60px 60px; animation: grid-drift 20s linear infinite; }
@keyframes grid-drift { from { transform: translate(0,0); } to { transform: translate(60px,60px); } }

.auth-card { position: relative; z-index: 1; width: 420px; padding: 36px 40px 28px; background: rgba(255,255,255,0.97); border-radius: 16px; box-shadow: 0 24px 80px rgba(0,0,0,0.3); }
.auth-header { text-align: center; margin-bottom: 28px; }
.auth-logo { width: 48px; height: 48px; margin: 0 auto 12px; background: var(--primary); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; }
.auth-logo svg { width: 24px; height: 24px; }
.auth-header h1 { font-size: 18px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.auth-header p { font-size: 12px; color: var(--text-muted); }
.auth-btn { width: 100%; height: 44px; font-size: 15px; font-weight: 500; letter-spacing: 4px; border-radius: 8px; }
.auth-footer { text-align: center; font-size: 13px; color: var(--text-secondary); }
.auth-footer a { margin-left: 4px; }
</style>
