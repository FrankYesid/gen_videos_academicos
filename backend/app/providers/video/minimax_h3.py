from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
from app.providers.video.base import (
    VideoGenerationProvider,
    VideoGenerationResult,
)

logger = get_logger(__name__)
settings = get_settings()

try:
    from huggingface_hub import InferenceClient
    _HAS_HUGGINGFACE = True
except ImportError:
    InferenceClient = None  # type: ignore[assignment]
    _HAS_HUGGINGFACE = False


class MiniMaxH3Provider(VideoGenerationProvider):
    """MiniMax H3 Turbo LoRA provider using Hugging Face InferenceClient with WaveSpeed."""

    def __init__(self) -> None:
        if not settings.HF_TOKEN:
            raise AIServiceError("HF_TOKEN is not configured")
        if not _HAS_HUGGINGFACE:
            raise AIServiceError(
                "huggingface_hub package is not installed. Install with: pip install huggingface_hub"
            )

        self.client = InferenceClient(
            provider=settings.HF_VIDEO_PROVIDER,
            token=settings.HF_TOKEN,
        )
        self.model = settings.HF_VIDEO_MODEL
        self.default_duration = 5
        self.default_resolution = "480p"
        self.default_aspect_ratio = "16:9"

    def _build_educational_prompt(
        self,
        topic: str,
        scene_description: str,
        visual_style: str = "Clean educational animation, modern classroom, professional academic style",
        camera: str = "Medium shot, slow camera movement",
        action: str = "Educational content presentation",
        audio: str = "Clear educational narration in Spanish, subtle classroom ambience, no background music",
    ) -> str:
        """Build a specialized prompt for educational video generation."""
        prompt = f"""Create a high-quality educational video scene.

Topic:
{topic}

Scene:
{scene_description}

Visual style:
{visual_style}

Camera:
{camera}

Action:
{action}

Audio:
{audio}
"""
        return prompt.strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_sync(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "480p",
        aspect_ratio: str = "16:9",
        seed: int | None = None,
        **kwargs: Any,
    ) -> VideoGenerationResult:
        """Synchronous version of generate for Celery tasks."""
        import asyncio
        return asyncio.run(self.generate(prompt, duration, resolution, aspect_ratio, seed, **kwargs))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "480p",
        aspect_ratio: str = "16:9",
        seed: int | None = None,
        **kwargs: Any,
    ) -> VideoGenerationResult:
        """Generate video from text prompt using MiniMax H3."""
        try:
            logger.info(
                "minimax_h3_generation_start",
                model=self.model,
                duration=duration,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            )

            # Prepare parameters
            generation_params: dict[str, Any] = {
                "model": self.model,
            }

            # Add optional parameters if supported
            if seed is not None:
                generation_params["seed"] = seed

            # Generate video using Hugging Face InferenceClient
            # Note: MiniMax H3 generates video with synchronized audio
            video = self.client.text_to_video(
                prompt,
                **generation_params
            )

            # Process the result
            # The InferenceClient returns different types depending on the provider
            # For WaveSpeed + MiniMax H3, we expect a path or URL
            if hasattr(video, 'path'):
                video_path = video.path
                video_url = None
            elif isinstance(video, str):
                video_path = video
                video_url = None
            else:
                # Assume it's a file-like object or URL
                video_path = str(video) if video else None
                video_url = None

            # In production, you would upload this to your storage service
            # For now, we'll return the local path
            provider_video_id = f"minimax_{uuid.uuid4().hex}"

            logger.info(
                "minimax_h3_generation_success",
                provider_video_id=provider_video_id,
                video_path=video_path,
            )

            return VideoGenerationResult(
                success=True,
                video_url=video_url,
                thumbnail_url=None,  # Would need to generate separately
                duration=duration,
                provider_video_id=provider_video_id,
                metadata={
                    "model": self.model,
                    "resolution": resolution,
                    "aspect_ratio": aspect_ratio,
                    "video_path": video_path,
                    "seed": seed,
                },
            )

        except Exception as exc:
            logger.error("minimax_h3_generation_failed", error=str(exc))
            return VideoGenerationResult(
                success=False,
                error_message=f"MiniMax H3 generation failed: {exc}",
                metadata={
                    "model": self.model,
                    "error_type": type(exc).__name__,
                },
            )

    @staticmethod
    def is_configured() -> bool:
        """Check if MiniMax H3 provider is properly configured."""
        return bool(settings.HF_TOKEN) and _HAS_HUGGINGFACE


class MockMiniMaxH3Provider(VideoGenerationProvider):
    """Mock MiniMax H3 provider for testing without API calls."""

    def __init__(self) -> None:
        logger.warning("Using MockMiniMaxH3Provider - no real API calls will be made")

    def _build_educational_prompt(
        self,
        topic: str,
        scene_description: str,
        visual_style: str = "Clean educational animation, modern classroom, professional academic style",
        camera: str = "Medium shot, slow camera movement",
        action: str = "Educational content presentation",
        audio: str = "Clear educational narration in Spanish, subtle classroom ambience, no background music",
    ) -> str:
        """Build a specialized prompt for educational video generation."""
        prompt = f"""Create a high-quality educational video scene.

Topic:
{topic}

Scene:
{scene_description}

Visual style:
{visual_style}

Camera:
{camera}

Action:
{action}

Audio:
{audio}
"""
        return prompt.strip()

    def generate_sync(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "480p",
        aspect_ratio: str = "16:9",
        seed: int | None = None,
        **kwargs: Any,
    ) -> VideoGenerationResult:
        """Synchronous version for Celery tasks."""
        return self.generate(prompt, duration, resolution, aspect_ratio, seed, **kwargs)

    async def generate(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "480p",
        aspect_ratio: str = "16:9",
        seed: int | None = None,
        **kwargs: Any,
    ) -> VideoGenerationResult:
        """Return mock video generation result."""
        fake_video_id = f"mock_minimax_{uuid.uuid4().hex}"
        
        logger.info(
            "mock_minimax_h3_generation",
            provider_video_id=fake_video_id,
            duration=duration,
            resolution=resolution,
        )

        return VideoGenerationResult(
            success=True,
            video_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            thumbnail_url="https://peach.blender.org/wp-content/uploads/title_anouncement.jpg?x11217",
            duration=duration,
            provider_video_id=fake_video_id,
            metadata={
                "model": "mock_minimax_h3",
                "resolution": resolution,
                "aspect_ratio": aspect_ratio,
                "seed": seed,
                "mock": True,
            },
        )

    def generate_sync(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "480p",
        aspect_ratio: str = "16:9",
        seed: int | None = None,
        **kwargs: Any,
    ) -> VideoGenerationResult:
        """Synchronous version for Celery tasks."""
        return self.generate(prompt, duration, resolution, aspect_ratio, seed, **kwargs)

    def is_configured(self) -> bool:
        """Mock provider is always configured."""
        return True


def get_video_provider() -> VideoGenerationProvider:
    """Factory function to get the appropriate video provider."""
    if not MiniMaxH3Provider.is_configured():
        logger.warning("MiniMax H3 not configured, using mock provider")
        return MockMiniMaxH3Provider()
    return MiniMaxH3Provider()
