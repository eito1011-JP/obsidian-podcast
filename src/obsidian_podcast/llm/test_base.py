"""Tests for LLM base module: providers, registry, text splitting, script gen."""

from unittest.mock import AsyncMock

import pytest


class TestLLMProvider:
    def test_cannot_instantiate_directly(self):
        from obsidian_podcast.llm.base import LLMProvider

        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore[abstract]


class TestRegistry:
    def test_register_and_create(self, monkeypatch):
        from obsidian_podcast.llm.base import (
            LLMProvider,
            _registry,
            create_llm_engine,
            register_llm_engine,
        )

        # Save and clear registry for isolation
        saved = dict(_registry)
        monkeypatch.setattr("obsidian_podcast.llm.base._registry", {})

        @register_llm_engine("test-engine")
        class TestProvider(LLMProvider):
            def __init__(self, config) -> None:
                self.config = config

            async def generate(self, prompt: str, system_prompt: str = "") -> str:
                return "test"

        class FakeConfig:
            engine = "test-engine"

        provider = create_llm_engine(FakeConfig())
        assert isinstance(provider, TestProvider)

        # Restore
        monkeypatch.setattr("obsidian_podcast.llm.base._registry", saved)

    def test_create_unknown_engine_raises(self, monkeypatch):
        from obsidian_podcast.llm.base import create_llm_engine

        monkeypatch.setattr("obsidian_podcast.llm.base._registry", {})

        class FakeConfig:
            engine = "nonexistent"

        with pytest.raises(ValueError, match="Unknown LLM engine"):
            create_llm_engine(FakeConfig())


class TestSplitTextForLLM:
    def test_empty_text_returns_empty(self):
        from obsidian_podcast.llm.base import split_text_for_llm

        assert split_text_for_llm("") == []
        assert split_text_for_llm("   ") == []

    def test_short_text_single_chunk(self):
        from obsidian_podcast.llm.base import split_text_for_llm

        text = "Hello world"
        result = split_text_for_llm(text, max_chars=100)
        assert result == [text]

    def test_long_text_multiple_chunks(self):
        from obsidian_podcast.llm.base import split_text_for_llm

        # Create text with multiple paragraphs
        paragraphs = [f"Paragraph {i} content here." for i in range(20)]
        text = "\n\n".join(paragraphs)
        result = split_text_for_llm(text, max_chars=100)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 100

    def test_long_paragraph_splits_by_sentences(self):
        from obsidian_podcast.llm.base import split_text_for_llm

        # One long paragraph with Japanese sentences (must exceed max_chars)
        text = "これは最初の文です。これは二番目の文です。これは三番目の文です。"
        result = split_text_for_llm(text, max_chars=20)
        assert len(result) >= 2


class TestGeneratePodcastScript:
    @pytest.mark.asyncio
    async def test_converts_text_with_provider(self):
        from obsidian_podcast.llm.base import generate_podcast_script

        mock_provider = AsyncMock()
        mock_provider.generate.return_value = "Converted script"

        result = await generate_podcast_script(
            "Some article text", mock_provider, max_chunk_chars=4000
        )
        assert result == "Converted script"
        mock_provider.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_text_returns_as_is(self):
        from obsidian_podcast.llm.base import generate_podcast_script

        mock_provider = AsyncMock()
        result = await generate_podcast_script("", mock_provider)
        assert result == ""
        mock_provider.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_chunks_joined(self):
        from obsidian_podcast.llm.base import generate_podcast_script

        mock_provider = AsyncMock()
        mock_provider.generate.side_effect = ["Part 1", "Part 2"]

        paragraphs = ["A" * 50, "B" * 50]
        text = "\n\n".join(paragraphs)
        result = await generate_podcast_script(
            text, mock_provider, max_chunk_chars=60
        )
        assert "Part 1" in result
        assert "Part 2" in result
        assert mock_provider.generate.call_count == 2


class TestGeneratePodcastScriptErrorHandling:
    @pytest.mark.asyncio
    async def test_fallback_to_original_on_provider_error(self):
        from obsidian_podcast.llm.base import generate_podcast_script

        mock_provider = AsyncMock()
        mock_provider.generate.side_effect = RuntimeError("API error")

        result = await generate_podcast_script(
            "Some article text", mock_provider, max_chunk_chars=4000
        )
        assert result == "Some article text"


class TestSystemPrompt:
    def test_system_prompt_defined(self):
        from obsidian_podcast.llm.base import SYSTEM_PROMPT

        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0
