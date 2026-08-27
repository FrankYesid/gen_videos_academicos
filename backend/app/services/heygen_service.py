from __future__ import annotations

import uuid
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

FORCE_NO_FALLBACK = (
    os.environ.get("FORCE_NO_FALLBACK", "").strip().lower()
    in {"1", "true", "yes", "on"}
)

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.video import VideoStatus
from app.schemas.script import ScriptOutput
from app.schemas.video import VideoStatusResponse

logger = get_logger(__name__)


class HeyGenVideoStatus:
    CREATED = VideoStatus.CREATED
    SUBMITTED = VideoStatus.SUBMITTED
    PROCESSING = VideoStatus.PROCESSING
    COMPLETED = VideoStatus.COMPLETED
    FAILED = VideoStatus.FAILED


class BaseHeyGenProvider(ABC):
    @abstractmethod
    def generate_video(
        self, lesson_id: uuid.UUID, script: ScriptOutput
    ) -> VideoStatusResponse:
        ...

    @abstractmethod
    def check_status(
        self, provider_video_id: str, job_id: str | None = None
    ) -> VideoStatusResponse:
        ...


class MockHeyGenProvider(BaseHeyGenProvider):
    def generate_video(
        self, lesson_id: uuid.UUID, script: ScriptOutput
    ) -> VideoStatusResponse:
        fake_video_id = f"mock_{uuid.uuid4().hex}"
        fake_job_id = f"job_{uuid.uuid4().hex}"
        logger.info(
            "mock_heygen_generate_video",
            lesson_id=str(lesson_id),
            provider_video_id=fake_video_id,
            job_id=fake_job_id,
        )
        return VideoStatusResponse(
            provider_video_id=fake_video_id,
            status=HeyGenVideoStatus.COMPLETED,
            progress=100,
            message="Mock video generated successfully",
            video_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            thumbnail_url="https://peach.blender.org/wp-content/uploads/title_anouncement.jpg?x11217",
            duration=300,
        )

    def check_status(
        self, provider_video_id: str, job_id: str | None = None
    ) -> VideoStatusResponse:
        return VideoStatusResponse(
            provider_video_id=provider_video_id,
            status=HeyGenVideoStatus.COMPLETED,
            progress=100,
            message="Mock video is ready",
            video_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            thumbnail_url="https://peach.blender.org/wp-content/uploads/title_anouncement.jpg?x11217",
            duration=300,
        )


