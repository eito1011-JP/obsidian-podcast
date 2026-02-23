"""OpenAI-compatible LLM provider (also works with Ollama)."""

import os

import openai

from obsidian_podcast.llm.base import LLMProvider, register_llm_engine


@register_llm_engine("openai")
class OpenAILLMProvider(LLMProvider):
    """LLM provider using OpenAI-compatible API."""

    def __init__(self, config) -> None:
        api_key = (
            os.environ.get(config.api_key_env, "")
            if config.api_key_env
            else "ollama"
        )
        kwargs: dict = {"api_key": api_key}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self.client = openai.AsyncOpenAI(**kwargs)
        self.model = config.model

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using OpenAI-compatible API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        if not response.choices:
            return ""
        return response.choices[0].message.content or ""
