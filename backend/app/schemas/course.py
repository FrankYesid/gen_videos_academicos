from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CourseStatus = Literal[
    "CREATED",
    "UPLOADED",
    "EXTRACTING",
    "ANALYZING",
    "PEDAGOGICAL_DESIGN",
    "SCRIPT_GENERATED",
    "SCRIPT_VALIDATED",
    "VIDEO_GENERATING",
    "VIDEO_PROCESSING",
    "VIDEO_READY",
    "QA",
    "COMPLETED",
    "FAILED",
]

CourseLevel = Literal["beginner", "intermediate", "advanced"]


class CourseBase(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None)
    subject: str | None = Field(default=None, max_length=255)
    level: CourseLevel | None = None
    language: str = Field(default="es", max_length=10)
    estimated_duration_minutes: int | None = Field(default=None, ge=1, le=180)


class CourseCreate(CourseBase):
    document_id: uuid.UUID | None = None


class CourseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    subject: str | None = None
    level: CourseLevel | None = None
    language: str | None = Field(default=None, max_length=10)
    status: CourseStatus | str | None = None
    script_approved: bool | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    current_step: str | None = Field(default=None, max_length=255)
    estimated_duration_minutes: int | None = None
    qa_score: int | None = Field(default=None, ge=0, le=100)
    qa_status: str | None = None
    error_message: str | None = None
    main_topics: list[str] | None = None
    prerequisites: list[str] | None = None
    concepts: list[dict] | None = None
    keywords: list[str] | None = None
    pedagogical_data: dict | None = None
    script_data: dict | None = None
    qa_data: dict | None = None


class CourseRead(CourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID | None = None
    status: str
    script_approved: bool = False
    progress: int = 0
    current_step: str | None = None
    qa_score: int | None = None
    qa_status: str | None = None
    error_message: str | None = None
    main_topics: list[str] | None = None
    prerequisites: list[str] | None = None
    concepts: list[dict] | None = None
    keywords: list[str] | None = None
    pedagogical_data: dict | None = None
    script_data: dict | None = None
    qa_data: dict | None = None
    created_at: datetime
    updated_at: datetime


class CourseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None = None
    subject: str | None = None
    level: str | None = None
    language: str
    status: str
    progress: int
    script_approved: bool = False
    created_at: datetime
    updated_at: datetime
