import os
import time
from collections import Counter

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import text, desc
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.services.detection_service import detection_service
from app.utils.file_utils import save_upload_file, ensure_directories
from app.config import settings
from app.models.schemas import (
    SingleDetectionResponse,
    BatchDetectionResponse, BatchDetectionData,
    VideoDetectionResponse, VideoDetectionData,
    TargetListResponse, TargetItem,
)
from typing import List

router = APIRouter(prefix="/detection", tags=["detection"])


def _save_record(
    detect_type: str, model_name: str, total_objects: int,
    detection_time: float, boxes: list, orig_key: str = "", result_key: str = "",
    user_id: str = None,
):
    try:
        _save_record_inner(detect_type, model_name, total_objects, detection_time, boxes, orig_key, result_key, user_id)
    except Exception as e:
        print(f"DB save skipped ({detect_type}): {e}")


def _save_record_inner(detect_type, model_name, total_objects, detection_time, boxes, orig_key, result_key, user_id):
    if user_id is None:
        user_id = _guest_user_id()
    if not user_id:
        return
    db = SessionLocal()
    try:
        rid = detection_service._new_uuid()
        cols = "id, user_id, type, model_name, total_objects, detection_time, original_image_key, result_image_key, status"
        db.execute(
            text(f"INSERT INTO detection_records ({cols}) VALUES (:id,:uid,:t,:mn,:to,:dt,:ok,:rk,:s)"),
            {"id": rid, "uid": user_id, "t": detect_type, "mn": model_name, "to": total_objects,
             "dt": round(detection_time, 3), "ok": orig_key, "rk": result_key, "s": "completed"},
        )
        for b in boxes:
            db.execute(
                text("INSERT INTO detection_results (record_id, x1, y1, x2, y2, confidence, class_id, class_name) VALUES (:rid,:x1,:y1,:x2,:y2,:c,:ci,:cn)"),
                {"rid": rid,
                 "x1": b["x1"] if isinstance(b, dict) else b.x1,
                 "y1": b["y1"] if isinstance(b, dict) else b.y1,
                 "x2": b["x2"] if isinstance(b, dict) else b.x2,
                 "y2": b["y2"] if isinstance(b, dict) else b.y2,
                 "c": b["confidence"] if isinstance(b, dict) else b.confidence,
                 "ci": b["class_id"] if isinstance(b, dict) else b.class_id,
                 "cn": b["class_name"] if isinstance(b, dict) else b.class_name},
            )
        db.commit()
    finally:
        db.close()


_guest_id = None


def _guest_user_id():
    global _guest_id
    if _guest_id:
        return _guest_id
    try:
        db = SessionLocal()
        try:
            row = db.execute(text("SELECT id FROM users WHERE username='admin'")).fetchone()
            _guest_id = row[0] if row else None
        finally:
            db.close()
    except Exception:
        _guest_id = None
    return _guest_id


def _boxes_to_rows(boxes):
    rows = []
    for b in boxes:
        if hasattr(b, "x1"):
            rows.append({"x1": b.x1, "y1": b.y1, "x2": b.x2, "y2": b.y2, "confidence": b.confidence, "class_id": b.class_id, "class_name": b.class_name})
        else:
            rows.append({"x1": b["x1"], "y1": b["y1"], "x2": b["x2"], "y2": b["y2"], "confidence": b.get("confidence", 0), "class_id": b.get("class_id", 0), "class_name": b.get("class_name", "unknown")})
    return rows


