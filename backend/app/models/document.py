from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utcnow


class DocumentStatus:
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=DocumentStatus.CREATED, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    courses: Mapped[list["Course"]] = relationship(
        "Course", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} name={self.filename!r} status={self.status}>"
