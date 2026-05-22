import os
import time
import uuid
from datetime import datetime

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

    def _name_to_id(self, name: str) -> int:
        for k, v in self.class_names.items():
            if v == name:
                return k
        return -1


detection_service = DetectionService()
