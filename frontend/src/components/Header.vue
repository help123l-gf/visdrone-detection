<template>
  <div class="header">
    <div class="header-left">
      <div class="breadcrumb">
        <el-icon class="bc-icon"><HomeFilled /></el-icon>
        <span class="bc-sep">/</span>
        <span class="bc-text">{{ currentPageName }}</span>
      </div>
    </div>

    <div class="header-right">
      <el-tooltip content="通知" placement="bottom">
        <el-badge :value="3" :max="99" class="header-action">
          <el-icon :size="20"><Bell /></el-icon>
        </el-badge>
      </el-tooltip>

      <el-dropdown trigger="click">
        <div class="user-area">
          <el-avatar :size="32" class="user-avatar">
            <el-icon :size="18"><UserFilled /></el-icon>
          </el-avatar>
          <div class="user-info">
            <span class="user-name">管理员</span>
            <span class="user-role">系统运维</span>
          </div>
          <el-icon class="user-arrow"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>
              <el-icon><User /></el-icon>个人中心
            </el-dropdown-item>
            <el-dropdown-item>
              <el-icon><Setting /></el-icon>系统设置
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { HomeFilled, Bell, UserFilled, ArrowDown, User, Setting, SwitchButton } from "@element-plus/icons-vue";

const route = useRoute();
const router = useRouter();

const nameMap = {
  "/detection": "单图分析",
  "/batch": "批量归档",
  "/video": "视频分析",
  "/monitor": "实时监控",
  "/history": "历史台账",
  "/targets": "目标分类库",
  "/profile": "个人中心",
};

const currentPageName = computed(() => {
  return nameMap[route.path] || "未知页面";
});

const handleLogout = () => {
  localStorage.removeItem("token");
  router.push("/login");
};
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.header-left {
  display: flex;
  align-items: center;
}
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
}
.bc-icon { color: var(--text-secondary); font-size: 14px; }
.bc-sep { color: var(--text-muted); font-size: 14px; }
.bc-text { font-size: 14px; color: var(--text-primary); font-weight: 500; }

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.header-action {
  cursor: pointer;
  color: var(--text-secondary);
}
.header-action:hover {
  color: var(--primary);
}

.user-area {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: background 0.15s;
}
.user-area:hover { background: #f3f4f6; }
.user-avatar {
  background: var(--primary-light);
  color: var(--primary);
}
.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.user-name { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.user-role { font-size: 11px; color: var(--text-secondary); }
.user-arrow { font-size: 12px; color: var(--text-muted); }
</style>
