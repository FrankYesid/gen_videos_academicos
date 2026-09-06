from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class TextGenerationProvider(ABC):
    """Abstract base class for text generation providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        """Generate text response from a prompt."""
        raise NotImplementedError

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[BaseModel],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> BaseModel:
        """Generate structured response using a Pydantic schema."""
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        raise NotImplementedError
