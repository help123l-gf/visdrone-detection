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

// 路由文件 router/index.js 做了什么
// 它定义了一张URL 和页面组件的映射表（routes 数组）。

// 当你在浏览器地址栏输入不同路径时，Router 会从这张表里找到对应的组件。例如：

// /login → 加载 LoginPage.vue

// /detection → 加载 DetectionPage.vue

// 特别的路由：path: "/" 没有直接加载组件，而是 redirect: "/login"，意思是访问根路径时立即重定向到登录页。

// 导航守卫 router.beforeEach 是一道检查：每次路由跳转前，它看本地存储里有没有 token（登录凭证）。

// 如果去的是 /login、/register、/forgot-password 这几个公开页面，直接放行。

// 否则，如果没有 token，就强制跳转到 /login。

// 有 token 才允许进入需要登录的页面。

// 这一层保证了：未登录用户看不到 /detection、/batch 等内部页面，只能被推到登录页