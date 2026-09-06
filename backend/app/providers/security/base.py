from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SecurityAnalysisResult:
    """Result of security analysis on text input."""
    is_safe: bool
    security_score: float  # 0.0 to 1.0
    blocked: bool
    reason: str | None = None
    chunks_checked: int = 0
    timestamp: datetime | None = None
    details: dict[str, Any] | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}


class PromptSecurityService(ABC):
    """Abstract base class for prompt security services."""

    @abstractmethod
    async def analyze(self, text: str) -> SecurityAnalysisResult:
        """Analyze text for security threats (prompt attacks, jailbreaks, etc.)."""
        raise NotImplementedError

    @abstractmethod
    async def analyze_chunks(self, text: str, chunk_size: int = 512) -> SecurityAnalysisResult:
        """Analyze text in chunks for better handling of long documents."""
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the security service is properly configured."""
        raise NotImplementedError
