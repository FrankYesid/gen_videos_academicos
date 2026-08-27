from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utcnow


class AgentRunStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AgentRunStatus.PENDING, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    course: Mapped["Course"] = relationship("Course", back_populates="agent_runs")
