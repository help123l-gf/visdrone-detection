# VisDrone Detection Platform

基于无人机航拍视觉的智能交通态势感知系统。上传无人机影像，YOLO 检测 10 类目标（行人/汽车/卡车等），输出拥堵评级、密度分析、历史台账。

## 运行

```bash
docker-compose up -d
cd backend && python main.py    # 后端 :8000
cd frontend && npm run dev      # 前端 :5173
```
登录: admin / admin123

---

## 从零起步：点一个按钮，代码走到哪里？

所有前端页面在 `frontend/src/views/`，所有后端路由在 `backend/app/api/`。

### 翻开前端

浏览器 `localhost:5173` → Vite 找到 `frontend/src/main.js` → 创建 Vue → 读 `router/index.js` → 默认跳 `/login` → 加载 `LoginPage.vue`

**`frontend/src/views/` 里 7 个页面，文件名就是功能名：**
- `LoginPage.vue` → 登录
- `DetectionPage.vue` → 单图分析（模块一）
- `BatchPage.vue` → 批量归档（模块二）
- `VideoPage.vue` → 视频分析（模块三）
- `MonitorPage.vue` → 实时监控（模块四）
- `HistoryPage.vue` → 历史台账
- `TargetsPage.vue` → 目标库
- `ProfilePage.vue` → 个人中心

**每个 `.vue` 文件里 `<script setup>` 块就是逻辑入口。** 数据从哪里来？找 `import ... from "../api/detection"` 这句，它引用了 `frontend/src/api/detection.js`。

### 翻开后端

`frontend/src/api/detection.js` 里每行函数对应一个后端路由。比如：
```js
export const detectSingleImage = (data) => request({ url: "/detection/single", method: "post", data, ... });
```
这意味着 `POST /api/detection/single`。

**所有后端路由在 `backend/app/api/` 里：**
- `detection.py` → `/api/detection/*` 全部检测相关路由
- `auth.py` → `/api/auth/*` 认证相关路由

`vite.config.js` 里配了代理：`/api` → `localhost:8000`，所以前端调 `/api/detection/single` 实际到了后端的 `POST /api/detection/single`。

打开 `detection.py`，搜索 `@router.post("/single")` 就找到了处理函数。

### 追踪一个完整请求

以单图检测为例：

```
1. 用户拖入图片 → DetectionPage.vue:406 detectSingleImage()
                                        ↓
2. 前端API         api/detection.js:3  POST /api/detection/single
                                        ↓  (Vite proxy: /api → :8000)
3. 后端路由         detection.py:87     @router.post("/single")
                                        ↓
4. 检测服务         detection_service.py:94  detect_single_image()
                                        ↓
5. 数据库           detection.py:31     _save_record() → PostgreSQL
                                        ↓
6. 返回JSON → 前端 DetectionPage.vue:440 渲染拥堵评级+分布图
```

### 项目文件夹为什么是这个样子

```
backend/
├── main.py              ← 唯一入口。uvicorn 读这个文件启动一切
├── .env                 ← 配置（只改这一个文件就能改端口/密码/模型路径）
├── yolo11m_visdrone.pt  ← 训练好的模型文件
├── yolo11n.pt
├── app/
│   ├── config.py        ← 读 .env → 变成 Python 变量（settings.YOLO_MODEL_PATH 等）
│   ├── database.py      ← 连 PostgreSQL
│   ├── api/             ← 路由层（接收请求、调用服务、返回响应）   [前端先看这]
│   ├── services/        ← 业务逻辑（YOLO推理、密码加密、MinIO上传） [后端核心]
│   ├── models/          ← 数据结构定义（Pydantic请求/响应 + SQLAlchemy表映射）
│   └── utils/           ← 工具函数（文件保存、JWT生成）
│
frontend/
├── index.html           ← 浏览器先加载这个
├── vite.config.js       ← 开发服务器配置 + /api 代理
├── src/
│   ├── main.js          ← Vue 启动入口
│   ├── App.vue          ← 最外层组件
│   ├── router/index.js  ← URL → 页面映射
│   ├── style.css        ← 全局颜色/字体
│   ├── utils/request.js ← Axios 封装（拦截器加 token）
│   ├── api/detection.js ← 所有后端 API 调用 [数据流起点]
│   ├── layouts/         ← 页面外壳（侧边栏+顶栏）
│   ├── components/      ← 可复用组件
│   └── views/           ← 每个页面的具体内容 [你打开浏览器看到的]
│
storage/
├── postgres/init/init_db.sql  ← 数据库建表语句（容器首次启动自动执行）
├── redis/data/                ← Redis 持久化文件
└── minio/data/                ← MinIO 存储的文件
```

