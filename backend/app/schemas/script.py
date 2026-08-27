from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


_STRICT_EXTRA = ConfigDict(
    extra="forbid",
    strict=True,
    json_schema_extra={"additionalProperties": False},
)


class Scene(BaseModel):
    """Individual scene in the video script."""

    model_config = _STRICT_EXTRA

    id: int = Field(..., ge=1, description="Sequential scene number")
    title: str = Field(..., min_length=1, max_length=500, description="Scene title")
    duration_seconds: int = Field(..., ge=5, le=600, description="Scene duration in seconds")
    narration: str = Field(..., min_length=1, description="Voiceover narration text")
    visual_instruction: str = Field(..., min_length=1, description="Visual elements and animations")
    on_screen_text: str = Field(..., max_length=280, description="Text to display on screen")
    educational_purpose: str = Field(..., min_length=1, max_length=255, description="Learning objective of this scene")
    camera_angle: str | None = Field(default=None, description="Suggested camera angle")
    background: str | None = Field(default=None, description="Background visual description")
    audio_cue: str | None = Field(default=None, description="Background music or sound effect")


class ScriptOutput(BaseModel):
    """Structured output from the Script Agent."""

    model_config = _STRICT_EXTRA

    title: str = Field(..., min_length=1, description="Script title")
    scenes: list[Scene] = Field(
        default_factory=list,
        min_length=2,
        description="Ordered list of video scenes"
    )
    total_duration_seconds: int = Field(..., ge=10, description="Total video duration")
    introduction: str = Field(..., min_length=1, description="Opening introduction text")
    conclusion: str = Field(..., min_length=1, description="Closing conclusion text")
    target_audience: str = Field(..., description="Intended audience")
    tone: str = Field(default="educational", description="Narrative tone")
    notes: str | None = Field(default=None, description="Additional production notes")


class Script(BaseModel):
    """Schema for API responses with script data."""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., min_length=1)
    scenes: list[Scene] = Field(default_factory=list, min_length=2)
    total_duration_seconds: int = Field(..., ge=10)
    introduction: str = Field(..., min_length=1)
    conclusion: str = Field(..., min_length=1)
    target_audience: str = Field(..., description="Intended audience")
    tone: str = Field(default="educational")
    notes: str | None = Field(default=None)
