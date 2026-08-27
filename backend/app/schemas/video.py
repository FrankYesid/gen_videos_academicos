from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VideoProvider:
    MOCK = "mock"
    HEYGEN_VIDEO_AGENT = "heygen_agent"
    HEYGEN_TEMPLATE = "heygen_template"


class VideoCreate(BaseModel):
    lesson_id: uuid.UUID
    provider: str = Field(..., max_length=50)
    script_version: str | None = Field(default=None, max_length=50)


class VideoUpdate(BaseModel):
    provider_video_id: str | None = None
    job_id: str | None = None
    status: str | None = None
    video_url: str | None = Field(default=None, max_length=1024)
    thumbnail_url: str | None = Field(default=None, max_length=1024)
    duration: int | None = None
    request_payload: dict | None = None
    webhook_response: dict | None = None
    error_message: str | None = None
    completed_at: datetime | None = None


class VideoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    provider: str
    provider_video_id: str | None = None
    job_id: str | None = None
    status: str
    video_url: str | None = None
    thumbnail_url: str | None = None
    duration: int | None = None
    created_at: datetime
    completed_at: datetime | None = None


class VideoStatusResponse(BaseModel):
    provider_video_id: str
    status: str
    progress: int = Field(default=0, ge=0, le=100)
    message: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    duration: int | None = None


class GenerateVideoResponse(BaseModel):
    course_id: uuid.UUID
    status: str
    job_id: uuid.UUID


class CourseStatusResponse(BaseModel):
    course_id: uuid.UUID
    status: str
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str | None = None
    video: dict | None = None
    qa: dict | None = None


class QAStatus(BaseModel):
    status: Literal["approved", "rejected"]
    score: int = Field(..., ge=0, le=100)
    issues: list[dict] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