### 按重要性排序的关键文件

| 优先级 | 文件 | 理由 |
|--------|------|------|
| 1 | `frontend/src/views/DetectionPage.vue` | 核心模块，看前端逻辑怎么写的 |
| 2 | `backend/app/services/detection_service.py` | 核心模块，看 YOLO 推理怎么写的 |
| 3 | `backend/app/api/detection.py` | 所有检测路由，看请求怎么接的 |
| 4 | `frontend/src/api/detection.js` | 所有前端 API 调用，看请求怎么发的 |
| 5 | `backend/main.py` | 启动入口，看路由怎么挂的 |
| 6 | `frontend/src/router/index.js` | 看页面怎么对应的 |
| 7 | `backend/app/config.py` | 看配置怎么加载的 |
| 8 | `backend/.env` | 改端口/密码/模型路径只改这个 |

### bin/debug 文件夹

`frontend/dist/` — `npm run build` 的输出，不用看  
`frontend/node_modules/` — npm install 装的依赖，不用看  
`backend/.venv/` — Python 虚拟环境，不用看  
`backend/static/uploads/` — 上传的临时文件  
`backend/static/results/` — 标注图和标注视频输出  
`storage/*/data/` — Docker 容器挂载的数据目录

---

## GPU 推理
后端自动检测 CUDA。已在 RTX 4050 上测试，推理速度 ~24ms/帧。
无 GPU 时自动退到 CPU。用 `uv pip` 装 GPU 版 PyTorch：
```bash
uv pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 目录结构

```
visdrone-detection/
├── CLAUDE.md                    ← 本文档（项目速查手册）

├── docker-compose.yml           # PostgreSQL + Redis + MinIO 三件套
├── storage/
│   ├── postgres/init/init_db.sql  # 首次启动自动建表（users, detection_records, detection_results, target_categories）
│   ├── redis/data/                # Redis 持久化
│   └── minio/data/                # MinIO 文件镜像（实际存这，通过 HTTP 访问）

├── backend/
│   ├── main.py                  # FastAPI 入口，CORS，路由挂载，DB 初始化
│   ├── .env                     # 环境变量（所有配置优先从这读）
│   ├── requirements.txt
│   ├── yolo11m_visdrone.pt      # VisDrone 微调模型 (39MB, 10类)
│   ├── yolo11n.pt               # COCO Nano (5.4MB, 80类, 监控演示用)
│   ├── static/
│   │   ├── uploads/             # 上传的原图暂存
│   │   └── results/             # 标注图 + 标注视频输出
│   └── app/
│       ├── config.py            # Pydantic Settings（DB/Redis/MinIO/YOLO 参数）
│       ├── database.py          # SQLAlchemy engine + SessionLocal
│       ├── redis_client.py      # Redis 连接 + 缓存 + 限流
│       ├── models/
│       │   ├── schemas.py       # Pydantic 请求/响应模型
│       │   └── db_models.py     # SQLAlchemy ORM 模型（对应 init_db.sql）
│       ├── api/
│       │   ├── detection.py     # 单图/批量/视频/下载/历史/详情/删除 + WebSocket 监控
│       │   └── auth.py          # 注册/登录/忘记密码/个人中心/统计
│       ├── services/
│       │   ├── detection_service.py  # YOLO 双模型加载 + 单图/批量/视频检测逻辑
│       │   ├── auth_service.py       # bcrypt 密码哈希 + JWT 签发/校验
│       │   └── storage_service.py    # MinIO 上传/删除/直链（备选方案）
│       └── utils/
│           ├── file_utils.py    # 文件保存、URL 生成
│           └── security.py      # JWT + bcrypt 实现

