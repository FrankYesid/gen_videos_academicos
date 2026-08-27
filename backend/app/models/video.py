from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import UUID, BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utcnow


class VideoStatus:
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_video_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=VideoStatus.CREATED, index=True
    )
    video_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    duration: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    request_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    webhook_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="videos")
