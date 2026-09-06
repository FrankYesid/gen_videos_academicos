from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.providers.video.minimax_h3 import get_video_provider
from app.schemas.script import ScriptOutput, Scene

logger = get_logger(__name__)


class ScriptService:
    """Service for script generation and scene processing."""

    def __init__(self) -> None:
        self.video_provider = get_video_provider()

    def process_script_for_video(
        self,
        script: ScriptOutput,
        topic: str = "Educational content",
    ) -> list[dict[str, Any]]:
        """Process a script into individual scene prompts for video generation."""
        
        scene_prompts = []
        
        for scene in script.scenes:
            # Build specialized prompt for each scene
            scene_prompt = self.video_provider._build_educational_prompt(
                topic=topic,
                scene_description=f"""
{scene.narration}

Visual: {scene.visual_instruction}
On-screen text: {scene.on_screen_text}
Educational purpose: {scene.educational_purpose}
""",
                visual_style=scene.background or "Clean educational animation, modern classroom, professional academic style",
                camera=scene.camera_angle or "Medium shot, slow camera movement",
                action=f"Educational presentation: {scene.educational_purpose}",
                audio=scene.audio_cue or "Clear educational narration in Spanish, subtle classroom ambience, no background music",
            )
            
            scene_prompts.append({
                "scene_number": scene.id,
                "title": scene.title,
                "prompt": scene_prompt,
                "duration": scene.duration_seconds,
                "original_scene": scene,
            })
        
        logger.info(
            "script_processed_for_video",
            total_scenes=len(scene_prompts),
            total_duration=sum(s["duration"] for s in scene_prompts),
        )
        
        return scene_prompts

    async def generate_scene_video(
        self,
        scene_prompt: dict[str, Any],
        resolution: str = "480p",
        aspect_ratio: str = "16:9",
    ) -> dict[str, Any]:
        """Generate video for a single scene."""
        
        try:
            result = await self.video_provider.generate(
                prompt=scene_prompt["prompt"],
                duration=scene_prompt["duration"],
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            )
            
            logger.info(
                "scene_video_generated",
                scene_number=scene_prompt["scene_number"],
                success=result.success,
                duration=result.duration,
            )
            
            return {
                "scene_number": scene_prompt["scene_number"],
                "title": scene_prompt["title"],
                "success": result.success,
                "video_url": result.video_url,
                "thumbnail_url": result.thumbnail_url,
                "duration": result.duration,
                "provider_video_id": result.provider_video_id,
                "error_message": result.error_message,
                "metadata": result.metadata,
            }
            
        except Exception as exc:
            logger.error(
                "scene_video_generation_failed",
                scene_number=scene_prompt["scene_number"],
                error=str(exc),
            )
            return {
                "scene_number": scene_prompt["scene_number"],
                "title": scene_prompt["title"],
                "success": False,
                "error_message": str(exc),
            }


# Singleton instance
_script_service: ScriptService | None = None


def get_script_service() -> ScriptService:
    """Get the script service singleton."""
    global _script_service
    if _script_service is None:
        _script_service = ScriptService()
    return _script_service
