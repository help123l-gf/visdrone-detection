"""检测历史记录服务"""
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.db_models import DetectionRecord, DetectionResultItem, User
from app.services.cache_service import cache_service


def create_record(
    db: Session,
    user_id: str | None,
    detection_type: str,
    model_name: str,
    filename: str | None = None,
    total_objects: int = 0,
    max_objects: int = 0,
    detection_time_sec: float = 0.0,
    congestion_level: str | None = None,
    original_image_key: str | None = None,
    result_image_key: str | None = None,
    annotated_video_key: str | None = None,
    category_summary: dict | None = None,
    extra_data: dict | None = None,
    boxes: list | None = None,
) -> DetectionRecord:
    """创建检测记录，可附带检测框详情"""
    record = DetectionRecord(
        user_id=user_id,
        type=detection_type,
        status="completed",
        model_name=model_name,
        filename=filename,
        total_objects=total_objects,
        max_objects=max_objects,
        detection_time_sec=round(detection_time_sec, 3),
        congestion_level=congestion_level,
        original_image_key=original_image_key,
        result_image_key=result_image_key,
        annotated_video_key=annotated_video_key,
        category_summary=json.dumps(category_summary, ensure_ascii=False) if category_summary else None,
        extra_data=json.dumps(extra_data, ensure_ascii=False) if extra_data else None,
    )
    db.add(record)
    db.flush()  # 获取 record.id

    # 保存检测框详情
    if boxes:
        for b in boxes:
            db.add(DetectionResultItem(
                record_id=record.id,
                x1=b.get("x1", 0),
                y1=b.get("y1", 0),
                x2=b.get("x2", 0),
                y2=b.get("y2", 0),
                confidence=b.get("confidence", 0),
                class_id=b.get("class_id", 0),
                class_name=b.get("class_name", "unknown"),
                chinese_name=b.get("chinese_name", None),
            ))

    db.commit()
    db.refresh(record)

    # 清除历史缓存
    cache_service.delete("history:list:*")

    return record


def query_records(
    db: Session,
    user_id: str | None = None,
    keyword: str | None = None,
    detection_type: str | None = None,
    congestion: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[DetectionRecord], int]:
    """分页查询检测记录"""
    q = db.query(DetectionRecord)

    if user_id:
        q = q.filter(DetectionRecord.user_id == user_id)
    if detection_type:
        q = q.filter(DetectionRecord.type == detection_type)
    if keyword:
        q = q.filter(DetectionRecord.filename.ilike(f"%{keyword}%"))
    if congestion:
        if congestion == "high":
            q = q.filter(DetectionRecord.congestion_level == "严重拥堵")
        elif congestion == "medium":
            q = q.filter(DetectionRecord.congestion_level == "交通缓行")
        elif congestion == "low":
            q = q.filter(DetectionRecord.congestion_level == "道路畅通")
    if start_date:
        try:
            dt = datetime.fromisoformat(start_date)
            q = q.filter(DetectionRecord.created_at >= dt)
        except ValueError:
            pass
    if end_date:
        try:
            dt = datetime.fromisoformat(end_date)
            q = q.filter(DetectionRecord.created_at <= dt)
        except ValueError:
            pass

    total = q.count()
    records = (
        q.order_by(desc(DetectionRecord.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return records, total


def get_record_detail(db: Session, record_id: str) -> DetectionRecord | None:
    """获取单条检测记录详情（含检测框）"""
    return (
        db.query(DetectionRecord)
        .options(joinedload(DetectionRecord.results))
        .filter(DetectionRecord.id == record_id)
        .first()
    )


def delete_record(db: Session, record_id: str) -> bool:
    """删除检测记录"""
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    cache_service.delete("history:list:*")
    return True


def get_user_stats(db: Session, user_id: str) -> dict:
    """获取用户检测统计"""
    total_detections = (
        db.query(func.count(DetectionRecord.id))
        .filter(DetectionRecord.user_id == user_id)
        .scalar() or 0
    )
    total_objects = (
        db.query(func.sum(DetectionRecord.total_objects))
        .filter(DetectionRecord.user_id == user_id)
        .scalar() or 0
    )
    success_count = (
        db.query(func.count(DetectionRecord.id))
        .filter(DetectionRecord.user_id == user_id, DetectionRecord.status == "completed")
        .scalar() or 0
    )
    success_rate = round(success_count / total_detections * 100, 1) if total_detections > 0 else 0

    return {
        "total_detections": total_detections,
        "total_objects": int(total_objects),
        "success_rate": success_rate,
    }
