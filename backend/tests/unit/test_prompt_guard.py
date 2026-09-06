from __future__ import annotations

import os
import pytest
from app.providers.security.prompt_guard import (
    GroqPromptGuard,
    MockPromptGuard,
    get_prompt_guard,
)
from app.providers.security.base import SecurityAnalysisResult


class TestPromptGuard:
    """Tests for Prompt Guard security service."""

    @pytest.mark.asyncio
    async def test_mock_provider_analyze(self):
        """Test mock provider security analysis."""
        provider = MockPromptGuard()
        result = await provider.analyze("Test input")
        assert result.is_safe is True
        assert result.blocked is False
        assert result.security_score == 1.0

    @pytest.mark.asyncio
    async def test_mock_provider_analyze_chunks(self):
        """Test mock provider chunk analysis."""
        provider = MockPromptGuard()
        long_text = "Test " * 1000
        result = await provider.analyze_chunks(long_text, chunk_size=512)
        assert result.is_safe is True
        assert result.blocked is False

    def test_mock_provider_is_configured(self):
        """Test mock provider is always configured."""
        provider = MockPromptGuard()
        assert provider.is_configured() is True

    def test_get_prompt_guard_mock(self):
        """Test factory returns mock when not configured."""
        provider = get_prompt_guard()
        # Should return mock since GROQ_API_KEY is not set
        assert isinstance(provider, MockPromptGuard)

    @pytest.mark.asyncio
    async def test_empty_text_analysis(self):
        """Test analysis of empty text."""
        provider = MockPromptGuard()
        result = await provider.analyze("")
        assert result.is_safe is True
        assert result.chunks_checked == 0


class TestPromptGuardIntegration:
    """Integration tests for Prompt Guard (requires API key)."""

    @pytest.mark.skipif(
        "not os.getenv('GROQ_API_KEY')",
        reason="GROQ_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_provider_analyze_safe_content(self):
        """Test real provider with safe content."""
        provider = GroqPromptGuard()
        result = await provider.analyze("This is a normal educational text about mathematics.")
        assert result.is_safe is True
        assert result.blocked is False

    @pytest.mark.skipif(
        "not os.getenv('GROQ_API_KEY')",
        reason="GROQ_API_KEY not set"
    )
    def test_real_provider_is_configured(self):
        """Test real provider is configured with API key."""
        provider = GroqPromptGuard()
        assert provider.is_configured() is True
