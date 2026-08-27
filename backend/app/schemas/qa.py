from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


_STRICT_EXTRA = ConfigDict(
    extra="forbid",
    strict=True,
    json_schema_extra={"additionalProperties": False},
)


class QAIssue(BaseModel):
    """Individual quality issue identified during QA review."""

    model_config = _STRICT_EXTRA

    category: str = Field(
        ...,
        min_length=1,
        description="Issue category: narration accuracy, visuals appropriateness, duration pacing, engagement level, pedagogical alignment, clarity, accessibility, completeness",
    )
    severity: Literal["low", "medium", "high"] = Field(
        ...,
        description="Severity level of the issue",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed description of the issue",
    )
    suggestion: str | None = Field(
        default=None,
        description="Optional suggestion for resolving the issue",
    )
    scene_id: int | None = Field(
        default=None,
        description="Optional scene ID where the issue occurs",
    )


class QAOutput(BaseModel):
    """Structured output from the QA Agent."""

    model_config = _STRICT_EXTRA

    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall quality score from 0 to 100",
    )
    status: Literal["approved", "rejected"] = Field(
        ...,
        description="QA_MIN_SCORE default 80 - approved if score >= QA_MIN_SCORE, rejected otherwise",
    )
    issues: list[QAIssue] = Field(
        default_factory=list,
        description="List of identified quality issues",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="List of general recommendations for improvement",
    )
    summary: str | None = Field(
        default=None,
        description="Executive summary of the QA review",
    )
    approved_at: str | None = Field(
        default=None,
        description="Timestamp when the review was approved",
    )
    qa_version: str = Field(
        default="1.0",
        description="QA review schema version",
    )


class QAResult(BaseModel):
    """Schema for API responses with QA review results."""

    model_config = ConfigDict(extra="ignore")

    score: int
    status: str
    issues: list[QAIssue] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    summary: str | None = None
