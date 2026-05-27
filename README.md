# VisDrone Detection Platform 无人机交通态势感知系统

基于 YOLO11 无人机航拍视觉的智能交通态势感知系统。包含模型训练、单图分析、批量归档、视频分析、实时监控，输出拥堵评级、密度分析、历史台账。前后端分离，PostgreSQL + Redis + MinIO 为基础设施。

**默认账号：admin / admin123**

---

## 快速开始

```bash
# 1. 启动基础服务（需要 Docker Desktop）
docker-compose up -d

# 2. 启动后端
cd backend
pip install -r requirements.txt
python main.py                      # → http://localhost:8000

# 3. 启动前端
cd frontend
npm install
npm run dev                         # → http://localhost:5173
```

浏览器打开 `http://localhost:5173`。

### GPU 推理（可选）

```bash
cd backend
uv pip install torch --index-url https://download.pytorch.org/whl/cu121
```

后端自动检测 CUDA，无 GPU 时退回 CPU。RTX 4050 实测推理 ~24ms/帧。

---

## 模型训练

`backend/train/train.py` — YOLO11m 在 VisDrone 数据集上微调：

```python
from ultralytics import YOLO

model = YOLO("yolo11m.pt")        # 从 COCO 预训练权重开始
model.train(
    data="VisDrone.yaml",          # 数据集配置（需自行准备）
    epochs=150,                    # 训练轮数
    imgsz=1024,                    # 输入分辨率
    batch=32,                      # 批大小（根据显存调整）
    device="0",                    # GPU 设备
    workers=16,                    # 数据加载线程
    mosaic=0.3,                    # Mosaic 数据增强概率
    mixup=0.1,                     # MixUp 增强概率
    copy_paste=0.2,                # Copy-Paste 增强概率
    patience=30,                   # 早停耐心值
)
```

训练产出 `yolo11m_visdrone.pt`（39MB），部署到 `backend/` 目录即可被系统加载。

### VisDrone 10 类目标

pedestrian（行人）· people（人群）· bicycle（自行车）· car（汽车）· van（面包车）· truck（卡车）· tricycle（三轮车）· awning-tricycle（遮阳三轮车）· bus（公交车）· motor（摩托车）

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

上传无人机航拍图片，YOLO 检测 10 类目标，输出交通态势评估报告。

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

上传无人机航拍视频，逐帧检测并生成 H.264 标注视频。

- OpenCV 逐帧读取 + YOLO 推理 + imageio-ffmpeg 编码
- ECharts 动态折线图（时间 × 目标数）带各类别堆叠面积图
- 视频播放同步：当前帧目标数 + 帧级类别明细

### 模块四：实时监控

本地摄像头 + WebSocket 实时推流检测。

- 每 120ms `canvas.toBlob(JPEG)` → WebSocket 发送 → YOLO 推理 → 返回框坐标
- Canvas 画框（requestAnimationFrame），可调阈值告警，告警日志滚动
- 双模型切换：COCO（近景） / VisDrone（航拍）

### 模块五：系统管理

- **认证**：JWT + bcrypt，注册 / 登录 / 重置密码
- **历史台账**：分页表格，按类型 / 日期筛选，详情弹窗查看标注图 + 目标列表
- **目标分类库**：VisDrone 10 类目标卡片
- **个人中心**：真实检测统计（总次数 / 累计目标 / 成功率 / 使用天数）

---

## 拥堵评级算法

```
1. 成对车宽归一化  →  像素距离 ÷ 两车平均宽度  →  消除近大远小透视形变
2. BFS 聚类        →  间距 < 2.5 车宽视为同一聚类
3. PCA 线性过滤    →  协方差特征值比 > 4 → 线性排列 → 路边停车 → 排除
4. 交通聚类率      →  团状聚类车辆 ÷ 总车辆
5. 评级            →  ≥75% 拥堵  ·  ≥45% 缓行  ·  <45% 畅通
```

算法在 `backend/app/services/detection_service.py` 的 `compute_clustering()`，单图和批量共用。

---

## 项目结构

