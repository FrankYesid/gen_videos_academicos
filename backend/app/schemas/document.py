from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentBase(BaseModel):
    filename: str = Field(..., description="Original file name", max_length=255)
    mime_type: str = Field(..., description="MIME type (application/pdf)", max_length=100)
    file_size: int = Field(..., description="Size in bytes", ge=0)
    language: str | None = Field(default=None, max_length=10)


class DocumentCreate(DocumentBase):
    file_path: str = Field(..., description="Absolute path on disk", max_length=1024)
    file_hash: str = Field(..., description="SHA-256 hash", min_length=64, max_length=64)


class DocumentUpdate(BaseModel):
    page_count: int | None = Field(default=None, ge=0)
    extracted_text: str | None = Field(default=None)
    status: str | None = Field(default=None, max_length=50)
    error_message: str | None = Field(default=None)


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_hash: str
    page_count: int | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("file_hash")
    @classmethod
    def mask_hash(cls, v: str) -> str:
        if len(v) < 16:
            return v
        return v[:8] + "…" + v[-8:]


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    mime_type: str
    file_size: int
    page_count: int | None = None
    status: str
    created_at: datetime