└── frontend/
    ├── vite.config.js           # Vite 配置 + /api 代理到 localhost:8000
    ├── src/
    │   ├── main.js              # Vue 入口，全局注册 ElementPlus 图标
    │   ├── App.vue              # 根组件（auth 页直接渲染，其他走 MainLayout）
    │   ├── style.css            # 全局主题（暗色侧边栏 + 交通绿 + 拥堵三色）
    │   ├── router/index.js      # 路由定义（7 个页面）
    │   ├── utils/request.js     # Axios 封装（baseURL /api, JWT 拦截器）
    │   ├── api/detection.js     # 全部 API 函数
    │   ├── layouts/MainLayout.vue   # 暗色侧边栏 + 顶栏 + 内容区
    │   ├── components/
    │   │   ├── Sidebar.vue      # 导航：单图/批量/视频/监控/历史/目标库/个人中心
    │   │   ├── Header.vue       # 动态面包屑 + 用户下拉
    │   │   └── SliderCompare.vue
    │   └── views/
    │       ├── LoginPage.vue        # 登录
    │       ├── RegisterPage.vue     # 注册
    │       ├── ForgotPasswordPage.vue # 忘记密码
    │       ├── DetectionPage.vue    # 模块一：单图分析
    │       ├── BatchPage.vue        # 模块二：批量归档 + ECharts饼图
    │       ├── VideoPage.vue        # 模块三：视频分析 + ECharts折线图
    │       ├── MonitorPage.vue      # 模块四：实时监控 (WebSocket)
    │       ├── HistoryPage.vue      # 模块五：历史台账 + 详情弹窗
    │       ├── TargetsPage.vue      # 目标分类库
    │       └── ProfilePage.vue      # 个人中心 + 统计
```

---

## 五个模块核心数据流

### 模块一：单图分析
```
用户拖拽图片 → processFile() 读尺寸
  → POST /api/detection/single (FormData: file + model_name)
  → detection_service.detect_single_image()
     → YOLO.predict() GPU推理
     → 框坐标 + 类别 → DetectionBox[]
     → results[0].plot() → 标注图 (BGR→RGB→PIL保存)
     → 标注图上传 MinIO (旁路, 失败不影响)
     → _save_record() → detection_records + detection_results 写 PostgreSQL
  → 返回 DetectionResult → 前端渲染
     → 拥堵评级: 车距聚类算法 (pairwise width归一化, ≥45%缓行 ≥75%拥堵)
     → 车辆分布特征: 聚类率进度条 + 聚类数 + 平均车距
     → 车辆类型分布: 水平条形图 (8类)
     → 车辆规模构成: 小/中/大型 (bbox面积三段)
     → 目标明细: 聚合表格
```
关键文件: `backend/app/services/detection_service.py` (94-150行), `frontend/src/views/DetectionPage.vue`

### 模块二：批量归档
```
多图选择 → POST /api/detection/batch (FormData: files[] + model_name)
  → 逐张调 detect_single_image()
  → 汇总 category_distribution + peak_image (目标最多的那张)
  → 返回 BatchDetectionData → 前端
     → ECharts 环形饼图 (各类别占比 + 百分比标签)
     → 峰值拥堵卡片 (缩略图 + 车辆数 + 评级)
     → 结果网格 (每张图缩略图)
     → 打包下载 → GET /api/detection/download → ZIP StreamingResponse
```
关键文件: `backend/app/api/detection.py` (113-125行), `frontend/src/views/BatchPage.vue`

### 模块三：视频分析
```
上传 MP4 → POST /api/detection/video (FormData: file + model_name + frame_interval)
  → save_upload_file() 保存原视频
  → detect_video(): OpenCV逐帧读 → 每N帧YOLO推理 → imageio写H.264标注视频
  → 标注视频上传 MinIO
  → 返回 frame_data[] (每帧 timestamp + boxes + category_counts)
  → 前端播放标注视频 + ECharts 动态折线图 (时间×目标数 + 各类别堆叠面积图)
  → 播放进度同步: 当前帧目标数 + 帧级类别明细
