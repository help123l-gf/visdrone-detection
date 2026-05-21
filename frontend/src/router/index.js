import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/LoginPage.vue"),
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("../views/RegisterPage.vue"),
  },
  {
    path: "/forgot-password",
    name: "ForgotPassword",
    component: () => import("../views/ForgotPasswordPage.vue"),
  },
  // ── 模块一：单图分析 ──
  {
    path: "/detection",
    name: "Detection",
    component: () => import("../views/DetectionPage.vue"),
  },
  // ── 模块二：批量归档 ──
  {
    path: "/batch",
    name: "Batch",
    component: () => import("../views/BatchPage.vue"),
  },
  // ── 模块三：视频分析 ──
  {
    path: "/video",
    name: "Video",
    component: () => import("../views/VideoPage.vue"),
  },
  // ── 模块四：实时监控 ──
  {
    path: "/monitor",
    name: "Monitor",
    component: () => import("../views/MonitorPage.vue"),
  },
  // ── 模块五：系统管理 ──
  {
    path: "/history",
    name: "History",
    component: () => import("../views/HistoryPage.vue"),
  },
  {
    path: "/targets",
    name: "Targets",
    component: () => import("../views/TargetsPage.vue"),
  },
  {
    path: "/profile",
    name: "Profile",
    component: () => import("../views/ProfilePage.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("token");
  const publicPaths = ["/login", "/register", "/forgot-password"];

  if (publicPaths.includes(to.path)) {
    next();
  } else if (!token) {
    next("/login");
  } else {
    next();
  }
});

export default router;
