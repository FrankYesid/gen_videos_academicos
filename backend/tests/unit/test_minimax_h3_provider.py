from __future__ import annotations

import os
import pytest
from app.providers.video.minimax_h3 import (
    MiniMaxH3Provider,
    MockMiniMaxH3Provider,
    get_video_provider,
)
from app.providers.video.base import VideoGenerationResult


class TestMiniMaxH3Provider:
    """Tests for MiniMax H3 video generation provider."""

    @pytest.mark.asyncio
    async def test_mock_provider_generate(self):
        """Test mock provider video generation."""
        provider = MockMiniMaxH3Provider()
        result = await provider.generate(
            prompt="Test prompt",
            duration=5,
            resolution="480p",
            aspect_ratio="16:9",
        )
        assert result.success is True
        assert result.video_url is not None
        assert result.duration == 5
        assert result.provider_video_id is not None

    @pytest.mark.asyncio
    async def test_mock_provider_with_different_params(self):
        """Test mock provider with different parameters."""
        provider = MockMiniMaxH3Provider()
        result = await provider.generate(
            prompt="Test prompt",
            duration=10,
            resolution="720p",
            aspect_ratio="16:9",
            seed=42,
        )
        assert result.success is True
        assert result.duration == 10
        assert result.metadata["resolution"] == "720p"
        assert result.metadata["seed"] == 42

    def test_mock_provider_is_configured(self):
        """Test mock provider is always configured."""
        provider = MockMiniMaxH3Provider()
        assert provider.is_configured() is True

    def test_get_video_provider_mock(self):
        """Test factory returns mock when not configured."""
        provider = get_video_provider()
        # Should return mock since HF_TOKEN is not set
        assert isinstance(provider, MockMiniMaxH3Provider)

    @pytest.mark.asyncio
    async def test_mock_provider_educational_prompt(self):
        """Test mock provider with educational prompt building."""
        provider = MockMiniMaxH3Provider()
        educational_prompt = provider._build_educational_prompt(
            topic="Probability",
            scene_description="A teacher explaining coin tosses",
        )
        assert "Probability" in educational_prompt
        assert "coin tosses" in educational_prompt
        assert "educational" in educational_prompt.lower()


class TestMiniMaxH3ProviderIntegration:
    """Integration tests for MiniMax H3 provider (requires API key)."""

    @pytest.mark.skipif(
        "not os.getenv('HF_TOKEN')",
        reason="HF_TOKEN not set"
    )
    @pytest.mark.asyncio
    async def test_real_provider_generate(self):
        """Test real provider video generation."""
        provider = MiniMaxH3Provider()
        result = await provider.generate(
            prompt="A simple educational scene",
            duration=5,
            resolution="480p",
        )
        # This test will make a real API call
        assert result is not None

    @pytest.mark.skipif(
        "not os.getenv('HF_TOKEN')",
        reason="HF_TOKEN not set"
    )
    def test_real_provider_is_configured(self):
        """Test real provider is configured with API key."""
        provider = MiniMaxH3Provider()
        assert provider.is_configured() is True
