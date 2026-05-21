<template>
  <div class="sidebar">
    <!-- Logo -->
    <div class="sidebar-brand">
      <div class="brand-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
      </div>
      <div class="brand-text">
        <div class="brand-name">交通态势感知</div>
        <div class="brand-sub">VisDrone Platform</div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <div v-for="group in navGroups" :key="group.label" class="nav-group">
        <div class="nav-group-label">{{ group.label }}</div>
        <router-link
          v-for="item in group.items"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span>{{ item.name }}</span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </router-link>
      </div>
    </nav>

    <!-- System footer -->
    <div class="sidebar-footer">
      <div class="system-status">
        <span class="status-dot"></span>
        <span>系统运行中</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from "vue-router";
import { Picture, Box, VideoCamera, Monitor, Clock, Collection, User } from "@element-plus/icons-vue";

const route = useRoute();

const navGroups = [
  {
    label: "检测功能",
    items: [
      { name: "单图分析", path: "/detection", icon: Picture },
      { name: "批量归档", path: "/batch", icon: Box },
      { name: "视频分析", path: "/video", icon: VideoCamera },
      { name: "实时监控", path: "/monitor", icon: Monitor, badge: "NEW" },
    ],
  },
  {
    label: "系统管理",
    items: [
      { name: "历史台账", path: "/history", icon: Clock },
      { name: "目标分类库", path: "/targets", icon: Collection },
      { name: "个人中心", path: "/profile", icon: User },
    ],
  },
];

const isActive = (path) => {
  if (path === "/detection") return route.path === "/detection";
  if (path === "/batch") return route.path.startsWith("/batch");
  if (path === "/video") return route.path.startsWith("/video");
  if (path === "/monitor") return route.path.startsWith("/monitor");
  return route.path === path;
};
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  color: var(--sidebar-text);
}

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  padding: 18px 20px;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand-icon {
  width: 38px;
  height: 38px;
  background: var(--primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.brand-icon svg {
  width: 20px;
  height: 20px;
}
.brand-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  letter-spacing: 0.5px;
}
.brand-sub {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 12px 12px;
}
.nav-group {
  margin-bottom: 8px;
}
.nav-group-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #475569;
  padding: 12px 12px 6px;
}
.nav-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  color: var(--sidebar-text);
  font-size: 14px;
  transition: all 0.15s;
  margin-bottom: 2px;
  cursor: pointer;
  text-decoration: none;
}
.nav-item:hover {
  background: var(--sidebar-hover);
  color: #cbd5e1;
}
.nav-item.active {
  background: var(--sidebar-active);
  color: var(--sidebar-text-active);
  font-weight: 500;
}
.nav-item .el-icon {
  margin-right: 10px;
  flex-shrink: 0;
}
.nav-item span {
  white-space: nowrap;
}
.nav-badge {
  margin-left: auto;
  font-size: 10px;
  background: var(--primary);
  color: #fff;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 600;
}

/* Footer */
.sidebar-footer {
  padding: 12px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.system-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #64748b;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
  animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
