import os
import time
import uuid
from collections import Counter
from datetime import datetime

import cv2
import imageio
import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO

from app.config import settings
from app.models.schemas import DetectionBox, DetectionResult
from app.utils.file_utils import get_file_url


class DetectionService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models = {}
        self.class_names = {}
        self._load_all_models()

    def _load_all_models(self):
        """Load VisDrone model (main) + COCO nano model (webcam demo)."""
        # VisDrone (main)
        if os.path.exists(settings.YOLO_MODEL_PATH):
            m = YOLO(settings.YOLO_MODEL_PATH)
            m.to(self.device)
            self.models["visdrone-v1"] = m
            self.models["visdrone-v2"] = m  # alias for future
        else:
            raise FileNotFoundError(f"VisDrone model not found: {settings.YOLO_MODEL_PATH}")

        # COCO nano (webcam/general demo)
        coco_path = settings.COCO_MODEL_PATH
        if os.path.exists(coco_path):
            m = YOLO(coco_path)
            m.to(self.device)
            self.models["coco"] = m
        else:
            print(f"Warning: COCO model not found at {coco_path}, skipping")

        self.class_names = {
            "visdrone-v1": {
                0: "pedestrian", 1: "people", 2: "bicycle", 3: "car", 4: "van",
                5: "truck", 6: "tricycle", 7: "awning-tricycle", 8: "bus", 9: "motor",
            },
            "visdrone-v2": {
                0: "pedestrian", 1: "people", 2: "bicycle", 3: "car", 4: "van",
                5: "truck", 6: "tricycle", 7: "awning-tricycle", 8: "bus", 9: "motor",
            },
            "coco": {
                0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
                5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
                10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench",
                14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep", 19: "cow",
                20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe", 24: "backpack",
                25: "umbrella", 26: "handbag", 27: "tie", 28: "suitcase", 29: "frisbee",
                30: "skis", 31: "snowboard", 32: "sports ball", 33: "kite",
                34: "baseball bat", 35: "baseball glove", 36: "skateboard",
                37: "surfboard", 38: "tennis racket", 39: "bottle", 40: "wine glass",
                41: "cup", 42: "fork", 43: "knife", 44: "spoon", 45: "bowl",
                46: "banana", 47: "apple", 48: "sandwich", 49: "orange",
                50: "broccoli", 51: "carrot", 52: "hot dog", 53: "pizza", 54: "donut",
                55: "cake", 56: "chair", 57: "couch", 58: "potted plant", 59: "bed",
                60: "dining table", 61: "toilet", 62: "tv", 63: "laptop", 64: "mouse",
                65: "remote", 66: "keyboard", 67: "cell phone", 68: "microwave",
                69: "oven", 70: "toaster", 71: "sink", 72: "refrigerator", 73: "book",
                74: "clock", 75: "vase", 76: "scissors", 77: "teddy bear",
                78: "hair drier", 79: "toothbrush",
            },
        }

    def get_model(self, model_name: str):
        if model_name in self.models:
            return self.models[model_name], self.class_names.get(model_name, {})
        return self.models["visdrone-v1"], self.class_names["visdrone-v1"]

    def detect_single_image(self, image_path: str, model_name: str = "visdrone-v1") -> DetectionResult:
        start_time = time.time()
        detection_id = str(uuid.uuid4())

        model, class_names = self.get_model(model_name)

        results = model.predict(
            source=image_path,
            conf=settings.CONFIDENCE_THRESHOLD,
            iou=settings.IOU_THRESHOLD,
            device=self.device,
            save=False
        )

        boxes = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = class_names.get(class_id, f"class_{class_id}")

                boxes.append(DetectionBox(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name
                ))

        result_filename = f"result_{uuid.uuid4().hex}.jpg"
        result_path = os.path.join(settings.RESULT_DIR, result_filename)

        annotated_image = results[0].plot()
        annotated_rgb = annotated_image[..., ::-1]
        Image.fromarray(annotated_rgb).save(result_path)

        # Upload to MinIO (alongside local storage)
        result_url = get_file_url(result_filename, "static/results")
        try:
            from app.services.storage_service import upload_file as minio_upload
            result_url = minio_upload(result_path, f"results/{result_filename}")
        except Exception:
            pass

        detection_time = time.time() - start_time
        image_filename = os.path.basename(image_path)

        # 计算聚类与拥堵评级
        clustering_data, congestion_data = self.compute_clustering(boxes)

        return DetectionResult(
            detection_id=detection_id,
            image_url=get_file_url(image_filename, "static/uploads"),
            result_image_url=result_url,
            boxes=boxes,
            total_objects=len(boxes),
            detection_time=round(detection_time, 3),
            model_name=model_name,
            created_at=datetime.now(),
            clustering=clustering_data,
            congestion=congestion_data,
        )


    def detect_batch_images(self, image_paths: list, model_name: str = "visdrone-v1"):
        from app.models.schemas import BatchImageResult, CategoryDistribution, PeakImage

        batch_start = time.time()
        batch_id = str(uuid.uuid4())
        results = []
        category_counts = {}
        peak = None
        peak_count = 0

        for i, path in enumerate(image_paths):
            r = self.detect_single_image(path, model_name) # 复用单图函数
            filename = os.path.basename(path)
            results.append(BatchImageResult(
                filename=filename,
                image_url=get_file_url(filename, "static/uploads"),
                result_image_url=r.result_image_url,
                total_objects=r.total_objects,
                detection_time=r.detection_time,
                boxes=r.boxes,
            ))

            for b in r.boxes:
                category_counts[b.class_name] = category_counts.get(b.class_name, 0) + 1

            if r.total_objects > peak_count:
                peak_count = r.total_objects
                level = r.congestion.label if r.congestion else "道路畅通"
                peak = PeakImage(filename=filename, total_objects=peak_count, congestion_level=level)

        total_objects = sum(category_counts.values())
        _, class_names = self.get_model(model_name)
        distribution = [
            CategoryDistribution(
                class_name=name,
                chinese_name=class_names.get(self._name_to_id(name, class_names), name),
                count=count,
            )
            for name, count in sorted(category_counts.items(), key=lambda x: -x[1])
        ]

        return {
            "batch_id": batch_id,
            "total_images": len(results),
            "total_objects": total_objects,
            "total_time": round(time.time() - batch_start, 3),
            "category_distribution": distribution,
            "peak_image": peak,
            "results": results,
        }

    def detect_video(self, video_path: str, model_name: str = "visdrone-v1", frame_interval: int = 5):
        from app.models.schemas import VideoFrameData, VideoPeakFrame, VideoBox

        model, class_names = self.get_model(model_name)
        video_id = str(uuid.uuid4())
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Prepare imageio video writer (H.264, browser-compatible)
        video_filename = f"video_{video_id[:8]}.mp4"
        video_path_out = os.path.join(settings.RESULT_DIR, video_filename)
        out_fps = fps / max(frame_interval, 1)
        writer = imageio.get_writer(
            video_path_out, format="FFMPEG", mode="I",
            fps=out_fps, codec="libx264", pixelformat="yuv420p",
            quality=8, macro_block_size=1,
        )

        frame_data = []
        peak = None
        peak_count = 0
        frame_idx = 0
        processed = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval != 0:
                frame_idx += 1
                continue

            processed += 1
            timestamp = frame_idx / fps

            # YOLO inference
            results = model.predict(
                source=frame, conf=settings.CONFIDENCE_THRESHOLD,
                iou=settings.IOU_THRESHOLD, device=self.device,
                save=False, verbose=False,
            )

            boxes_list = []
            cat_counts = Counter()
            for r in results:
                for b in r.boxes:
                    cls_name = class_names.get(int(b.cls[0]), "unknown")
                    cat_counts[cls_name] += 1
                    boxes_list.append(VideoBox(
                        x1=float(b.xyxy[0][0]), y1=float(b.xyxy[0][1]),
                        x2=float(b.xyxy[0][2]), y2=float(b.xyxy[0][3]),
                        class_name=cls_name,
                    ))

            total = sum(cat_counts.values())
            frame_data.append(VideoFrameData(
                frame_index=frame_idx,
                timestamp_sec=round(timestamp, 2),
                total_objects=total,
                category_counts=dict(cat_counts),
                boxes=boxes_list,
            ))

            if total > peak_count:
                peak_count = total
                peak = VideoPeakFrame(
                    frame_index=frame_idx,
                    timestamp_sec=round(timestamp, 2),
                    total_objects=total,
                )

            # Generate annotated frame and write to video
            annotated = results[0].plot() if len(results) > 0 and results[0].boxes is not None else frame
            annotated_rgb = annotated[..., ::-1]  # BGR -> RGB for imageio
            writer.append_data(annotated_rgb)

            frame_idx += 1

        cap.release()
        writer.close()

        avg_objects = sum(f.total_objects for f in frame_data) / processed if processed > 0 else 0
        duration = total_frames / fps

        annotated_url = get_file_url(video_filename, "static/results") if processed > 0 else None
        # Also upload annotated video to MinIO
        if processed > 0:
            try:
                from app.services.storage_service import upload_file as minio_upload
                annotated_url = minio_upload(video_path_out, f"videos/{video_filename}", "video/mp4")
            except Exception:
                pass

        return {
            "video_id": video_id,
            "video_url": get_file_url(os.path.basename(video_path), "static/uploads"),
            "total_frames": total_frames,
            "processed_frames": processed,
            "duration_sec": round(duration, 1),
            "fps": round(fps, 1),
            "annotated_video_url": annotated_url,
            "frame_data": frame_data,
            "peak_frame": peak,
            "avg_objects_per_frame": round(avg_objects, 1),
        }

    @staticmethod
    def compute_clustering(boxes, image_w: int = 0, image_h: int = 0):
        """车距聚类 + 线性排列过滤 → 拥堵评级（从 DetectionPage.vue 迁移到后端）"""
        from app.models.schemas import ClusteringData, CongestionInfo

        n = len(boxes)
        if n < 2:
            return (
                ClusteringData(ratio=0, cluster_count=0, traffic_cluster_count=0, avg_spacing=0, label="无数据", level=""),
                CongestionInfo(level="", label="就绪", emoji="—"),
            )

        # 提取坐标和宽度
        def _val(b, attr):
            return b[attr] if isinstance(b, dict) else getattr(b, attr)
        widths = [max(_val(b, "x2") - _val(b, "x1"), 1) for b in boxes]
        cx = [(_val(b, "x1") + _val(b, "x2")) / 2 for b in boxes]
        cy = [(_val(b, "y1") + _val(b, "y2")) / 2 for b in boxes]

        # 1. 最近邻车距（成对车宽归一化）
        nn_dists = []
        for i in range(n):
            min_d = float("inf")
            for j in range(n):
                if i == j: continue
                d = ((cx[i] - cx[j]) ** 2 + (cy[i] - cy[j]) ** 2) ** 0.5
                ref = (widths[i] + widths[j]) / 2
                norm = d / ref
                if norm < min_d:
                    min_d = norm
            nn_dists.append(min_d)

        # 2. BFS 建聚类（阈值 2.5 车宽）
        CLUSTER_THRESHOLD = 2.5
        visited = [False] * n
        clusters = []

        for i in range(n):
            if visited[i]: continue
            queue = [i]
            visited[i] = True
            members = []
            while queue:
                cur = queue.pop(0)
                members.append(cur)
                for j in range(n):
                    if visited[j]: continue
                    pd = ((cx[cur] - cx[j]) ** 2 + (cy[cur] - cy[j]) ** 2) ** 0.5
                    ref = (widths[cur] + widths[j]) / 2
                    if pd / ref < CLUSTER_THRESHOLD:
                        visited[j] = True
                        queue.append(j)
            if len(members) >= 3:
                clusters.append(members)

        # 3. PCA 过滤线性聚类（λ1/λ2 > 4 → 疑似停车线）
        traffic_clusters = []
        for members in clusters:
            if len(members) < 5:
                traffic_clusters.append(members)
                continue

            xs = [cx[k] for k in members]
            ys = [cy[k] for k in members]
            mx = sum(xs) / len(xs)
            my = sum(ys) / len(ys)

            cov_xx = sum((x - mx) ** 2 for x in xs) / len(xs)
            cov_yy = sum((y - my) ** 2 for y in ys) / len(ys)
            cov_xy = sum((xs[k] - mx) * (ys[k] - my) for k in range(len(xs))) / len(xs)

            trace = cov_xx + cov_yy
            det = cov_xx * cov_yy - cov_xy * cov_xy
            disc = (max(trace * trace - 4 * det, 0)) ** 0.5
            lam1 = (trace + disc) / 2
            lam2 = (trace - disc) / 2
            elongation = lam1 / lam2 if lam2 > 1e-6 else 999

            if elongation > 4:
                continue  # 线性 → 路边停车
            traffic_clusters.append(members)

        # 4. 计算交通聚类率
        traffic_vehicles = sum(len(m) for m in traffic_clusters)
        ratio = traffic_vehicles / n
        avg_spacing = sum(nn_dists) / len(nn_dists)

        if ratio >= 0.75:
            cl = ClusteringData(ratio=ratio, cluster_count=len(clusters), traffic_cluster_count=len(traffic_clusters), avg_spacing=round(avg_spacing, 1), label="密集聚集", level="dense")
            cg = CongestionInfo(level="congested", label="严重拥堵", emoji="🚨")
        elif ratio >= 0.45:
            cl = ClusteringData(ratio=ratio, cluster_count=len(clusters), traffic_cluster_count=len(traffic_clusters), avg_spacing=round(avg_spacing, 1), label="局部聚集", level="moderate")
            cg = CongestionInfo(level="slow", label="交通缓行", emoji="⚠️")
        elif n > 0:
            cl = ClusteringData(ratio=ratio, cluster_count=len(clusters), traffic_cluster_count=len(traffic_clusters), avg_spacing=round(avg_spacing, 1), label="均匀分散", level="sparse")
            cg = CongestionInfo(level="clear", label="道路畅通", emoji="✅")
        else:
            cl = ClusteringData(ratio=0, cluster_count=0, traffic_cluster_count=0, avg_spacing=0, label="无数据", level="")
            cg = CongestionInfo(level="", label="无车辆", emoji="🔘")

        return cl, cg

    @staticmethod
    def _new_uuid() -> str:
        return str(uuid.uuid4())

    def _name_to_id(self, name: str, class_names: dict = None) -> int:
        names = class_names or self.class_names.get("visdrone-v1", {})
        for k, v in names.items():
            if v == name:
                return k
        return -1


detection_service = DetectionService()
