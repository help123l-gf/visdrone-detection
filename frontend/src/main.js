import { createApp } from "vue"; //用来创建一个 Vue 应用实例
import "./style.css"; // 直接引入一个全局 CSS 文件,让整个应用都有这些基础样式
import App from "./App.vue";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import router from "./router";
import pinia from "./stores";

const app = createApp(App);
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}
app.use(ElementPlus);
app.use(router);
app.use(pinia);

app.mount("#app");