# ── Single detection ──
@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(file: UploadFile = File(...), model_name: str = Form("visdrone-v1")):
    try:
        filename = await save_upload_file(file, settings.UPLOAD_DIR)
        image_path = os.path.join(settings.UPLOAD_DIR, filename)
        result = detection_service.detect_single_image(image_path, model_name)
        _save_record("single", model_name, result.total_objects, result.detection_time,
                      _boxes_to_rows(result.boxes), orig_key=filename, result_key=os.path.basename(result.result_image_url))
        return SingleDetectionResponse(success=True, message="检测成功", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


# ── Batch detection ──
@router.post("/batch", response_model=BatchDetectionResponse)
async def detect_batch_images(files: list[UploadFile] = File(...), model_name: str = Form("visdrone-v1")):
    try:
        paths = []
        for file in files:
            fname = await save_upload_file(file, settings.UPLOAD_DIR)
            paths.append(os.path.join(settings.UPLOAD_DIR, fname))
        data = detection_service.detect_batch_images(paths, model_name)
        _save_record("batch", model_name, data["total_objects"], data["total_time"], [])
        return BatchDetectionResponse(success=True, message=f"批量检测完成", data=BatchDetectionData(**data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量检测失败: {str(e)}")


# ── Video detection ──
@router.post("/video", response_model=VideoDetectionResponse)
async def detect_video(file: UploadFile = File(...), model_name: str = Form("visdrone-v1"), frame_interval: int = Form(5)):
    try:
        fname = await save_upload_file(file, settings.UPLOAD_DIR)
        vpath = os.path.join(settings.UPLOAD_DIR, fname)
        data = detection_service.detect_video(vpath, model_name, frame_interval)
        total = sum(f.total_objects for f in data["frame_data"]) if data.get("frame_data") else 0
        _save_record("video", model_name, total, data["duration_sec"], [])
        return VideoDetectionResponse(success=True, message=f"视频分析完成", data=VideoDetectionData(**data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频分析失败: {str(e)}")


# ── Targets ──
@router.get("/targets/list", response_model=TargetListResponse)
async def get_target_list():
    from app.redis_client import cache_get, cache_set
    import json as _json
    cached = cache_get("targets")
    if cached:
        return _json.loads(cached)

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
    resp = TargetListResponse(success=True, message="获取成功", data=targets)
    from app.redis_client import cache_set
    import json as _json
    cache_set("targets", _json.dumps(resp.model_dump()), 86400)
    return resp


# ── Download ZIP ──
@router.get("/download")
async def download_results(record_ids: str = "", db: Session = Depends(get_db)):
    import io, zipfile
    records = []
    if record_ids:
        ids = [rid.strip() for rid in record_ids.split(",") if rid.strip()]
        for rid in ids:
            row = db.execute(
                text("SELECT result_image_key, original_image_key FROM detection_records WHERE id=:id"),
                {"id": rid},
            ).fetchone()
            if row:
                records.append({"result": row[0] or "", "original": row[1] or ""})
    else:
        rows = db.execute(
            text("SELECT result_image_key, original_image_key FROM detection_records ORDER BY created_at DESC LIMIT 50")
        ).fetchall()
        for row in rows:
            records.append({"result": row[0] or "", "original": row[1] or ""})

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        seen = set()
        for i, rec in enumerate(records):
            for key_type, key in [("result", rec["result"]), ("original", rec["original"])]:
                if not key or key in seen:
                    continue
                seen.add(key)
                fpath = os.path.join(settings.RESULT_DIR if key_type == "result" else settings.UPLOAD_DIR, key)
                if os.path.exists(fpath):
                    zf.write(fpath, f"{i+1:03d}_{key_type}_{os.path.basename(key)}")
    buf.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=detection_results.zip"})


# ── History ──
@router.get("/history")
async def get_history(
    keyword: str = "", type: str = "", page: int = 1, page_size: int = 10,
    start_date: str = "", end_date: str = "", db: Session = Depends(get_db),
):
    from app.config import is_db_available
    if not is_db_available():
        return {"success": True, "data": [], "total": 0, "message": "数据库不可用"}

    conditions = ["1=1"]
    params = {}
    if keyword:
        conditions.append("(original_image_key ILIKE :kw)")
        params["kw"] = f"%{keyword}%"
    if type:
        conditions.append("type = :tp")
        params["tp"] = type
    if start_date:
        conditions.append("created_at >= :sd")
        params["sd"] = start_date
    if end_date:
        conditions.append("created_at <= :ed")
        params["ed"] = end_date + " 23:59:59"

    where = " AND ".join(conditions)
    count = db.execute(text(f"SELECT COUNT(*) FROM detection_records WHERE {where}"), params).fetchone()[0]

    rows = db.execute(
        text(f"SELECT id, type, model_name, total_objects, detection_time, original_image_key, result_image_key, status, created_at FROM detection_records WHERE {where} ORDER BY created_at DESC LIMIT :lim OFFSET :off"),
        {**params, "lim": page_size, "off": (page - 1) * page_size},
    ).fetchall()

    items = [{
        "id": r[0], "type": r[1], "model_name": r[2], "max_objects": r[3],
        "detection_time_sec": round(r[4], 2) if r[4] else 0,
        "filename": r[5] or "", "result_url": r[6] or "",
        "status": r[7], "detection_time": str(r[8]),
        "congestion": _congestion_label(r[3]),
    } for r in rows]

    return {"success": True, "message": "获取成功", "data": items, "total": count}


def _congestion_label(total: int) -> str:
    if total >= 30: return "严重拥堵"
    if total >= 15: return "交通缓行"
    if total > 0: return "道路畅通"
    return "无目标"


# ── Detail ──
@router.get("/detail/{record_id}")
async def get_detail(record_id: str, db: Session = Depends(get_db)):
    cols = "id, user_id, type, status, model_name, model_version, total_objects, detection_time, original_image_key, result_image_key, error_message, created_at, updated_at"
    rec = db.execute(text(f"SELECT {cols} FROM detection_records WHERE id=:id"), {"id": record_id}).fetchone()
    if not rec:
        raise HTTPException(404, "记录不存在")
    boxes = db.execute(text("SELECT id, record_id, x1, y1, x2, y2, confidence, class_id, class_name FROM detection_results WHERE record_id=:rid"), {"rid": record_id}).fetchall()
    return {
        "success": True,
        "data": {
            "id": rec[0], "type": rec[2], "model_name": rec[4],
            "total_objects": rec[6], "detection_time": rec[7],
            "result_url": rec[9], "created_at": str(rec[11]),
            "boxes": [{"x1": b[2], "y1": b[3], "x2": b[4], "y2": b[5],
                       "confidence": b[6], "class_id": b[7], "class_name": b[8]} for b in boxes],
        },
    }


# ── Delete ──
@router.delete("/delete/{record_id}")
async def delete_record(record_id: str, db: Session = Depends(get_db)):
    from app.config import is_db_available
    if not is_db_available():
        raise HTTPException(503, "数据库不可用")
    rec = db.execute(text("SELECT result_image_key FROM detection_records WHERE id=:id"), {"id": record_id}).fetchone()
    if not rec:
        raise HTTPException(404, "记录不存在")
    if rec[0]:
        try:
            from app.services.storage_service import delete_file
            delete_file(f"results/{rec[0]}")
        except Exception:
            pass
    db.execute(text("DELETE FROM detection_results WHERE record_id=:rid"), {"rid": record_id})
    db.execute(text("DELETE FROM detection_records WHERE id=:id"), {"id": record_id})
    db.commit()
    return {"success": True, "message": "删除成功"}


# ── WebSocket Monitor ──
ALERT_THRESHOLD = 15


@router.websocket("/ws/monitor")
async def monitor_websocket(websocket: WebSocket, model_name: str = "coco"):
    await websocket.accept()
    service = detection_service
    model, class_names = service.get_model(model_name)

    frame_count = 0
    total_obj_sum = 0
    max_obj = 0
    start_time = time.time()

    try:
        while True:
            data = await websocket.receive_bytes()
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
            h, w = frame.shape[:2]
            if w > 640:
                scale = 640 / w
                frame = cv2.resize(frame, (640, int(h * scale)))

            results = model.predict(source=frame, conf=settings.CONFIDENCE_THRESHOLD,
                                    iou=settings.IOU_THRESHOLD, device=service.device,
                                    save=False, verbose=False)

            boxes = []
            cat_counts = Counter()
            for r in results:
                for b in r.boxes:
                    cls_name = class_names.get(int(b.cls[0]), "unknown")
                    cat_counts[cls_name] += 1
                    boxes.append({"x1": float(b.xyxy[0][0]), "y1": float(b.xyxy[0][1]),
                                  "x2": float(b.xyxy[0][2]), "y2": float(b.xyxy[0][3]),
                                  "confidence": float(b.conf[0]), "class_name": cls_name})
            total = sum(cat_counts.values())

            frame_count += 1
            total_obj_sum += total
            if total > max_obj:
                max_obj = total

            await websocket.send_json({
                "success": True, "boxes": boxes, "total_objects": total,
                "alert": total >= ALERT_THRESHOLD,
                "category_counts": dict(cat_counts),
                "frame_w": frame.shape[1], "frame_h": frame.shape[0],
            })
    except WebSocketDisconnect:
        pass
    finally:
        elapsed = time.time() - start_time
        if frame_count > 0:
            _save_record("monitor", model_name, max_obj, elapsed, [])
