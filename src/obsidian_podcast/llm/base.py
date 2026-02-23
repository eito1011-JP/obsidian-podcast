"""LLM provider base class, registry, and podcast script generation."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from obsidian_podcast.config import LLMConfig

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "あなたはラジオDJです。"
    "与えられた記事テキストを、日本語TTSで読み上げるための台本に変換してください。\n\n"
    "【最重要ルール：TTS音声合成向けの表記】\n"
    "出力は日本語TTSエンジンがそのまま読み上げます。以下を厳守してください：\n\n"
    "1. 英語・アルファベットは全てカタカナに変換する（英語を一切残さない）\n"
    "   - Next.js → ネクストジェーエス\n"
    "   - App Router → アップルーター\n"
    "   - React → リアクト\n"
    "   - Turbopack → ターボパック\n"
    "   - Webpack → ウェブパック\n"
    "   - Server Actions → サーバーアクションズ\n"
    "   - Rust → ラスト\n"
    "   - JavaScript → ジャバスクリプト\n"
    "2. 記号は使わない\n"
    "   - 「!」「?」「#」「*」「`」は全て削除するか日本語に置き換える\n"
    "   - 感嘆は「。」で終わらせ、語調で表現する\n"
    "   - 疑問は「〜でしょうか」「〜ですよね」で表現する\n"
    "3. コードブロックはそのまま書かず、内容を日本語で説明する\n"
    "4. 数字はそのまま使ってよい（例: 15、10倍）\n"
    "5. 絵文字は使わない\n\n"
    "【台本スタイル】\n"
    "- 箇条書きは自然な話し言葉に変換する\n"
    "- 見出しは話題の転換として自然に導入する\n"
    "- 聞き手に語りかける口調で、親しみやすいトーンにする\n"
    "- 元の情報は正確に保つ\n"
    "- 「それでは」「さて」などの接続詞で段落間をつなぐ"
)

_registry: dict[str, type[LLMProvider]] = {}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text from a prompt."""
        ...


def register_llm_engine(name: str):
    """Decorator to register an LLM provider class."""

    def decorator(cls: type[LLMProvider]) -> type[LLMProvider]:
        _registry[name] = cls
        return cls

    return decorator


def create_llm_engine(config: LLMConfig) -> LLMProvider:
    """Create an LLM provider instance from config."""
    if config.engine not in _registry:
        available = list(_registry.keys())
        msg = f"Unknown LLM engine: {config.engine}. Available: {available}"
        raise ValueError(msg)
    return _registry[config.engine](config)


def split_text_for_llm(text: str, max_chars: int = 4000) -> list[str]:
    """Split text into chunks for LLM processing.

    Strategy: split by paragraphs first, then by sentences if needed.
    """
    if not text or not text.strip():
        return []

    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current_chunk = ""

    for para in paragraphs:
        if not para.strip():
            continue

        if len(current_chunk) + len(para) + 2 <= max_chars:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append(current_chunk)

            if len(para) <= max_chars:
                current_chunk = para
            else:
                # Split long paragraph by sentences
                sentences = (
                    para.replace("。", "。\n").replace(". ", ".\n").split("\n")
                )
                current_chunk = ""
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    if len(current_chunk) + len(sentence) + 1 <= max_chars:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


async def generate_podcast_script(
    text: str,
    provider: LLMProvider,
    max_chunk_chars: int = 4000,
) -> str:
    """Convert article text to podcast script using LLM."""
    chunks = split_text_for_llm(text, max_chars=max_chunk_chars)

    if not chunks:
        return text

    results: list[str] = []
    for chunk in chunks:
        try:
            result = await provider.generate(chunk, system_prompt=SYSTEM_PROMPT)
            results.append(result)
        except Exception:
            logger.warning(
                "LLM generation failed for chunk, using original text",
                exc_info=True,
            )
            results.append(chunk)

    return "\n\n".join(results)
