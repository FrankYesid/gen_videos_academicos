from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Level = Literal["beginner", "intermediate", "advanced"]

_STRICT_EXTRA = ConfigDict(
    extra="forbid",
    json_schema_extra={"additionalProperties": False},
)


class Concept(BaseModel):
    model_config = _STRICT_EXTRA
    concept: str = Field(..., min_length=1, description="The main concept or term")
    description: str = Field(..., min_length=1, description="Detailed explanation of the concept")
    source_pages: list[int] = Field(default_factory=list, description="Page numbers where this concept appears")


class AnalysisOutput(BaseModel):
    """Structured output from the Analyzer Agent."""
    model_config = _STRICT_EXTRA

    title: str = Field(..., min_length=1, max_length=500, description="Course title")
    subject: str = Field(..., min_length=1, max_length=255, description="Academic subject area")
    level: Level = Field(..., description="Difficulty level")
    language: str = Field(..., min_length=1, max_length=10, description="Content language (e.g., 'es', 'en')")
    summary: str = Field(..., min_length=1, description="Brief summary of the content")
    main_topics: list[str] = Field(default_factory=list, description="Main topics covered")
    prerequisites: list[str] = Field(default_factory=list, description="Required prior knowledge")
    concepts: list[Concept] = Field(default_factory=list, description="Key concepts with details")
    keywords: list[str] = Field(default_factory=list, description="Important keywords for search/indexing")


class Analysis(BaseModel):
    """Analysis schema for API responses."""
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    title: str = Field(..., min_length=1, max_length=500)
    subject: str = Field(..., min_length=1, max_length=255)
    level: Level
    language: str = Field(..., min_length=1, max_length=10)
    summary: str = Field(..., min_length=1)
    main_topics: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    concepts: list[Concept] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class AnalysisCreate(BaseModel):
    """Schema for creating analysis requests."""
    model_config = ConfigDict(extra="ignore")

    document_id: str = Field(..., description="Document ID to analyze")
    force_regenerate: bool = Field(default=False, description="Force regeneration even if analysis exists")
