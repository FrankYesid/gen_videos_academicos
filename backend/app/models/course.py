from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utcnow


class CourseStatus:
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    ANALYZING = "ANALYZING"
    PEDAGOGICAL_DESIGN = "PEDAGOGICAL_DESIGN"
    SCRIPT_GENERATED = "SCRIPT_GENERATED"
    SCRIPT_VALIDATED = "SCRIPT_VALIDATED"
    VIDEO_GENERATING = "VIDEO_GENERATING"
    VIDEO_PROCESSING = "VIDEO_PROCESSING"
    VIDEO_READY = "VIDEO_READY"
    QA = "QA"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    @classmethod
    def all(cls) -> list[str]:
        return [
            cls.CREATED,
            cls.UPLOADED,
            cls.EXTRACTING,
            cls.ANALYZING,
            cls.PEDAGOGICAL_DESIGN,
            cls.SCRIPT_GENERATED,
            cls.SCRIPT_VALIDATED,
            cls.VIDEO_GENERATING,
            cls.VIDEO_PROCESSING,
            cls.VIDEO_READY,
            cls.QA,
            cls.COMPLETED,
            cls.FAILED,
        ]

    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        if from_status == to_status and from_status != cls.COMPLETED:
            return True
        transitions = {
            cls.CREATED: {
                cls.UPLOADED,
                cls.EXTRACTING,
                cls.ANALYZING,
                cls.PEDAGOGICAL_DESIGN,
                cls.SCRIPT_GENERATED,
                cls.SCRIPT_VALIDATED,
                cls.VIDEO_GENERATING,
                cls.VIDEO_PROCESSING,
                cls.VIDEO_READY,
                cls.QA,
                cls.FAILED,
            },
            cls.UPLOADED: {
                cls.EXTRACTING, cls.ANALYZING, cls.PEDAGOGICAL_DESIGN,
                cls.SCRIPT_GENERATED, cls.SCRIPT_VALIDATED, cls.VIDEO_GENERATING,
                cls.VIDEO_PROCESSING, cls.VIDEO_READY, cls.QA, cls.FAILED,
            },
            cls.EXTRACTING: {
                cls.ANALYZING, cls.PEDAGOGICAL_DESIGN, cls.SCRIPT_GENERATED,
                cls.SCRIPT_VALIDATED, cls.VIDEO_GENERATING, cls.VIDEO_PROCESSING,
                cls.VIDEO_READY, cls.QA, cls.FAILED,
            },
            cls.ANALYZING: {
                cls.PEDAGOGICAL_DESIGN, cls.SCRIPT_GENERATED,
                cls.SCRIPT_VALIDATED, cls.VIDEO_GENERATING,
                cls.VIDEO_PROCESSING, cls.VIDEO_READY, cls.QA, cls.FAILED,
            },
            cls.PEDAGOGICAL_DESIGN: {
                cls.SCRIPT_GENERATED, cls.SCRIPT_VALIDATED,
                cls.VIDEO_GENERATING, cls.VIDEO_PROCESSING, cls.VIDEO_READY,
                cls.QA, cls.ANALYZING, cls.FAILED,
            },
            cls.SCRIPT_GENERATED: {
                cls.SCRIPT_VALIDATED, cls.VIDEO_GENERATING,
                cls.VIDEO_PROCESSING, cls.VIDEO_READY, cls.QA,
                cls.PEDAGOGICAL_DESIGN, cls.ANALYZING, cls.FAILED,
            },
            cls.SCRIPT_VALIDATED: {
                cls.VIDEO_GENERATING, cls.VIDEO_PROCESSING,
                cls.VIDEO_READY, cls.QA, cls.SCRIPT_GENERATED,
                cls.PEDAGOGICAL_DESIGN, cls.ANALYZING, cls.FAILED,
            },
            cls.VIDEO_GENERATING: {
                cls.VIDEO_PROCESSING, cls.VIDEO_READY, cls.QA,
                cls.SCRIPT_VALIDATED, cls.SCRIPT_GENERATED,
                cls.PEDAGOGICAL_DESIGN, cls.ANALYZING, cls.FAILED,
            },
            cls.VIDEO_PROCESSING: {
                cls.VIDEO_READY, cls.QA, cls.VIDEO_GENERATING,
                cls.SCRIPT_VALIDATED, cls.SCRIPT_GENERATED,
                cls.PEDAGOGICAL_DESIGN, cls.ANALYZING, cls.FAILED,
            },
            cls.VIDEO_READY: {
                cls.QA, cls.COMPLETED, cls.VIDEO_PROCESSING,
                cls.VIDEO_GENERATING, cls.SCRIPT_VALIDATED,
                cls.SCRIPT_GENERATED, cls.PEDAGOGICAL_DESIGN,
                cls.ANALYZING, cls.FAILED,
            },
            cls.QA: {
                cls.COMPLETED, cls.VIDEO_READY, cls.VIDEO_PROCESSING,
                cls.VIDEO_GENERATING, cls.SCRIPT_VALIDATED,
                cls.SCRIPT_GENERATED, cls.PEDAGOGICAL_DESIGN,
                cls.ANALYZING, cls.UPLOADED, cls.EXTRACTING, cls.FAILED,
            },
            cls.COMPLETED: {
                cls.QA, cls.VIDEO_READY, cls.VIDEO_PROCESSING,
                cls.VIDEO_GENERATING, cls.SCRIPT_VALIDATED,
                cls.SCRIPT_GENERATED, cls.PEDAGOGICAL_DESIGN,
                cls.ANALYZING, cls.FAILED,
            },
            cls.FAILED: set(),
        }
        allowed = transitions.get(from_status)
        if allowed is None:
            return False
        return to_status in allowed


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="es")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=CourseStatus.CREATED, index=True
    )
    script_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qa_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qa_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_topics: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    prerequisites: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    concepts: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    pedagogical_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    script_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    qa_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    document: Mapped["Document | None"] = relationship("Document", back_populates="courses")
    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson", back_populates="course", cascade="all, delete-orphan"
    )
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun", back_populates="course", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course id={self.id} title={self.title!r} status={self.status}>"
