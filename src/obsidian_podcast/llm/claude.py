"""Claude (Anthropic) LLM provider."""

import os

import anthropic

from obsidian_podcast.llm.base import LLMProvider, register_llm_engine


@register_llm_engine("claude")
class ClaudeLLMProvider(LLMProvider):
    """LLM provider using Anthropic Claude API."""

    def __init__(self, config) -> None:
        api_key = (
            os.environ.get(config.api_key_env, "")
            if config.api_key_env
            else None
        )
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = config.model

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using Anthropic Claude API."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.content:
            return ""
        return response.content[0].text
