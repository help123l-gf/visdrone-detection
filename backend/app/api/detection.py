import json
import os
from collections import Counter

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect

from app.services.detection_service import detection_service
from app.utils.file_utils import save_upload_file, ensure_directories
from app.config import settings
from app.models.schemas import (
    SingleDetectionResponse,
    BatchDetectionResponse,
    BatchDetectionData,
    VideoDetectionResponse,
    VideoDetectionData,
    HistoryResponse,
    TargetListResponse,
    TargetItem,
    HistoryItem,
)
from typing import List
from datetime import datetime

router = APIRouter(prefix="/detection", tags=["detection"])

ensure_directories()


@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),
    model_name: str = Form("visdrone-v1")
):
    try:
        filename = await save_upload_file(file, settings.UPLOAD_DIR)
        image_path = os.path.join(settings.UPLOAD_DIR, filename)

        result = detection_service.detect_single_image(image_path, model_name)

        return SingleDetectionResponse(
            success=True,
            message="检测成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.post("/batch", response_model=BatchDetectionResponse)
async def detect_batch_images(
    files: list[UploadFile] = File(...),
    model_name: str = Form("visdrone-v1"),
):
    try:
        paths = []
        for file in files:
            filename = await save_upload_file(file, settings.UPLOAD_DIR)
            paths.append(os.path.join(settings.UPLOAD_DIR, filename))

        data = detection_service.detect_batch_images(paths, model_name)

        return BatchDetectionResponse(
            success=True,
            message=f"批量检测完成，{data['total_images']} 张图片，共 {data['total_objects']} 个目标",
            data=BatchDetectionData(**data),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量检测失败: {str(e)}")


@router.post("/video", response_model=VideoDetectionResponse)
async def detect_video(
    file: UploadFile = File(...),
    model_name: str = Form("visdrone-v1"),
    frame_interval: int = Form(5),
):
    try:
        filename = await save_upload_file(file, settings.UPLOAD_DIR)
        video_path = os.path.join(settings.UPLOAD_DIR, filename)

        data = detection_service.detect_video(video_path, model_name, frame_interval)

        return VideoDetectionResponse(
            success=True,
            message=f"视频分析完成，{data['processed_frames']} 帧，平均 {data['avg_objects_per_frame']} 个目标/帧",
            data=VideoDetectionData(**data),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频分析失败: {str(e)}")


@router.get("/targets/list", response_model=TargetListResponse)
async def get_target_list():
    targets = [
        TargetItem(id=0, name="pedestrian", chinese_name="行人", description="单个行人目标"),
        TargetItem(id=1, name="people", chinese_name="人群", description="密集人群目标"),
        TargetItem(id=2, name="bicycle", chinese_name="自行车", description="自行车、电动车骑行者"),
        TargetItem(id=3, name="car", chinese_name="汽车", description="小轿车、SUV等"),
        TargetItem(id=4, name="van", chinese_name="面包车", description="厢式货车、面包车"),
        TargetItem(id=5, name="truck", chinese_name="卡车", description="大型货运卡车"),
        TargetItem(id=6, name="tricycle", chinese_name="三轮车", description="人力或机动三轮车"),
        TargetItem(id=7, name="awning-tricycle", chinese_name="遮阳三轮车", description="带遮阳棚的三轮车"),
        TargetItem(id=8, name="bus", chinese_name="公交车", description="公共汽车、大巴"),
        TargetItem(id=9, name="motor", chinese_name="摩托车", description="摩托车、电动车"),
    ]
    return TargetListResponse(
        success=True,
        message="获取成功",
        data=targets
    )


@router.get("/history", response_model=HistoryResponse)
async def get_detection_history():
    return HistoryResponse(
        success=True,
        message="获取成功",
        data=[],
        total=0
    )


ALERT_THRESHOLD = 15

@router.websocket("/ws/monitor")
async def monitor_websocket(websocket: WebSocket, model_name: str = "coco"):
    await websocket.accept()
    service = detection_service
    model, class_names = service.get_model(model_name)

    try:
        while True:
            data = await websocket.receive_bytes()

            # Decode JPEG
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # Resize for speed (max 640px wide)
            h, w = frame.shape[:2]
            if w > 640:
                scale = 640 / w
                frame = cv2.resize(frame, (640, int(h * scale)))

            # YOLO inference
            results = model.predict(
                source=frame,
                conf=settings.CONFIDENCE_THRESHOLD,
                iou=settings.IOU_THRESHOLD,
                device=service.device,
                save=False,
                verbose=False,
            )

            boxes = []
            cat_counts = Counter()
            for r in results:
                for b in r.boxes:
                    cls_name = class_names.get(int(b.cls[0]), "unknown")
                    cat_counts[cls_name] += 1
                    boxes.append({
                        "x1": float(b.xyxy[0][0]),
                        "y1": float(b.xyxy[0][1]),
                        "x2": float(b.xyxy[0][2]),
                        "y2": float(b.xyxy[0][3]),
                        "confidence": float(b.conf[0]),
                        "class_name": cls_name,
                    })

            total = sum(cat_counts.values())

            await websocket.send_json({
                "success": True,
                "boxes": boxes,
                "total_objects": total,
                "alert": total >= ALERT_THRESHOLD,
                "category_counts": dict(cat_counts),
                "frame_w": frame.shape[1],
                "frame_h": frame.shape[0],
            })

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
