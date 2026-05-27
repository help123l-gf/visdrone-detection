# VisDrone Detection Platform 无人机交通态势感知系统

基于 YOLO11 无人机航拍视觉的智能交通态势感知系统。支持单图分析、批量归档、视频分析、实时监控四大检测模块，输出拥堵评级、密度分析、历史台账。

**演示环境默认账号：admin / admin123**

---

## 快速开始

```bash
# 1. 启动基础服务（需要 Docker Desktop）
docker-compose up -d

# 2. 启动后端（Python 3.10+）
cd backend
pip install -r requirements.txt    # 首次
python main.py                      # http://localhost:8000

# 3. 启动前端（Node 18+）
cd frontend
npm install                         # 首次
npm run dev                         # http://localhost:5173
```

浏览器打开 `http://localhost:5173`，登录后使用。

### GPU 推理（可选）

```bash
cd backend
uv pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Vite + Element Plus + ECharts |
| 后端 | FastAPI + Uvicorn |
| 目标检测 | Ultralytics YOLO11（双模型） |
| 数据库 | PostgreSQL 15 |
| 缓存 | Redis 7 |
| 对象存储 | MinIO（S3 兼容） |
| 视频处理 | OpenCV + imageio-ffmpeg |
| 实时通信 | WebSocket |
| 认证 | JWT + bcrypt |

---

## 五个功能模块

### 模块一：单图分析

上传无人机航拍图片，YOLO 检测 10 类 VisDrone 目标，输出交通态势评估报告。

- **拥堵评级**：车距聚类算法（成对车宽归一化 + PCA 线性停车线过滤），自动判别「道路畅通 / 交通缓行 / 严重拥堵」
- **车辆分布特征**：聚类率进度条、聚类数量、平均车距
- **车辆类型分布**：8 类车辆水平条形图
- **车辆规模构成**：小型 / 中型 / 大型目标按 bbox 面积三分
- **目标明细**：按类别聚合的统计表格

### 模块二：批量归档

多图批量检测 + ZIP 上传，生成巡航分析报告。

- 支持多选图片或上传 .zip 压缩包
- ECharts 环形饼图展示目标类别分布占比
- 峰值拥堵图片高亮 + 结果网格浏览
- 一键打包下载标注结果（ZIP）

### 模块三：视频分析

上传无人机航拍视频，逐帧检测并生成标注视频。

- YOLO 逐帧推理 → imageio H.264 编码标注视频
- ECharts 动态折线图（时间 × 目标数）带各类别堆叠面积图
- 视频播放同步：当前帧目标数 + 帧级类别明细
- 峰值 / 均值 / 已处理帧统计

### 模块四：实时监控

调用本地摄像头 + WebSocket 实时推流检测。

- 每 120ms 抓一帧 JPEG → WebSocket 发后端 → YOLO 推理 → 返回框坐标
- Canvas 实时画框（requestAnimationFrame）
- 可调阈值告警栏：目标数超阈值时红色闪烁
- 告警记录滚动日志 + 实时指标（FPS / 累计检测 / 告警次数）
- 双模型切换：COCO（近景摄像头演示）/ VisDrone（航拍）

### 模块五：系统管理

- **登录 / 注册 / 忘记密码**：JWT 认证 + bcrypt 密码哈希
- **历史台账**：数据表格分页展示，支持按类型 / 日期筛选，详情弹窗查看标注图 + 目标列表
- **目标分类库**：VisDrone 10 类目标卡片展示
- **个人中心**：用户信息 + 真实检测统计（总次数 / 累计目标 / 成功率 / 使用天数）

---

## 项目结构

```
visdrone-detection/
├── docker-compose.yml              # PostgreSQL + Redis + MinIO
├── storage/
│   ├── postgres/init/init_db.sql   # 数据库建表 + 初始数据
│   ├── redis/data/                 # Redis 持久化
│   └── minio/data/                 # MinIO 存储
│
├── backend/
│   ├── main.py                     # FastAPI 入口
│   ├── .env                        # 环境变量配置
│   ├── yolo11m_visdrone.pt         # VisDrone 微调模型 (39MB, 10类)
│   ├── yolo11n.pt                  # COCO 预训练模型 (5.4MB, 80类)
│   ├── static/
│   │   ├── uploads/                # 上传原图
│   │   └── results/                # 标注图 + 标注视频
│   └── app/
│       ├── config.py               # 配置加载
│       ├── database.py             # SQLAlchemy 数据库
│       ├── redis_client.py         # Redis 客户端
│       ├── api/
│       │   ├── detection.py        # 检测路由 (单图/批量/视频/WS/历史/下载)
│       │   └── auth.py             # 认证路由 (登录/注册/重置/统计)
│       ├── services/
│       │   ├── detection_service.py    # YOLO 双模型 + 聚类算法
│       │   ├── auth_service.py         # 密码 + JWT
│       │   └── storage_service.py      # MinIO 上传/删除
│       ├── models/
│       │   ├── schemas.py          # Pydantic 请求/响应模型
│       │   └── db_models.py        # SQLAlchemy ORM
│       └── utils/
│           ├── file_utils.py       # 文件保存
│           └── security.py         # JWT + bcrypt
│
└── frontend/
    ├── vite.config.js              # Vite 配置 + /api 代理
    └── src/
        ├── main.js                 # Vue 入口
        ├── App.vue
        ├── style.css               # 全局主题
        ├── router/index.js         # 路由
        ├── utils/request.js        # Axios 封装
        ├── api/detection.js        # 所有 API 函数
        ├── layouts/MainLayout.vue  # 主布局（暗色侧边栏）
        ├── components/
        │   ├── Sidebar.vue         # 导航
        │   ├── Header.vue          # 顶栏
        │   └── SliderCompare.vue   # 滑块对比
        └── views/
            ├── LoginPage.vue
            ├── RegisterPage.vue
            ├── ForgotPasswordPage.vue
            ├── DetectionPage.vue   # 模块一
            ├── BatchPage.vue       # 模块二
            ├── VideoPage.vue       # 模块三
            ├── MonitorPage.vue     # 模块四
            ├── HistoryPage.vue     # 模块五
            ├── TargetsPage.vue
            └── ProfilePage.vue
