from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.core.logging import get_logger
from app.providers.text.groq import get_groq_provider
from app.providers.security.prompt_guard import get_prompt_guard
from app.providers.security.base import SecurityAnalysisResult

logger = get_logger(__name__)


class ContentService:
    """Service for content generation with security validation."""

    def __init__(self) -> None:
        self.text_provider = get_groq_provider()
        self.security_service = get_prompt_guard()

    async def generate_content(
        self,
        prompt: str,
        system_prompt: str | None = None,
        response_schema: type[BaseModel] | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        require_security_check: bool = True,
    ) -> tuple[Any, SecurityAnalysisResult]:
        """Generate content with optional security validation."""
        
        # Security check
        security_result: SecurityAnalysisResult
        if require_security_check:
            security_result = await self.security_service.analyze(prompt)
            
            if security_result.blocked:
                logger.warning(
                    "content_generation_blocked",
                    reason=security_result.reason,
                    security_score=security_result.security_score,
                )
                return None, security_result
        else:
            # Skip security check
            from app.providers.security.base import SecurityAnalysisResult
            security_result = SecurityAnalysisResult(
                is_safe=True,
                security_score=1.0,
                blocked=False,
                reason="Security check skipped",
            )

        # Generate content
        try:
            if response_schema:
                content = await self.text_provider.generate_structured(
                    prompt=prompt,
                    response_schema=response_schema,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                content = await self.text_provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            logger.info(
                "content_generation_success",
                has_schema=response_schema is not None,
                security_score=security_result.security_score,
            )

            return content, security_result

        except Exception as exc:
            logger.error("content_generation_failed", error=str(exc))
            raise


# Singleton instance
_content_service: ContentService | None = None


def get_content_service() -> ContentService:
    """Get the content service singleton."""
    global _content_service
    if _content_service is None:
        _content_service = ContentService()
    return _content_service
