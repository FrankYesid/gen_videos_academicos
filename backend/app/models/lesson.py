from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utcnow


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    general_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    specific_objectives: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lesson_structure: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    examples: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    common_mistakes: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_suggested: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="CREATED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    course: Mapped["Course"] = relationship("Course", back_populates="lessons")
    scenes: Mapped[list["Scene"]] = relationship(
        "Scene", back_populates="lesson", cascade="all, delete-orphan"
    )
    videos: Mapped[list["Video"]] = relationship(
        "Video", back_populates="lesson", cascade="all, delete-orphan"
    )
