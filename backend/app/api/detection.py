import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.detection_service import detection_service
from app.utils.file_utils import save_upload_file, ensure_directories
from app.config import settings
from app.models.schemas import (
    SingleDetectionResponse,
    BatchDetectionResponse,
    BatchDetectionData,
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
