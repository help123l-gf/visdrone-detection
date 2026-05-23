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
        <h1>重置密码</h1>
        <p>输入用户名和新密码直接重置</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名"><template #prefix><el-icon><User /></el-icon></template></el-input>
        </el-form-item>
        <el-form-item prop="new_password">
          <el-input v-model="form.new_password" type="password" placeholder="新密码（至少6位）"><template #prefix><el-icon><Lock /></el-icon></template></el-input>
        </el-form-item>
        <el-form-item prop="confirm">
          <el-input v-model="form.confirm" type="password" placeholder="确认新密码"><template #prefix><el-icon><Lock /></el-icon></template></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="auth-btn" :loading="loading" @click="handleReset">重 置 密 码</el-button>
        </el-form-item>
      </el-form>
      <div class="auth-footer"><router-link to="/login">返回登录</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { User, Lock } from "@element-plus/icons-vue";
import request from "../utils/request";

const router = useRouter();
const loading = ref(false);
const formRef = ref(null);
const form = reactive({ username: "", new_password: "", confirm: "" });

const validateConfirm = (_rule, value, cb) => {
  if (value !== form.new_password) cb(new Error("两次输入的密码不一致"));
  else cb();
};

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  new_password: [{ required: true, message: "请输入新密码", trigger: "blur" }, { min: 6, message: "至少6位", trigger: "blur" }],
  confirm: [{ required: true, message: "请确认密码", trigger: "blur" }, { validator: validateConfirm, trigger: "blur" }],
};

const handleReset = () => {
  formRef.value?.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    try {
      const res = await request({
        url: "/auth/reset-password",
        method: "post",
        data: { username: form.username, new_password: form.new_password },
      });
      if (res.success) {
        ElMessage.success("密码重置成功，请登录");
        router.push("/login");
      }
    } catch { } finally { loading.value = false; }
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
