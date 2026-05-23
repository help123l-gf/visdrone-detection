"""SQLAlchemy ORM 数据库模型"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=new_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=True)
    role = Column(String(20), default="user")
    avatar_url = Column(String(500), nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    records = relationship("DetectionRecord", back_populates="user", cascade="all, delete-orphan")


class DetectionRecord(Base):
    __tablename__ = "detection_records"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(String(20), nullable=False, comment="single/batch/video/monitor")
    status = Column(String(20), default="completed")
    model_name = Column(String(50), nullable=False)
    model_version = Column(String(20), default="1.0.0")
    filename = Column(String(500), nullable=True)
    total_objects = Column(Integer, default=0)
    max_objects = Column(Integer, default=0)
    detection_time_sec = Column(Float, default=0.0)
    congestion_level = Column(String(20), nullable=True)
    original_image_key = Column(String(500), nullable=True)
    result_image_key = Column(String(500), nullable=True)
    annotated_video_key = Column(String(500), nullable=True)
    category_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    extra_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="records")
    results = relationship("DetectionResultItem", back_populates="record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_records_user_type", "user_id", "type"),
        Index("idx_records_created_desc", created_at.desc()),
    )


class DetectionResultItem(Base):
    __tablename__ = "detection_results"

    id = Column(String, primary_key=True, default=new_uuid)
    record_id = Column(String, ForeignKey("detection_records.id", ondelete="CASCADE"), nullable=False, index=True)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(50), nullable=False)
    chinese_name = Column(String(50), nullable=True)

    record = relationship("DetectionRecord", back_populates="results")


class TargetCategory(Base):
    __tablename__ = "target_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    chinese_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    color = Column(String(20), default="#10b981")
    enabled = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
