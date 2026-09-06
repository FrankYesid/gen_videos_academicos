from __future__ import annotations

import os
import pytest
from app.providers.text.groq import GroqProvider, MockGroqProvider, get_groq_provider
from app.schemas.script import ScriptOutput


class TestGroqProvider:
    """Tests for Groq text generation provider."""

    @pytest.mark.asyncio
    async def test_mock_provider_generate(self):
        """Test mock provider text generation."""
        provider = MockGroqProvider()
        result = await provider.generate("Test prompt")
        assert result == "This is a mock response from the Groq provider."

    @pytest.mark.asyncio
    async def test_mock_provider_generate_structured(self):
        """Test mock provider structured generation."""
        provider = MockGroqProvider()
        result = await provider.generate_structured(
            "Test prompt",
            ScriptOutput,
        )
        assert isinstance(result, ScriptOutput)
        assert result.title is not None
        assert len(result.scenes) > 0

    def test_mock_provider_is_configured(self):
        """Test mock provider is always configured."""
        provider = MockGroqProvider()
        assert provider.is_configured() is True

    def test_get_groq_provider_mock(self):
        """Test factory returns mock when not configured."""
        provider = get_groq_provider()
        # Should return mock since GROQ_API_KEY is not set
        assert isinstance(provider, MockGroqProvider)


class TestGroqProviderIntegration:
    """Integration tests for Groq provider (requires API key)."""

    @pytest.mark.skipif(
        "not os.getenv('GROQ_API_KEY')",
        reason="GROQ_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_provider_generate(self):
        """Test real provider text generation."""
        provider = GroqProvider()
        result = await provider.generate("What is 2+2?")
        assert "4" in result or "four" in result.lower()

    @pytest.mark.skipif(
        "not os.getenv('GROQ_API_KEY')",
        reason="GROQ_API_KEY not set"
    )
    def test_real_provider_is_configured(self):
        """Test real provider is configured with API key."""
        provider = GroqProvider()
        assert provider.is_configured() is True
