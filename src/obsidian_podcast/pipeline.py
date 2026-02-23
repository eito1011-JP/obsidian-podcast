"""Async pipeline skeleton for article processing."""

from abc import ABC, abstractmethod
from typing import Any

from obsidian_podcast.llm.base import LLMProvider, generate_podcast_script


class PipelineStep[T, U](ABC):
    """Abstract base class for a pipeline processing step."""

    @abstractmethod
    async def process(self, input_data: T) -> U:
        """Process input data and return output."""
        ...


class Pipeline:
    """Chain of PipelineStep instances executed sequentially."""

    def __init__(self, steps: list[PipelineStep[Any, Any]]) -> None:
        self.steps = steps

    async def run(self, input_data: Any) -> Any:
        """Run all steps in sequence, passing output of each to the next."""
        result = input_data
        for step in self.steps:
            result = await step.process(result)
        return result


class LLMScriptStep(PipelineStep[str, str]):
    """Pipeline step that converts text to podcast script using LLM."""

    def __init__(
        self, provider: LLMProvider, max_chunk_chars: int = 4000
    ) -> None:
        self.provider = provider
        self.max_chunk_chars = max_chunk_chars

    async def process(self, input_data: str) -> str:
        """Convert article text to podcast script."""
        return await generate_podcast_script(
            input_data, self.provider, self.max_chunk_chars
        )
