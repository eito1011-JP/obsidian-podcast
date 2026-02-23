"""Tests for async pipeline skeleton."""

import pytest


@pytest.mark.asyncio
async def test_pipeline_step_interface():
    """PipelineStep should define process method."""
    from obsidian_podcast.pipeline import PipelineStep

    class UpperStep(PipelineStep[str, str]):
        async def process(self, input_data: str) -> str:
            return input_data.upper()

    step = UpperStep()
    result = await step.process("hello")
    assert result == "HELLO"


@pytest.mark.asyncio
async def test_pipeline_run_single_step():
    """Pipeline with one step should process input."""
    from obsidian_podcast.pipeline import Pipeline, PipelineStep

    class DoubleStep(PipelineStep[int, int]):
        async def process(self, input_data: int) -> int:
            return input_data * 2

    pipeline = Pipeline(steps=[DoubleStep()])
    result = await pipeline.run(5)
    assert result == 10


@pytest.mark.asyncio
async def test_pipeline_run_chained_steps():
    """Pipeline should chain multiple steps."""
    from obsidian_podcast.pipeline import Pipeline, PipelineStep

    class AddOneStep(PipelineStep[int, int]):
        async def process(self, input_data: int) -> int:
            return input_data + 1

    class DoubleStep(PipelineStep[int, int]):
        async def process(self, input_data: int) -> int:
            return input_data * 2

    pipeline = Pipeline(steps=[AddOneStep(), DoubleStep()])
    result = await pipeline.run(3)
    # (3 + 1) * 2 = 8
    assert result == 8


@pytest.mark.asyncio
async def test_pipeline_empty():
    """Pipeline with no steps should return input unchanged."""
    from obsidian_podcast.pipeline import Pipeline

    pipeline = Pipeline(steps=[])
    result = await pipeline.run("unchanged")
    assert result == "unchanged"


@pytest.mark.asyncio
async def test_pipeline_step_is_abstract():
    """PipelineStep should not be instantiable directly."""
    from obsidian_podcast.pipeline import PipelineStep

    with pytest.raises(TypeError):
        PipelineStep()  # type: ignore[abstract]


class TestLLMScriptStep:
    @pytest.mark.asyncio
    async def test_process_with_mock_provider(self):
        from unittest.mock import AsyncMock

        from obsidian_podcast.pipeline import LLMScriptStep

        mock_provider = AsyncMock()
        mock_provider.generate.return_value = "Podcast script output"

        step = LLMScriptStep(provider=mock_provider, max_chunk_chars=4000)
        result = await step.process("Article text here")
        assert result == "Podcast script output"

    @pytest.mark.asyncio
    async def test_in_pipeline(self):
        from unittest.mock import AsyncMock

        from obsidian_podcast.pipeline import LLMScriptStep, Pipeline

        mock_provider = AsyncMock()
        mock_provider.generate.return_value = "Transformed"

        step = LLMScriptStep(provider=mock_provider)
        pipeline = Pipeline(steps=[step])
        result = await pipeline.run("Input text")
        assert result == "Transformed"