class HeyGenVideoAgentProvider(BaseHeyGenProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.HEYGEN_API_KEY
        self.base_url = settings.HEYGEN_BASE_URL.rstrip("/")
        self.avatar_id = settings.HEYGEN_AVATAR_ID
        self.voice_id = settings.HEYGEN_VOICE_ID
        self.timeout = settings.HEYGEN_TIMEOUT
        self.max_retries = settings.HEYGEN_MAX_RETRIES

    def _build_headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key or "",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _build_prompt(self, script: ScriptOutput) -> str:
        parts: list[str] = []
        if script.title:
            parts.append(f"Título del curso/video: {script.title}.")
        if script.target_audience:
            parts.append(f"Audiencia objetivo: {script.target_audience}.")
        if script.tone:
            parts.append(f"Tono: {script.tone}.")
        if script.introduction:
            parts.append(f"Introducción: {script.introduction}")
        for idx, scene in enumerate(script.scenes, 1):
            narration = scene.narration.strip()
            visual = scene.visual_instruction.strip()
            title = scene.title.strip() if scene.title else ""
            on_screen = scene.on_screen_text.strip() if scene.on_screen_text else ""
            block = []
            if title:
                block.append(f"Sección {idx} · {title}")
            if narration:
                block.append(f"Narración (texto hablado por el avatar: {narration}")
            if visual:
                    block.append(f"Instrucción visual para las escenas/B-roll: {visual}")
            if on_screen:
                block.append(f"Texto superpuesto en pantalla: {on_screen}")
            if block:
                parts.append(" ".join(block))
        if script.conclusion:
            parts.append(f"Conclusión y cierre: {script.conclusion}")
        if script.notes:
            parts.append(f"Notas adicionales: {script.notes}")
        prompt = " ".join(p for p in parts if p).strip()
        if len(prompt) > 10000:
            prompt = prompt[:9900] + "\n[...truncado por límite HeyGen]"
        return prompt

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    def generate_video(
        self, lesson_id: uuid.UUID, script: ScriptOutput
    ) -> VideoStatusResponse:
        if not self.api_key:
            if FORCE_NO_FALLBACK:
                raise RuntimeError(
                    "FORCE_NO_FALLBACK=1: HeyGen API key missing, mock fallback disabled"
                )
            logger.warning("heygen_api_key_missing_fallback_mock", lesson_id=str(lesson_id))
            return MockHeyGenProvider().generate_video(lesson_id, script)

        settings = get_settings()
        url = f"{self.base_url}/v3/video-agents"
        base_payload: dict[str, object] = {
            "prompt": self._build_prompt(script),
            "mode": "generate",
            "orientation": "landscape",
        }
        webhook = getattr(settings, "HEYGEN_WEBHOOK_URL", None) or None
        if webhook:
            base_payload["callback_url"] = webhook

        def _do_post(include_avatar: bool, include_voice: bool) -> tuple[int, str, dict[str, Any] | None]:
            effective: dict[str, object] = dict(base_payload)
            if include_avatar and self.avatar_id:
                effective["avatar_id"] = self.avatar_id
            if include_voice and self.voice_id:
                effective["voice_id"] = self.voice_id
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=self._build_headers(), json=effective)
            text = resp.text[:800]
            js: dict[str, Any] | None = None
            try:
                js = resp.json()
            except Exception:
                js = None
            return resp.status_code, text, js

        scenes_count = len(script.scenes)
        logger.info(
            "heygen_v3_video_agent_submit",
            lesson_id=str(lesson_id),
            title=script.title,
            scenes_count=scenes_count,
            avatar_id=bool(self.avatar_id),
            voice_id=bool(self.voice_id),
        )

        try:
            include_avatar = bool(self.avatar_id)
            include_voice = bool(self.voice_id)
            status_code, detail, data = (0, "", None)
            max_attempts = 4
            attempt = 0
            last_skipped = set()
            while attempt < max_attempts:
                attempt += 1
                status_code, detail, data = _do_post(include_avatar, include_voice)
                if status_code < 400:
                    break
                logger.error(
                    "heygen_v3_submit_failed",
                    status=status_code,
                    body=detail,
                    lesson_id=str(lesson_id),
                    attempt=attempt,
                )
                msg_lower = (detail or "").lower()
                bad_avatar = (
                    "avatar" not in last_skipped
                    and include_avatar
                    and (
                        "invalid avatar_id" in msg_lower
                        or ("invalid_parameter" in msg_lower and "avatar" in msg_lower)
                    )
                )
                bad_voice = (
                    "voice" not in last_skipped
                    and include_voice
                    and (
                        "invalid voice_id" in msg_lower
                        or "voice not found" in msg_lower
                        or ("invalid_parameter" in msg_lower and "voice" in msg_lower)
                    )
                )
                if not bad_avatar and not bad_voice:
                    break
                if bad_avatar:
                    include_avatar = False
                    last_skipped.add("avatar")
                    logger.warning(
                        "heygen_v3_invalid_avatar_id_retrying_without",
                        lesson_id=str(lesson_id),
                    )
                    continue
                if bad_voice:
                    include_voice = False
                    last_skipped.add("voice")
                    logger.warning(
                        "heygen_v3_invalid_voice_id_retrying_without",
                        lesson_id=str(lesson_id),
                    )
                    continue
            if status_code >= 400:
                if FORCE_NO_FALLBACK:
                    raise httpx.HTTPStatusError(
                        f"HeyGen returned {status_code}: {detail}",
                        request=httpx.Request("POST", url),
                        response=httpx.Response(status_code, text=detail or ""),
                    )
                logger.warning(
                    "heygen_v3_submit_bad_status_fallback_mock",
                    lesson_id=str(lesson_id),
                    status=status_code,
                )
                return MockHeyGenProvider().generate_video(lesson_id, script)
            if data is None:
                data = {}
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            if FORCE_NO_FALLBACK:
                raise RuntimeError(
                    f"FORCE_NO_FALLBACK=1: HeyGen provider failed and mock disabled: {exc!s}"
                ) from exc
            logger.warning(
                "heygen_v3_submit_exception_fallback_mock",
                lesson_id=str(lesson_id),
                error=str(exc),
            )
            return MockHeyGenProvider().generate_video(lesson_id, script)

        inner = data.get("data") or data
        session_id = str(inner.get("session_id")) or str(data.get("session_id")) or str(uuid.uuid4().hex)
        video_id = inner.get("video_id")
        raw_status = str(inner.get("status") or "submitted").lower()
        logger.info(
            "heygen_v3_submitted",
            lesson_id=str(lesson_id),
            session_id=session_id,
            initial_video_id=video_id,
            status=raw_status,
        )
        return VideoStatusResponse(
            provider_video_id=str(video_id or session_id),
            job_id=session_id,
            status=HeyGenVideoStatus.SUBMITTED,
            progress=5,
            message=f"HeyGen v3 Video Agent session {session_id} enqueued",
            video_url=None,
            thumbnail_url=None,
            duration=None,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    def check_status(
        self, provider_video_id: str, job_id: str | None = None
    ) -> VideoStatusResponse:
        if not self.api_key:
            return MockHeyGenProvider().check_status(provider_video_id, job_id)

        def _map_status(raw: str, progress: int) -> str:
            r = (raw or "").lower()
            if r in {"completed", "success", "done"}:
                return HeyGenVideoStatus.COMPLETED
            if r in {"failed", "error", "cancelled", "canceled"}:
                return HeyGenVideoStatus.FAILED
            if r in {"processing", "rendering", "generating", "thinking", "in_progress"}:
                return HeyGenVideoStatus.PROCESSING
            if r == "submitted" or r == "pending" or r == "queued":
                return HeyGenVideoStatus.SUBMITTED
            return HeyGenVideoStatus.PROCESSING if progress > 0 and progress < 100 else HeyGenVideoStatus.SUBMITTED

        raw: Any = None
        data: Any = None
        candidate_urls: list[str] = []
        if provider_video_id and provider_video_id.startswith("v_"):
            candidate_urls.append(f"{self.base_url}/v3/videos/{provider_video_id}")
        if job_id:
            candidate_urls.append(f"{self.base_url}/v3/video-agents/{job_id}")
        if provider_video_id:
            candidate_urls.append(f"{self.base_url}/v1/video_status/{provider_video_id}")
        candidate_urls = [u for u in dict.fromkeys(candidate_urls) if u]

        last_err: Exception | None = None
        for url in candidate_urls:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url, headers=self._build_headers())
                    if resp.status_code == 404:
                        continue
                    resp.raise_for_status()
                    payload = resp.json()
                    data = payload.get("data") or payload
                    break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                continue

        if data is None:
            if last_err:
                raise last_err
            return VideoStatusResponse(
                provider_video_id=provider_video_id,
                status=HeyGenVideoStatus.SUBMITTED,
                progress=0,
                message="Aún no hay estado disponible en HeyGen",
            )

        raw_status = str(data.get("status") or data.get("session_status") or data.get("state") or "").lower()
        progress = int(data.get("progress") or 0)
        message = (
            data.get("message")
            or data.get("error")
            or data.get("error_message")
            or data.get("status_message")
        )

        status = _map_status(raw_status, progress)
        if status == HeyGenVideoStatus.COMPLETED:
            progress = 100

        video_url = data.get("video_url") or data.get("url") or data.get("download_url")
        thumbnail_url = data.get("thumbnail_url") or data.get("cover_url") or data.get("thumbnail")
        duration = data.get("duration")

        if duration is not None:
            try:
                s = str(duration).replace("s", "").strip()
                duration = int(float(s))
            except (ValueError, TypeError):
                duration = None

        return VideoStatusResponse(
            provider_video_id=provider_video_id,
            status=status,
            progress=progress,
            message=message,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            duration=duration,
        )


