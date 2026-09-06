from __future__ import annotations

import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VideoComposer:
    """Service for composing multiple video scenes into a final video using FFmpeg."""

    def __init__(self) -> None:
        self.temp_dir = Path(tempfile.gettempdir()) / "video_composer"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _check_ffmpeg_installed(self) -> bool:
        """Check if FFmpeg is installed and accessible."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _download_video(self, url: str, output_path: Path) -> bool:
        """Download video from URL to local path."""
        try:
            import httpx
            
            response = httpx.get(url, timeout=30, follow_redirects=True)
            response.raise_for_status()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info("video_downloaded", url=url, output_path=str(output_path))
            return True
            
        except Exception as exc:
            logger.error("video_download_failed", url=url, error=str(exc))
            return False

    def _create_concat_list(self, video_paths: list[Path]) -> Path:
        """Create FFmpeg concat demuxer list file."""
        list_path = self.temp_dir / f"concat_{uuid.uuid4().hex}.txt"
        
        with open(list_path, "w") as f:
            for video_path in video_paths:
                # FFmpeg requires escaped paths
                escaped_path = str(video_path).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
        
        return list_path

    def concatenate_videos(
        self,
        video_urls: list[str],
        output_path: str | None = None,
        normalize_audio: bool = True,
        resolution: str = "480p",
        fps: int = 30,
    ) -> dict[str, Any]:
        """Concatenate multiple videos into a single video file."""
        
        if not self._check_ffmpeg_installed():
            logger.error("ffmpeg_not_installed")
            return {
                "success": False,
                "error_message": "FFmpeg is not installed or not accessible",
            }

        if not video_urls:
            logger.error("no_videos_to_concatenate")
            return {
                "success": False,
                "error_message": "No videos provided for concatenation",
            }

        try:
            # Download all videos to temp directory
            video_paths = []
            for i, url in enumerate(video_urls):
                video_path = self.temp_dir / f"scene_{i+1}_{uuid.uuid4().hex}.mp4"
                if not self._download_video(url, video_path):
                    return {
                        "success": False,
                        "error_message": f"Failed to download video {i+1}",
                    }
                video_paths.append(video_path)

            # Create concat list
            concat_list = self._create_concat_list(video_paths)

            # Set output path
            if output_path is None:
                output_path = str(self.temp_dir / f"final_video_{uuid.uuid4().hex}.mp4")
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build FFmpeg command
            # Basic concatenation with audio normalization
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-r", str(fps),
            ]

            # Add resolution scaling if specified
            if resolution == "480p":
                cmd.extend(["-vf", "scale=-2:480"])
            elif resolution == "720p":
                cmd.extend(["-vf", "scale=-2:720"])
            elif resolution == "1080p":
                cmd.extend(["-vf", "scale=-2:1080"])

            # Add audio normalization filter if requested
            if normalize_audio:
                cmd.extend([
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                ])

            cmd.extend([
                "-movflags", "+faststart",
                str(output_path),
                "-y",  # Overwrite output file if exists
            ])

            logger.info(
                "ffmpeg_concatenate_start",
                input_videos=len(video_urls),
                output_path=str(output_path),
                resolution=resolution,
            )

            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(
                    "ffmpeg_concatenate_failed",
                    returncode=result.returncode,
                    stderr=result.stderr,
                )
                return {
                    "success": False,
                    "error_message": f"FFmpeg failed: {result.stderr}",
                }

            # Get video duration
            duration_cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(output_path),
            ]
            
            duration_result = subprocess.run(
                duration_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            duration = None
            if duration_result.returncode == 0:
                try:
                    duration = float(duration_result.stdout.strip())
                except ValueError:
                    pass

            logger.info(
                "ffmpeg_concatenate_success",
                output_path=str(output_path),
                duration=duration,
            )

            # Clean up temporary files
            for video_path in video_paths:
                try:
                    video_path.unlink()
                except Exception:
                    pass
            try:
                concat_list.unlink()
            except Exception:
                pass

            return {
                "success": True,
                "output_path": str(output_path),
                "duration": duration,
                "resolution": resolution,
                "fps": fps,
                "input_count": len(video_urls),
            }

        except subprocess.TimeoutExpired:
            logger.error("ffmpeg_timeout")
            return {
                "success": False,
                "error_message": "FFmpeg operation timed out",
            }
        except Exception as exc:
            logger.error("video_composition_failed", error=str(exc))
            return {
                "success": False,
                "error_message": f"Video composition failed: {exc}",
            }


# Singleton instance
_video_composer: VideoComposer | None = None


def get_video_composer() -> VideoComposer:
    """Get the video composer singleton."""
    global _video_composer
    if _video_composer is None:
        _video_composer = VideoComposer()
    return _video_composer