```
visdrone-detection/
├── docker-compose.yml
├── storage/
│   ├── postgres/init/init_db.sql
│   ├── redis/data/
│   └── minio/data/
│
├── backend/
│   ├── main.py                     # FastAPI 入口
│   ├── .env                        # 环境变量（DB/Redis/MinIO/YOLO 路径）
│   ├── yolo11m_visdrone.pt         # 训练产出：VisDrone 微调模型 (39MB, 10类)
│   ├── yolo11n.pt                  # COCO 预训练模型 (5.4MB, 80类, 监控演示用)
│   ├── train/
│   │   └── train.py                # YOLO11m 训练脚本
│   ├── static/
│   │   ├── uploads/                # 上传原图暂存
│   │   └── results/                # 标注图 + 标注视频
│   └── app/
│       ├── config.py
│       ├── database.py
│       ├── redis_client.py
│       ├── api/
│       │   ├── detection.py        # 单图/批量/视频/WebSocket/历史/下载/删除
│       │   └── auth.py             # 注册/登录/重置密码/个人中心/统计
│       ├── services/
│       │   ├── detection_service.py    # YOLO 双模型 + 聚类算法
│       │   ├── auth_service.py
│       │   └── storage_service.py      # MinIO 上传/删除
│       ├── models/
│       │   ├── schemas.py
│       │   └── db_models.py
│       └── utils/
│           ├── file_utils.py
│           └── security.py
│
└── frontend/
    ├── vite.config.js
    └── src/
        ├── main.js
        ├── router/index.js
        ├── style.css
        ├── utils/request.js
        ├── api/detection.js
        ├── layouts/MainLayout.vue
        ├── components/
        │   ├── Sidebar.vue
        │   ├── Header.vue
        │   └── SliderCompare.vue
        └── views/
            ├── LoginPage.vue / RegisterPage.vue / ForgotPasswordPage.vue
            ├── DetectionPage.vue    # 模块一：单图分析
            ├── BatchPage.vue        # 模块二：批量归档
            ├── VideoPage.vue        # 模块三：视频分析
            ├── MonitorPage.vue      # 模块四：实时监控
            ├── HistoryPage.vue      # 模块五：历史台账
            ├── TargetsPage.vue      # 目标分类库
            └── ProfilePage.vue      # 个人中心
```

---

## API 速查

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/reset-password` | 重置密码 |
| GET | `/api/auth/me` | 当前用户信息 |
| GET | `/api/auth/stats` | 用户检测统计 |
| POST | `/api/detection/single` | 单图检测 |
| POST | `/api/detection/batch` | 批量检测 |
| POST | `/api/detection/video` | 视频分析 |
| WS | `/api/detection/ws/monitor` | 实时监控 |
| GET | `/api/detection/history` | 历史记录（分页） |
| GET | `/api/detection/detail/{id}` | 检测详情 |
| DELETE | `/api/detection/delete/{id}` | 删除记录 |
| GET | `/api/detection/download` | 打包下载 ZIP |
| GET | `/api/detection/targets/list` | 目标类别列表 |

---

## 双模型

| 模型名 | 文件 | 大小 | 类别数 | 用途 |
|--------|------|------|--------|------|
| visdrone-v1 | yolo11m_visdrone.pt | 39MB | 10 | 无人机航拍 |
| coco | yolo11n.pt | 5.4MB | 80 | 摄像头近景演示 |

启动时同时加载到 GPU。`get_model(name)` 按名切换，WebSocket 监控默认 COCO，其余默认 VisDrone。

---

## 数据库

| 表 | 字段 |
|----|------|
| `users` | id, username, email, password_hash, role, created_at |
| `detection_records` | id, user_id, type, model_name, total_objects, detection_time, original_image_key, result_image_key, created_at |
| `detection_results` | id, record_id, x1, y1, x2, y2, confidence, class_id, class_name |
| `target_categories` | name, chinese_name, description, color |

```bash
docker exec -it visdrone-postgres psql -U visdrone_user -d visdrone_db
```

MinIO 控制台：`http://localhost:9001`（minioadmin / minioadmin）

---

## 数据流（开发参考）

```
用户操作 → views/XxxPage.vue
         → api/detection.js              ← 前端 API 层
         → request({ url: "/detection/xxx" })
         → app/api/detection.py          ← 后端路由
         → services/detection_service.py ← YOLO 推理
         → PostgreSQL / MinIO / Redis
```

- `app/api/` 只收请求、返回响应
- `app/services/` 放业务逻辑
- Vue 页面通过 `api/detection.js` 发请求，不直接 `import request`
- 全中文注释
