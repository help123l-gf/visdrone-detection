import json
import os
from collections import Counter

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.detection_service import detection_service
from app.services.history_service import create_record, query_records, get_record_detail, delete_record
from app.services.storage_service import storage_service
from app.utils.file_utils import save_upload_file, ensure_directories
from app.config import settings
from app.models.schemas import (
    SingleDetectionResponse,
    BatchDetectionResponse,
    BatchDetectionData,
    VideoDetectionResponse,
    VideoDetectionData,
    HistoryResponse,
    HistoryItem,
    TargetListResponse,
    TargetItem,
    DetectionDetailResponse,
    DeleteRecordResponse,
    UserStatsResponse,
)
from app.api.deps import get_current_user
from app.models.db_models import User
from typing import List
from datetime import datetime

router = APIRouter(prefix="/detection", tags=["detection"])

ensure_directories()


@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),
    model_name: str = Form("visdrone-v1"),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    try:
        filename = await save_upload_file(file, settings.UPLOAD_DIR)
        image_path = os.path.join(settings.UPLOAD_DIR, filename)

        result = detection_service.detect_single_image(image_path, model_name)

        # 上传到 MinIO（如果启用）
        result_key = None
        if storage_service.enabled:
            result_path = os.path.join(settings.RESULT_DIR, os.path.basename(result.result_image_url.lstrip("/static/results/")))
            result_key = storage_service.upload_file(result_path)

        # 计算拥堵评级
        congestion = _calc_congestion(result.total_objects)

        # 类别统计
        cat_summary = {}
        for b in result.boxes:
            cat_summary[b.class_name] = cat_summary.get(b.class_name, 0) + 1

        # 写入历史记录
        create_record(
            db=db,
            user_id=user.id if user else None,
            detection_type="single",
            model_name=model_name,
            filename=os.path.basename(image_path),
            total_objects=result.total_objects,
            max_objects=result.total_objects,
            detection_time_sec=result.detection_time,
            congestion_level=congestion,
            result_image_key=result_key,
            category_summary=cat_summary,
            boxes=[b.model_dump() for b in result.boxes],
        )

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
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    try:
        paths = []
        filenames = []
        for file in files:
            filename = await save_upload_file(file, settings.UPLOAD_DIR)
            paths.append(os.path.join(settings.UPLOAD_DIR, filename))
            filenames.append(filename)

        data = detection_service.detect_batch_images(paths, model_name)

        # 类别统计汇总
        cat_summary = {}
        for d in data["category_distribution"]:
            cat_summary[d.class_name] = d.count

        peak_count = data["peak_image"].total_objects if data["peak_image"] else 0
        congestion = _calc_congestion(peak_count)

        # 写入历史记录
        create_record(
            db=db,
            user_id=user.id if user else None,
            detection_type="batch",
            model_name=model_name,
            filename=", ".join(filenames[:3]) + ("..." if len(filenames) > 3 else ""),
            total_objects=data["total_objects"],
            max_objects=peak_count,
            detection_time_sec=data["total_time"],
            congestion_level=congestion,
            category_summary=cat_summary,
            extra_data={"total_images": data["total_images"]},
        )

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
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    try:
        filename = await save_upload_file(file, settings.UPLOAD_DIR)
        video_path = os.path.join(settings.UPLOAD_DIR, filename)

        data = detection_service.detect_video(video_path, model_name, frame_interval)

        # 上传标注视频到 MinIO
        if storage_service.enabled and data.get("annotated_video_url"):
            video_name = os.path.basename(data["annotated_video_url"].lstrip("/static/results/"))
            video_result_path = os.path.join(settings.RESULT_DIR, video_name)
            storage_service.upload_file(video_result_path)

        peak_count = data["peak_frame"].total_objects if data["peak_frame"] else 0
        congestion = _calc_congestion(peak_count)

        # 写入历史记录
        create_record(
            db=db,
            user_id=user.id if user else None,
            detection_type="video",
            model_name=model_name,
            filename=os.path.basename(video_path),
            total_objects=int(data["avg_objects_per_frame"] * data["processed_frames"]),
            max_objects=peak_count,
            detection_time_sec=data["duration_sec"],
            congestion_level=congestion,
            extra_data={
                "processed_frames": data["processed_frames"],
                "total_frames": data["total_frames"],
                "fps": data["fps"],
                "duration_sec": data["duration_sec"],
            },
        )

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
async def get_detection_history(
    keyword: str = Query(None),
    type: str = Query(None),
    congestion: str = Query(None),
    startDate: str = Query(None),
    endDate: str = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    records, total = query_records(
        db=db,
        user_id=user.id if user else None,
        keyword=keyword,
        detection_type=type,
        congestion=congestion,
        start_date=startDate,
        end_date=endDate,
        page=page,
        page_size=pageSize,
    )

    items = []
    for r in records:
        items.append(HistoryItem(
            id=r.id,
            type=r.type,
            filename=r.filename,
            model_name=r.model_name,
            total_objects=r.total_objects,
            max_objects=r.max_objects,
            detection_time_sec=r.detection_time_sec,
            congestion=r.congestion_level or "道路畅通",
            detection_time=r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            result_image_url=f"/static/results/{r.result_image_key}" if r.result_image_key else None,
        ))

    return HistoryResponse(
        success=True,
        message="获取成功",
        data=items,
        total=total,
    )


@router.get("/detail/{record_id}", response_model=DetectionDetailResponse)
async def get_detection_detail(
    record_id: str,
    db: Session = Depends(get_db),
):
    record = get_record_detail(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    boxes = []
    for r in record.results:
        boxes.append({
            "x1": r.x1, "y1": r.y1, "x2": r.x2, "y2": r.y2,
            "confidence": r.confidence, "class_id": r.class_id,
            "class_name": r.class_name, "chinese_name": r.chinese_name,
        })

    return DetectionDetailResponse(
        success=True,
        message="获取成功",
        data={
            "id": record.id,
            "type": record.type,
            "filename": record.filename,
            "model_name": record.model_name,
            "total_objects": record.total_objects,
            "max_objects": record.max_objects,
            "detection_time_sec": record.detection_time_sec,
            "congestion": record.congestion_level or "道路畅通",
            "detection_time": record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else "",
            "category_summary": json.loads(record.category_summary) if record.category_summary else {},
            "boxes": boxes,
            "result_image_url": f"/static/results/{record.result_image_key}" if record.result_image_key else None,
        },
    )


@router.delete("/history/{record_id}", response_model=DeleteRecordResponse)
async def delete_detection_record(
    record_id: str,
    db: Session = Depends(get_db),
):
    ok = delete_record(db, record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记录不存在")
    return DeleteRecordResponse(success=True, message="删除成功")


@router.get("/stats", response_model=UserStatsResponse)
async def get_detection_stats(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    if not user:
        return UserStatsResponse(
            success=True, message="获取成功",
            data={"total_detections": 0, "total_objects": 0, "success_rate": 0},
        )
    from app.services.history_service import get_user_stats
    stats = get_user_stats(db, user.id)
    return UserStatsResponse(success=True, message="获取成功", data=stats)


def _calc_congestion(total: int) -> str:
    if total > 20:
        return "严重拥堵"
    elif total >= 10:
        return "交通缓行"
    return "道路畅通"


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
