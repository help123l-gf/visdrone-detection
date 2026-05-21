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
            <div class="uname">管理员</div>
            <div class="urole">系统运维</div>
            <el-tag size="small" type="success" effect="light">已认证</el-tag>
          </div>
        </div>
        <el-divider />
        <div class="info-list">
          <div class="il"><span>邮箱</span><span>admin@visdrone.cn</span></div>
          <div class="il"><span>注册时间</span><span>2026-05-01</span></div>
          <div class="il"><span>上次登录</span><span>2026-05-21 10:30</span></div>
        </div>
        <el-button type="primary" plain size="default" style="width:100%;margin-top:16px">编辑资料</el-button>
      </div>

      <div class="stats-cards">
        <div class="stat-card"><div class="sv">156</div><div class="sl">总检测次数</div></div>
        <div class="stat-card"><div class="sv">1,024</div><div class="sl">累计检测目标</div></div>
        <div class="stat-card"><div class="sv">98.7%</div><div class="sl">检测成功率</div></div>
        <div class="stat-card"><div class="sv">21</div><div class="sl">使用天数</div></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { UserFilled } from "@element-plus/icons-vue";
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
