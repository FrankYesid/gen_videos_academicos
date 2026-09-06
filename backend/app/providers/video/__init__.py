from __future__ import annotations

from app.providers.video.base import VideoGenerationProvider
from app.providers.video.minimax_h3 import MiniMaxH3Provider

__all__ = ["VideoGenerationProvider", "MiniMaxH3Provider"]
