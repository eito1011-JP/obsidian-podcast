"""Tests for Claude (Anthropic) LLM provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestClaudeLLMProvider:
    def test_registered_as_claude(self):
        # Import to trigger registration
        import obsidian_podcast.llm.claude  # noqa: F401
        from obsidian_podcast.llm.base import _registry

        assert "claude" in _registry

    @pytest.mark.asyncio
    async def test_generate_calls_anthropic_api(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated text")]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        with patch("obsidian_podcast.llm.claude.anthropic") as mock_anthropic:
            mock_anthropic.AsyncAnthropic.return_value = mock_client

            from obsidian_podcast.llm.claude import ClaudeLLMProvider

            config = MagicMock()
            config.api_key_env = "TEST_KEY"
            config.model = "claude-sonnet-4-20250514"

            with patch.dict("os.environ", {"TEST_KEY": "fake-key"}):
                provider = ClaudeLLMProvider(config)

            result = await provider.generate("test prompt", system_prompt="sys")

            assert result == "Generated text"
            mock_client.messages.create.assert_called_once_with(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system="sys",
                messages=[{"role": "user", "content": "test prompt"}],
            )
