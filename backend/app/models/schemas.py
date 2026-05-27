from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DetectionBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str


class ClusteringData(BaseModel):
    ratio: float                # 交通聚类率 (0~1)
    cluster_count: int          # 总聚类数（含停车线）
    traffic_cluster_count: int  # 交通聚类数（剔除停车线后）
    avg_spacing: float          # 平均车距（车宽倍数）
    label: str                  # 中文标签：密集聚集 / 局部聚集 / 均匀分散
    level: str                  # dense / moderate / sparse


class CongestionInfo(BaseModel):
    level: str                  # clear / slow / congested
    label: str                  # 道路畅通 / 交通缓行 / 严重拥堵
    emoji: str                  # ✅ / ⚠️ / 🚨


class DetectionResult(BaseModel):
    detection_id: str
    image_url: str
    result_image_url: str
    boxes: List[DetectionBox]
    total_objects: int
    detection_time: float
    model_name: str
    created_at: datetime
    clustering: Optional[ClusteringData] = None
    congestion: Optional[CongestionInfo] = None


class SingleDetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[DetectionResult] = None


class HistoryItem(BaseModel):
    id: str
    image_url: str
    result_image_url: str
    total_objects: int
    created_at: datetime
    model_name: str


class HistoryResponse(BaseModel):
    success: bool
    message: str
    data: List[HistoryItem]
    total: int


class TargetItem(BaseModel):
    id: int
    name: str
    chinese_name: str
    description: Optional[str] = None


class TargetListResponse(BaseModel):
    success: bool
    message: str
    data: List[TargetItem]


class BatchImageResult(BaseModel):
    record_id: Optional[str] = None
    filename: str
    image_url: str
    result_image_url: str
    total_objects: int
    detection_time: float
    boxes: List[DetectionBox]


class CategoryDistribution(BaseModel):
    class_name: str
    chinese_name: str
    count: int


class PeakImage(BaseModel):
    filename: str
    total_objects: int
    congestion_level: str


class BatchDetectionData(BaseModel):
    batch_id: str
    total_images: int
    total_objects: int
    total_time: float
    category_distribution: List[CategoryDistribution]
    peak_image: Optional[PeakImage] = None
    results: List[BatchImageResult]


class BatchDetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[BatchDetectionData] = None


class VideoBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    class_name: str


class VideoFrameData(BaseModel):
    frame_index: int
    timestamp_sec: float
    total_objects: int
    category_counts: dict  # {class_name: count}
    boxes: List[VideoBox]


class VideoPeakFrame(BaseModel):
    frame_index: int
    timestamp_sec: float
    total_objects: int


class VideoDetectionData(BaseModel):
    video_id: str
    video_url: str
    total_frames: int
    processed_frames: int
    duration_sec: float
    fps: float
    annotated_video_url: Optional[str] = None
    frame_data: List[VideoFrameData]
    peak_frame: Optional[VideoPeakFrame] = None
    avg_objects_per_frame: float


class VideoDetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[VideoDetectionData] = None