```
关键文件: `backend/app/services/detection_service.py` (210-310行), `frontend/src/views/VideoPage.vue`

### 模块四：实时监控 (WebSocket)
```
点击"启动监控" → getUserMedia() 开摄像头
  → new WebSocket(ws://localhost:5173/api/detection/ws/monitor?model_name=coco)
  → 每120ms: canvas.toBlob(JPEG) → ws.send(bytes)
     → 后端: cv2.imdecode → YOLO.predict → ws.send_json({boxes, total, alert})
  → 前端: Canvas画框(requestAnimationFrame) + 实时计数 + 告警日志
  → 关闭时: WebSocketDisconnect → 存一条 monitor 记录到 DB
```
关键文件: `backend/app/api/detection.py` (338-380行), `frontend/src/views/MonitorPage.vue`

### 模块五：系统管理
- **登录**: `POST /auth/login` → bcrypt验证 → JWT (2h) → Redis缓存token → 前端存localStorage
- **注册**: `POST /auth/register` → users表INSERT
- **忘记密码**: `POST /auth/reset-password` → 用户名+新密码直接改
- **历史台账**: `GET /detection/history` → detection_records表分页查询 + `GET /detection/detail/{id}`弹窗
- **个人中心**: `GET /auth/me` + `GET /auth/stats` → 用户信息+检测统计
- **目标库**: `GET /detection/targets/list` → VisDrone 10类 (Redis缓存24h)
- **默认账号**: admin / admin123 (启动时自动创建)

---

## API 速查

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 → JWT |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/reset-password` | 重置密码 |
| GET | `/api/auth/me` | 当前用户信息 |
| GET | `/api/auth/stats` | 用户检测统计 |
| POST | `/api/detection/single` | 单图检测 |
| POST | `/api/detection/batch` | 批量检测 |
| POST | `/api/detection/video` | 视频分析 |
| WS | `/api/detection/ws/monitor?model_name=coco` | 实时监控 |
| GET | `/api/detection/history` | 历史记录 (分页) |
| GET | `/api/detection/detail/{id}` | 检测详情 |
| DELETE | `/api/detection/delete/{id}` | 删除记录 |
| GET | `/api/detection/download` | 下载结果ZIP |
| GET | `/api/detection/targets/list` | 目标类别列表 |

---

## 数据库表

```
users: id(UUID), username, email, password_hash, role, ...
detection_records: id(UUID), user_id→users, type(single|batch|video|monitor),
                   model_name, total_objects, detection_time,
                   original_image_key, result_image_key, created_at
detection_results: id, record_id→detection_records CASCADE,
                   x1,y1,x2,y2, confidence, class_id, class_name
target_categories: name, chinese_name, description, color
```

---

## 双模型架构

`DetectionService.__init__()` 启动时加载两个 YOLO 模型：

| 模型 | 文件 | 大小 | 类别 | 用途 |
|------|------|------|------|------|
| visdrone-v1 | yolo11m_visdrone.pt | 39MB | 10 | 无人机航拍（默认） |
| coco | yolo11n.pt | 5.4MB | 80 | 摄像头近景演示 |

`get_model(name)` → 返回 `(model, class_names)`。WebSocket 监控默认用 COCO（`?model_name=coco`），其他用 VisDrone。

---

## 当前项目状态

### 已完成 ✅
- 四大检测模块前后端全通（单图/批量/视频/实时监控）
- GPU 推理（CUDA），自动检测设备
- 用户认证（注册/登录/JWT/忘记密码）
- 历史台账（数据库真实数据 + 分页筛选 + 详情弹窗 + 删除）
- 个人中心（真实统计：总检测次数/目标数/成功率/使用天数）
- 结果打包下载（ZIP）
- PostgreSQL 表自动创建 + admin 用户 seed
- 拥堵评级（车距聚类算法，pairwise 归一化，透视不敏感）
- 交通态势可视化（密度分布/类型分布/规模构成/智能诊断）
- ECharts 图表（批量饼图 + 视频折线图）
- MinIO 后备存储（标注图 + 标注视频上传）
- Redis 缓存（登录限流 + Token + 目标列表）

### 可继续完善
- 批量/视频/监控的 result_key 存入 DB（当前只有单图存了，详情弹窗批量/视频显示"无图"）
- MinIO 真正替代 static/（而非双写）
- 视频帧级结果可回放（目前只存了标注视频，没存帧级 boxes 到 DB）
- 用户权限细化（目前只有 admin/user 角色，检测 API 不强制鉴权）
- 前端打包下载传真正的 DB record IDs 而非空参数


数据库设计文档
项目需求文档
演示视频
答辩ppt