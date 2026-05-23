<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">个人中心</h1>
      <p class="page-desc">账户信息与使用统计</p>
    </div>

    <div class="profile-grid">
      <div class="card user-card">
        <div class="user-top">
          <el-avatar :size="72">
            <el-icon :size="36"><UserFilled /></el-icon>
          </el-avatar>
          <div class="user-detail">
            <div class="uname">{{ user.nickname || user.username || '用户' }}</div>
            <div class="urole">{{ user.role === 'admin' ? '系统管理员' : '普通用户' }}</div>
            <el-tag size="small" type="success" effect="light">{{ user.is_active ? '已认证' : '未激活' }}</el-tag>
          </div>
        </div>
        <el-divider />
        <div class="info-list">
          <div class="il"><span>邮箱</span><span>{{ user.email || '-' }}</span></div>
          <div class="il"><span>注册时间</span><span>{{ user.created_at ? user.created_at.substring(0, 10) : '-' }}</span></div>
          <div class="il"><span>用户ID</span><span>{{ user.id ? user.id.substring(0, 8) + '...' : '-' }}</span></div>
        </div>
        <el-button type="primary" plain size="default" style="width:100%;margin-top:16px" @click="$router.push('/history')">查看检测历史</el-button>
      </div>

      <div class="stats-cards">
        <div class="stat-card"><div class="sv">{{ stats.total_detections }}</div><div class="sl">总检测次数</div></div>
        <div class="stat-card"><div class="sv">{{ stats.total_objects.toLocaleString() }}</div><div class="sl">累计检测目标</div></div>
        <div class="stat-card"><div class="sv">{{ stats.success_rate }}%</div><div class="sl">检测成功率</div></div>
        <div class="stat-card"><div class="sv">--</div><div class="sl">使用天数</div></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { UserFilled } from "@element-plus/icons-vue";
import request from "../utils/request";

const user = ref({});
const stats = reactive({
  total_detections: 0,
  total_objects: 0,
  success_rate: 0,
});

onMounted(async () => {
  // 从 localStorage 恢复用户信息
  const stored = localStorage.getItem("user");
  if (stored) {
    try { user.value = JSON.parse(stored); } catch (e) {}
  }

  // 从 API 获取最新用户信息
  try {
    const res = await request.get("/auth/me");
    if (res.success && res.data) {
      user.value = res.data;
      localStorage.setItem("user", JSON.stringify(res.data));
    }
  } catch (e) {}

  // 获取统计信息
  try {
    const statRes = await request.get("/detection/stats");
    if (statRes.success && statRes.data) {
      stats.total_detections = statRes.data.total_detections || 0;
      stats.total_objects = statRes.data.total_objects || 0;
      stats.success_rate = statRes.data.success_rate || 0;
    }
  } catch (e) {}
});
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.profile-grid { display: flex; gap: 24px; }
.card { background: #fff; border-radius: 10px; box-shadow: var(--card-shadow); padding: 24px; }

.user-card { width: 320px; flex-shrink: 0; }
.user-top { display: flex; align-items: center; gap: 16px; }
.uname { font-size: 18px; font-weight: 600; }
.urole { font-size: 13px; color: var(--text-secondary); margin: 4px 0 8px; }

.info-list { display: flex; flex-direction: column; gap: 8px; }
.il { display: flex; justify-content: space-between; font-size: 13px; }
.il span:first-child { color: var(--text-secondary); }

.stats-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; flex: 1; }
.stat-card {
  background: #fff; border-radius: 10px; box-shadow: var(--card-shadow);
  padding: 24px; text-align: center; display: flex; flex-direction: column; justify-content: center;
}
.sv { font-size: 32px; font-weight: 700; color: var(--primary); }
.sl { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }
</style>
