from __future__ import annotations

import uuid
from datetime import datetime

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.video import Video, VideoStatus
from app.models.scene import Scene
from app.schemas.script import ScriptOutput
from app.services.content_service import get_content_service
from app.services.script_service import get_script_service
from app.services.video_composer import get_video_composer
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@shared_task(bind=True, name="generate_script_task")
def generate_script_task(
    self,
    course_id: str,
    document_text: str,
    analysis_data: dict,
    pedagogical_data: dict,
) -> dict:
    """Generate educational script using Groq with security validation."""
    
    db = SessionLocal()
    try:
        content_service = get_content_service()
        
        system_prompt = """
        You are an expert educational video scriptwriter. Create engaging, clear, 
        and pedagogically sound video scripts for academic content.
        """
        
        user_prompt = f"""
        Create a comprehensive educational video script based on this analysis:
        
        Analysis: {analysis_data}
        Pedagogical Design: {pedagogical_data}
        
        Requirements:
        - Clear, educational narration in Spanish
        - Specific visual instructions for each scene
        - Appropriate on-screen text
        - Educational purpose for each scene
        - 4-8 scenes with appropriate pacing
        """
        
        # Generate script with security check
        from app.schemas.script import ScriptOutput
        
        # Use synchronous method for Celery task
        text_provider = content_service.text_provider
        if hasattr(text_provider, 'generate_structured_sync'):
            script = text_provider.generate_structured_sync(
                prompt=user_prompt,
                response_schema=ScriptOutput,
                system_prompt=system_prompt,
            )
            # Security check separately
            security_service = content_service.security_service
            if hasattr(security_service, 'analyze_sync'):
                security_result = security_service.analyze_sync(user_prompt)
            else:
                import asyncio
                security_result = asyncio.run(security_service.analyze(user_prompt))
        else:
            import asyncio
            script, security_result = asyncio.run(content_service.generate_content(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_schema=ScriptOutput,
                require_security_check=True,
            ))
        
        if script is None:
            return {
                "success": False,
                "error": f"Content generation blocked: {security_result.reason}",
                "security_result": {
                    "is_safe": security_result.is_safe,
                    "security_score": security_result.security_score,
                    "blocked": security_result.blocked,
                    "reason": security_result.reason,
                }
            }
        
        return {
            "success": True,
            "script": script.model_dump(),
            "security_result": {
                "is_safe": security_result.is_safe,
                "security_score": security_result.security_score,
                "blocked": security_result.blocked,
            }
        }
        
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }
    finally:
        db.close()


@shared_task(bind=True, name="generate_scene_video_task")
def generate_scene_video_task(
    self,
    course_id: str,
    scene_data: dict,
    topic: str = "Educational content",
    resolution: str = "480p",
    aspect_ratio: str = "16:9",
) -> dict:
    """Generate video for a single scene using MiniMax H3."""
    
    db = SessionLocal()
    try:
        script_service = get_script_service()
        
        # Generate video for this scene (use sync method for Celery)
        video_provider = script_service.video_provider
        if hasattr(video_provider, 'generate_sync'):
            video_result = video_provider.generate_sync(
                prompt=scene_data["prompt"],
                duration=scene_data["duration"],
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            )
            
            result = {
                "scene_number": scene_data["scene_number"],
                "title": scene_data["title"],
                "success": video_result.success,
                "video_url": video_result.video_url,
                "thumbnail_url": video_result.thumbnail_url,
                "duration": video_result.duration,
                "provider_video_id": video_result.provider_video_id,
                "error_message": video_result.error_message,
                "metadata": video_result.metadata,
            }
        else:
            import asyncio
            result = asyncio.run(script_service.generate_scene_video(
                scene_prompt=scene_data,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            ))
        
        return result
        
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "scene_number": scene_data.get("scene_number"),
        }
    finally:
        db.close()


@shared_task(bind=True, name="compose_video_task")
def compose_video_task(
    self,
    course_id: str,
    video_urls: list[str],
    output_path: str | None = None,
    resolution: str = "480p",
    fps: int = 30,
) -> dict:
    """Compose multiple scene videos into final video using FFmpeg."""
    
    db = SessionLocal()
    try:
        video_composer = get_video_composer()
        
        result = video_composer.concatenate_videos(
            video_urls=video_urls,
            output_path=output_path,
            resolution=resolution,
            fps=fps,
            normalize_audio=True,
        )
        
        return result
        
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }
    finally:
        db.close()


@shared_task(bind=True, name="generate_complete_video_task")
def generate_complete_video_task(
    self,
    course_id: str,
    script_data: dict,
    topic: str = "Educational content",
    resolution: str = "480p",
    aspect_ratio: str = "16:9",
) -> dict:
    """Orchestrate complete video generation pipeline."""
    
    db = SessionLocal()
    try:
        # Convert script data to ScriptOutput
        from app.schemas.script import ScriptOutput
        script = ScriptOutput.model_validate(script_data)
        
        # Process script into scene prompts
        script_service = get_script_service()
        scene_prompts = script_service.process_script_for_video(
            script=script,
            topic=topic,
        )
        
        # Generate videos for each scene
        scene_results = []
        video_urls = []
        
        for scene_prompt in scene_prompts:
            # Launch async task for each scene
            result = generate_scene_video_task(
                course_id=course_id,
                scene_data=scene_prompt,
                topic=topic,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            )
            
            scene_results.append(result)
            
            if result["success"]:
                video_urls.append(result["video_url"])
            else:
                logger.error(
                    "scene_generation_failed",
                    course_id=course_id,
                    scene_number=scene_prompt["scene_number"],
                    error=result.get("error_message"),
                )
        
        # Check if all scenes were generated successfully
        successful_scenes = sum(1 for r in scene_results if r["success"])
        
        if successful_scenes != len(scene_prompts):
            logger.error(
                "generate_complete_video_task_partial_failure",
                course_id=course_id,
                successful=successful_scenes,
                total=len(scene_prompts),
            )
            return {
                "success": False,
                "error": f"Only {successful_scenes}/{len(scene_prompts)} scenes generated successfully",
                "scene_results": scene_results,
            }
        
        # Compose final video
        if len(video_urls) > 1:
            compose_result = compose_video_task(
                course_id=course_id,
                video_urls=video_urls,
                resolution=resolution,
            )
            
            if not compose_result["success"]:
                return {
                    "success": False,
                    "error": f"Video composition failed: {compose_result.get('error_message')}",
                    "scene_results": scene_results,
                }
            
            final_video_url = compose_result["output_path"]
        else:
            # Single scene, no composition needed
            final_video_url = video_urls[0]
        
        return {
            "success": True,
            "final_video_url": final_video_url,
            "scenes_count": len(scene_prompts),
            "scene_results": scene_results,
        }
        
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }
    finally:
        db.close()


@shared_task(bind=True, name="security_check_task")
def security_check_task(
    self,
    course_id: str,
    text: str,
) -> dict:
    """Perform security check on text using Prompt Guard 2."""
    
    try:
        from app.providers.security.prompt_guard import get_prompt_guard
        
        security_service = get_prompt_guard()
        # Use synchronous method for Celery task
        if hasattr(security_service, 'analyze_sync'):
            result = security_service.analyze_sync(text)
        else:
            import asyncio
            result = asyncio.run(security_service.analyze(text))
        
        return {
            "success": True,
            "is_safe": result.is_safe,
            "security_score": result.security_score,
            "blocked": result.blocked,
            "reason": result.reason,
            "chunks_checked": result.chunks_checked,
        }
        
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }
