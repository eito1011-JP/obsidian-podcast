"""Tests for OpenAI-compatible LLM provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestOpenAILLMProvider:
    def test_registered_as_openai(self):
        import obsidian_podcast.llm.openai_provider  # noqa: F401
        from obsidian_podcast.llm.base import _registry

        assert "openai" in _registry

    @pytest.mark.asyncio
    async def test_generate_calls_openai_api(self):
        mock_choice = MagicMock()
        mock_choice.message.content = "Generated text"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("obsidian_podcast.llm.openai_provider.openai") as mock_openai:
            mock_openai.AsyncOpenAI.return_value = mock_client

            from obsidian_podcast.llm.openai_provider import OpenAILLMProvider

            config = MagicMock()
            config.api_key_env = "TEST_KEY"
            config.model = "gpt-4"
            config.base_url = None

            with patch.dict("os.environ", {"TEST_KEY": "fake-key"}):
                provider = OpenAILLMProvider(config)

            result = await provider.generate("test prompt", system_prompt="sys")

            assert result == "Generated text"
            mock_client.chat.completions.create.assert_called_once_with(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "sys"},
                    {"role": "user", "content": "test prompt"},
                ],
            )

    @pytest.mark.asyncio
    async def test_base_url_passed_when_configured(self):
        with patch("obsidian_podcast.llm.openai_provider.openai") as mock_openai:
            mock_openai.AsyncOpenAI.return_value = AsyncMock()

            from obsidian_podcast.llm.openai_provider import OpenAILLMProvider

            config = MagicMock()
            config.api_key_env = ""
            config.model = "qwen2.5"
            config.base_url = "http://localhost:11434/v1"

            provider = OpenAILLMProvider(config)  # noqa: F841

            mock_openai.AsyncOpenAI.assert_called_once_with(
                api_key="ollama",
                base_url="http://localhost:11434/v1",
            )

    @pytest.mark.asyncio
    async def test_empty_api_key_env_uses_ollama_default(self):
        with patch("obsidian_podcast.llm.openai_provider.openai") as mock_openai:
            mock_openai.AsyncOpenAI.return_value = AsyncMock()

            from obsidian_podcast.llm.openai_provider import OpenAILLMProvider

            config = MagicMock()
            config.api_key_env = ""
            config.model = "qwen2.5"
            config.base_url = None

            provider = OpenAILLMProvider(config)  # noqa: F841

            call_kwargs = mock_openai.AsyncOpenAI.call_args
            assert call_kwargs[1]["api_key"] == "ollama"

    @pytest.mark.asyncio
    async def test_generate_returns_empty_on_no_choices(self):
        mock_response = MagicMock()
        mock_response.choices = []

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("obsidian_podcast.llm.openai_provider.openai") as mock_openai:
            mock_openai.AsyncOpenAI.return_value = mock_client

            from obsidian_podcast.llm.openai_provider import OpenAILLMProvider

            config = MagicMock()
            config.api_key_env = ""
            config.model = "gpt-4"
            config.base_url = None

            provider = OpenAILLMProvider(config)
            result = await provider.generate("test")

            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_returns_empty_on_none_content(self):
        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("obsidian_podcast.llm.openai_provider.openai") as mock_openai:
            mock_openai.AsyncOpenAI.return_value = mock_client

            from obsidian_podcast.llm.openai_provider import OpenAILLMProvider

            config = MagicMock()
            config.api_key_env = ""
            config.model = "gpt-4"
            config.base_url = None

            provider = OpenAILLMProvider(config)
            result = await provider.generate("test")

            assert result == ""
