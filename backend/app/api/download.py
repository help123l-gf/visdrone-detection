"""文件下载 API 路由"""
import os
import zipfile
import io
import uuid

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.config import settings
from app.services.storage_service import storage_service

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/result/{filename}")
async def download_result_file(filename: str):
    """下载单个检测结果文件"""
    file_path = os.path.join(settings.RESULT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return StreamingResponse(
        open(file_path, "rb"),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/batch-results")
async def download_batch_results(filenames: str = Query(..., description="逗号分隔的文件名列表")):
    """打包下载多个检测结果（ZIP）"""
    file_list = [f.strip() for f in filenames.split(",") if f.strip()]

    if not file_list:
        raise HTTPException(status_code=400, detail="请提供要下载的文件名")

    # 创建内存中的 ZIP
    zip_buffer = io.BytesIO()
    added = 0
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in file_list:
            # 从结果目录查找
            result_path = os.path.join(settings.RESULT_DIR, fname)
            upload_path = os.path.join(settings.UPLOAD_DIR, fname)

            if os.path.exists(result_path):
                zf.write(result_path, fname)
                added += 1
            elif os.path.exists(upload_path):
                zf.write(upload_path, fname)
                added += 1

    if added == 0:
        raise HTTPException(status_code=404, detail="没有找到可下载的文件")

    zip_buffer.seek(0)
    zip_name = f"visdrone_results_{uuid.uuid4().hex[:8]}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


@router.get("/annotated-video/{filename}")
async def download_annotated_video(filename: str):
    """下载标注后的视频文件"""
    file_path = os.path.join(settings.RESULT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    return StreamingResponse(
        open(file_path, "rb"),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Accept-Ranges": "bytes",
        },
    )
