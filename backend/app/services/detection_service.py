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
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.class_names = {}
        self._load_model()
        self._init_class_names()

    def _load_model(self):
        if os.path.exists(settings.YOLO_MODEL_PATH):
            self.model = YOLO(settings.YOLO_MODEL_PATH)
            self.model.to(self.device)
        else:
            raise FileNotFoundError(f"Model file not found: {settings.YOLO_MODEL_PATH}")

    def _init_class_names(self):
        self.class_names = {
            0: "pedestrian",
            1: "people",
            2: "bicycle",
            3: "car",
            4: "van",
            5: "truck",
            6: "tricycle",
            7: "awning-tricycle",
            8: "bus",
            9: "motor",
        }

    def detect_single_image(self, image_path: str, model_name: str = "visdrone-v1") -> DetectionResult:
        start_time = time.time()
        detection_id = str(uuid.uuid4())

        results = self.model.predict(
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
                class_name = self.class_names.get(class_id, f"class_{class_id}")

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

        annotated_image = results[0].plot()  # BGR format
        annotated_rgb = annotated_image[..., ::-1]  # BGR -> RGB for PIL
        Image.fromarray(annotated_rgb).save(result_path)

        detection_time = time.time() - start_time

        image_filename = os.path.basename(image_path)

        return DetectionResult(
            detection_id=detection_id,
            image_url=get_file_url(image_filename, "static/uploads"),
            result_image_url=get_file_url(result_filename, "static/results"),
            boxes=boxes,
            total_objects=len(boxes),
            detection_time=round(detection_time, 3),
            model_name=model_name,
            created_at=datetime.now()
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
            r = self.detect_single_image(path, model_name)
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
                level = "道路畅通"
                if peak_count > 20:
                    level = "严重拥堵"
                elif peak_count >= 10:
                    level = "交通缓行"
                peak = PeakImage(filename=filename, total_objects=peak_count, congestion_level=level)

        total_objects = sum(category_counts.values())
        distribution = [
            CategoryDistribution(
                class_name=name,
                chinese_name=self.class_names.get(self._name_to_id(name), name),
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
            results = self.model.predict(
                source=frame, conf=settings.CONFIDENCE_THRESHOLD,
                iou=settings.IOU_THRESHOLD, device=self.device,
                save=False, verbose=False,
            )

            boxes_list = []
            cat_counts = Counter()
            for r in results:
                for b in r.boxes:
                    cls_name = self.class_names.get(int(b.cls[0]), "unknown")
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

    def _name_to_id(self, name: str) -> int:
        for k, v in self.class_names.items():
            if v == name:
                return k
        return -1


detection_service = DetectionService()
