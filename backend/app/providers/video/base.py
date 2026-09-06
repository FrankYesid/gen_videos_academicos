from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class VideoGenerationResult:
    """Result of video generation."""
    success: bool
    video_url: str | None = None
    thumbnail_url: str | None = None
    duration: int | None = None
    error_message: str | None = None
    provider_video_id: str | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class VideoGenerationProvider(ABC):
    """Abstract base class for video generation providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "480p",
        aspect_ratio: str = "16:9",
        seed: int | None = None,
        **kwargs: Any,
    ) -> VideoGenerationResult:
        """Generate video from text prompt."""
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the video provider is properly configured."""
        raise NotImplementedError
