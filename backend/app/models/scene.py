from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utcnow


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    narration: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    on_screen_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    educational_purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="scenes")