```

---

## API 速查

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 → JWT |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/reset-password` | 重置密码 |
| GET | `/api/auth/me` | 当前用户 |
| GET | `/api/auth/stats` | 用户检测统计 |
| POST | `/api/detection/single` | 单图检测 |
| POST | `/api/detection/batch` | 批量检测 |
| POST | `/api/detection/video` | 视频分析 |
| WS | `/api/detection/ws/monitor` | 实时监控 |
| GET | `/api/detection/history` | 历史记录 |
| GET | `/api/detection/detail/{id}` | 检测详情 |
| DELETE | `/api/detection/delete/{id}` | 删除记录 |
| GET | `/api/detection/download` | 下载结果 ZIP |
| GET | `/api/detection/targets/list` | 目标类别 |

---

## 双模型

| 模型 | 文件 | 类别数 | 用途 |
|------|------|--------|------|
| visdrone-v1 | yolo11m_visdrone.pt | 10（行人/汽车/卡车等） | 无人机航拍 |
| coco | yolo11n.pt | 80（人/车/日用品等） | 摄像头近景演示 |

WebSocket 监控默认用 COCO，其余模块用 VisDrone。启动时两个模型同时加载到 GPU。

---

## 拥堵评级算法

1. **成对车宽归一化**：车 A 与车 B 的像素距离 ÷ 两车平均宽度 → 消除近大远小的透视形变
2. **BFS 聚类**：间距 < 2.5 车宽视为同一聚类
3. **PCA 线性过滤**：协方差矩阵特征值比 > 4 → 线性排列 → 疑似路边停车 → 排除
4. **交通聚类率**：属于团状聚类的车辆 ÷ 总车辆
5. **评级**：聚类率 ≥ 75% → 拥堵，≥ 45% → 缓行，< 45% → 畅通

算法位于 `backend/app/services/detection_service.py` 的 `compute_clustering()` 方法，单图和批量共用。

---

## 数据库

| 表 | 说明 |
|----|------|
| users | 用户（用户名/邮箱/密码哈希/角色） |
| detection_records | 检测记录（类型/模型/目标数/耗时/文件key/时间） |
| detection_results | 每框结果（x1,y1,x2,y2/置信度/类别ID/类别名） |
| target_categories | VisDrone 10 类目标（中英文名/描述/颜色） |

```bash
# 直连数据库
docker exec -it visdrone-postgres psql -U visdrone_user -d visdrone_db
# 查看所有表
\dt
# 查最近 10 条记录
SELECT type, model_name, total_objects, created_at FROM detection_records ORDER BY created_at DESC LIMIT 10;
```

MinIO 控制台：`http://localhost:9001`（minioadmin / minioadmin）

Redis 验证：`docker exec visdrone-redis redis-cli KEYS "visdrone:*"`

---

## 开发说明

### 数据流追踪

```
用户操作 → frontend/src/views/XxxPage.vue
         → import X from "../api/detection.js"   ← 找到 API 调用
         → request({ url: "/detection/xxx" })    ← 对应的路由
         → backend/app/api/detection.py          ← 路由处理函数
         → services/detection_service.py         ← YOLO 推理
         → PostgreSQL / MinIO / Redis            ← 数据持久化
```

### 环境变量

所有配置在 `backend/.env`，包括数据库连接、模型路径、MinIO 地址等。修改后重启后端生效。

### 代码规范

- Python：`app/api/` 只接收请求和返回响应，`app/services/` 放业务逻辑
- Vue：每个页面通过 `api/detection.js` 发请求，不直接 import `request`
- 注释：全部中文注释