class HeyGenTemplateProvider(BaseHeyGenProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.HEYGEN_API_KEY
        self.base_url = settings.HEYGEN_BASE_URL.rstrip("/")
        self.template_id = settings.HEYGEN_TEMPLATE_ID
        self.timeout = settings.HEYGEN_TIMEOUT
        self.max_retries = settings.HEYGEN_MAX_RETRIES

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _build_template_variables(self, script: ScriptOutput) -> dict:
        variables: dict[str, object] = {
            "title": script.title,
            "introduction": script.introduction,
            "conclusion": script.conclusion,
            "total_duration_seconds": script.total_duration_seconds,
            "target_audience": script.target_audience,
            "tone": script.tone,
            "scenes_count": len(script.scenes),
        }
        for idx, scene in enumerate(script.scenes, start=1):
            variables[f"scene_{idx}_title"] = scene.title
            variables[f"scene_{idx}_narration"] = scene.narration
            variables[f"scene_{idx}_visual"] = scene.visual_instruction
            variables[f"scene_{idx}_text"] = scene.on_screen_text
            variables[f"scene_{idx}_duration"] = scene.duration_seconds
            variables[f"scene_{idx}_purpose"] = scene.educational_purpose
        return variables

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    def generate_video(
        self, lesson_id: uuid.UUID, script: ScriptOutput
    ) -> VideoStatusResponse:
        if not self.api_key or not self.template_id:
            logger.warning(
                "heygen_template_config_missing_fallback_mock",
                lesson_id=str(lesson_id),
                has_key=bool(self.api_key),
                has_template=bool(self.template_id),
            )
            return MockHeyGenProvider().generate_video(lesson_id, script)

        payload = {
            "template_id": self.template_id,
            "variables": self._build_template_variables(script),
            "title": script.title or f"Lesson-{str(lesson_id)[:8]}",
        }

        logger.info(
            "heygen_template_submit",
            lesson_id=str(lesson_id),
            template_id=self.template_id,
            title=script.title,
            scenes_count=len(script.scenes),
        )

        url = f"{self.base_url}/v2/template/generate"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=self._build_headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()

        job_id = str(data.get("job_id") or uuid.uuid4().hex)
        provider_video_id = str(data.get("video_id") or data.get("template_task_id") or job_id)
        logger.info(
            "heygen_template_submitted",
            lesson_id=str(lesson_id),
            job_id=job_id,
            provider_video_id=provider_video_id,
        )
        return VideoStatusResponse(
            provider_video_id=provider_video_id,
            status=HeyGenVideoStatus.SUBMITTED,
            progress=5,
            message="Template video submitted to HeyGen",
            video_url=None,
            thumbnail_url=None,
            duration=None,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    def check_status(
        self, provider_video_id: str, job_id: str | None = None
    ) -> VideoStatusResponse:
        if not self.api_key:
            return MockHeyGenProvider().check_status(provider_video_id, job_id)

        url = f"{self.base_url}/v1/video_status/{provider_video_id}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, headers=self._build_headers())
            resp.raise_for_status()
            data = resp.json()

        raw_status = str(data.get("status") or "").lower()
        progress = int(data.get("progress") or 0)
        message = data.get("message") or data.get("error")

        if raw_status in {"completed", "success", "done"}:
            status = HeyGenVideoStatus.COMPLETED
            progress = 100
        elif raw_status in {"failed", "error", "cancelled", "canceled"}:
            status = HeyGenVideoStatus.FAILED
        elif raw_status in {"processing", "rendering", "generating"}:
            status = HeyGenVideoStatus.PROCESSING
        else:
            status = HeyGenVideoStatus.SUBMITTED

        video_url = data.get("video_url") or data.get("url")
        thumbnail_url = data.get("thumbnail_url") or data.get("cover_url")
        duration = data.get("duration")

        return VideoStatusResponse(
            provider_video_id=provider_video_id,
            status=status,
            progress=progress,
            message=message,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            duration=duration,
        )


def get_heygen_provider(provider_name: str | None = None) -> BaseHeyGenProvider:
    settings = get_settings()
    mode = (provider_name or settings.HEYGEN_MODE or "mock").lower()

    if mode == "heygen_agent":
        if not settings.HEYGEN_API_KEY:
            logger.warning("heygen_agent_no_api_key_fallback_mock")
            return MockHeyGenProvider()
        return HeyGenVideoAgentProvider()

    if mode == "heygen_template":
        if not settings.HEYGEN_API_KEY or not settings.HEYGEN_TEMPLATE_ID:
            logger.warning("heygen_template_no_config_fallback_mock")
            return MockHeyGenProvider()
        return HeyGenTemplateProvider()

    return MockHeyGenProvider()
