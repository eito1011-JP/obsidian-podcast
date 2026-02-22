"""Async pipeline skeleton for article processing."""

from abc import ABC, abstractmethod
from typing import Any


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
