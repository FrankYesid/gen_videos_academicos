from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


_STRICT_EXTRA = ConfigDict(
    extra="forbid",
    strict=True,
    json_schema_extra={"additionalProperties": False},
)


class LessonStructureItem(BaseModel):
    """Individual module or section within the lesson structure."""

    model_config = _STRICT_EXTRA

    module: str = Field(..., description="Module or section name")
    topics: list[str] = Field(default_factory=list, description="Topics covered in this module")
    order: int = Field(..., ge=1, description="Sequential order in the lesson")
    purpose: str | None = Field(default=None, description="Educational purpose of this module")
    duration_minutes: int | None = Field(default=None, ge=1, description="Estimated duration for this module")


class Example(BaseModel):
    """Practical example to illustrate concepts."""

    model_config = _STRICT_EXTRA

    title: str = Field(..., min_length=1, description="Example title")
    description: str = Field(..., min_length=1, description="Detailed description of the example")
    explanation: str | None = Field(default=None, description="Step-by-step explanation")


class CommonMistake(BaseModel):
    """Common mistake students make and its correction."""

    model_config = _STRICT_EXTRA

    mistake: str = Field(..., min_length=1, description="The common mistake")
    correction: str = Field(..., min_length=1, description="How to correct or avoid the mistake")
    context: str | None = Field(default=None, description="When this mistake typically occurs")


class PedagogicalOutput(BaseModel):
    """Structured output from the Pedagogical Agent."""

    model_config = _STRICT_EXTRA

    general_objective: str = Field(..., min_length=1, description="Overall learning goal")
    specific_objectives: list[str] = Field(
        default_factory=list,
        min_length=1,
        description="Specific, measurable learning objectives"
    )
    prerequisites: list[str] = Field(default_factory=list, description="Required prior knowledge")
    lesson_structure: list[LessonStructureItem] = Field(
        default_factory=list,
        description="Structured breakdown of lesson modules"
    )
    examples: list[Example] = Field(default_factory=list, description="Practical examples")
    common_mistakes: list[CommonMistake] = Field(default_factory=list, description="Common student errors")
    summary: str = Field(..., min_length=1, description="Pedagogical approach summary")
    estimated_duration_minutes: int = Field(
        default=10,
        ge=1,
        le=180,
        description="Total estimated lesson duration"
    )
    activity_suggested: str | None = Field(default=None, description="Suggested learning activity")
    teaching_strategies: list[str] = Field(default_factory=list, description="Recommended teaching methods")
    assessment_methods: list[str] = Field(default_factory=list, description="Suggested assessment approaches")


class PedagogicalDesign(BaseModel):
    """Schema for API responses with pedagogical design."""

    model_config = ConfigDict(extra="ignore")

    general_objective: str = Field(..., min_length=1)
    specific_objectives: list[str] = Field(default_factory=list, min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    lesson_structure: list[LessonStructureItem] = Field(default_factory=list)
    examples: list[Example] = Field(default_factory=list)
    common_mistakes: list[CommonMistake] = Field(default_factory=list)
    summary: str = Field(..., min_length=1)
    estimated_duration_minutes: int = Field(default=10, ge=1, le=180)
    activity_suggested: str | None = None
    teaching_strategies: list[str] = Field(default_factory=list)
    assessment_methods: list[str] = Field(default_factory=list)
