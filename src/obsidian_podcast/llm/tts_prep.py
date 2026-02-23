"""TTS pre-processing: sanitize LLM output for Japanese TTS engines.

Japanese TTS engines (edge-tts etc.) misread certain characters:
- "!" → "アクサングラーブ" (French reading)
- English words → garbled pronunciation
- Markdown syntax → read literally

This module provides a sanitization layer between LLM output and TTS input.
"""

from __future__ import annotations

import re
import unicodedata

import alkana

# Tech terms that alkana doesn't know and phonetic fallback mangles.
# Users can extend this via config in the future.
_TECH_TERMS: dict[str, str] = {
    "Turbopack": "ターボパック",
    "turbopack": "ターボパック",
    "Webpack": "ウェブパック",
    "webpack": "ウェブパック",
    "TypeScript": "タイプスクリプト",
    "typescript": "タイプスクリプト",
    "JavaScript": "ジャバスクリプト",
    "javascript": "ジャバスクリプト",
    "GitHub": "ギットハブ",
    "github": "ギットハブ",
    "Vue": "ビュー",
    "vue": "ビュー",
    "Svelte": "スベルト",
    "svelte": "スベルト",
    "Vite": "ヴィート",
    "vite": "ヴィート",
    "Nuxt": "ナクスト",
    "nuxt": "ナクスト",
    "Vercel": "バーセル",
    "vercel": "バーセル",
    "Deno": "ディーノ",
    "deno": "ディーノ",
    "Bun": "バン",
    "bun": "バン",
    "Remix": "リミックス",
    "remix": "リミックス",
    "Astro": "アストロ",
    "astro": "アストロ",
    "GraphQL": "グラフキューエル",
    "Prisma": "プリズマ",
    "prisma": "プリズマ",
    "Docker": "ドッカー",
    "docker": "ドッカー",
    "Kubernetes": "クバネティス",
    "kubernetes": "クバネティス",
    "Tailwind": "テイルウインド",
    "tailwind": "テイルウインド",
    "Rust": "ラスト",
    "Python": "パイソン",
    "python": "パイソン",
    "Golang": "ゴーラング",
    "golang": "ゴーラング",
    "Node": "ノード",
    "npm": "エヌピーエム",
    "pnpm": "ピーエヌピーエム",
    "yarn": "ヤーン",
    "API": "エーピーアイ",
    "CSS": "シーエスエス",
    "HTML": "エイチティーエムエル",
    "URL": "ユーアールエル",
    "JSON": "ジェイソン",
    "YAML": "ヤムル",
    "SQL": "エスキューエル",
    "CLI": "シーエルアイ",
    "SDK": "エスディーケー",
    "SSR": "エスエスアール",
    "SSG": "エスエスジー",
    "ISR": "アイエスアール",
    "RSC": "アールエスシー",
    "App": "アップ",
    "app": "アップ",
    "Router": "ルーター",
    "router": "ルーター",
    "UI": "ユーアイ",
    "UX": "ユーエックス",
    "OS": "オーエス",
    "IoT": "アイオーティー",
    "AI": "エーアイ",
    "LLM": "エルエルエム",
    "ORM": "オーアールエム",
    "SPA": "エスピーエー",
    "PWA": "ピーダブリューエー",
    "CDN": "シーディーエヌ",
    "CI": "シーアイ",
    "CD": "シーディー",
    "PR": "プルリクエスト",
    "AWS": "エーダブリューエス",
    "GCP": "ジーシーピー",
    "Azure": "アジュール",
    "Next": "ネクスト",
    "next": "ネクスト",
    "js": "ジェーエス",
    "JS": "ジェーエス",
    "ts": "ティーエス",
    "TS": "ティーエス",
}


def remove_tts_unsafe_chars(text: str) -> str:
    """Remove characters that cause TTS mispronunciation."""
    # Remove code fences and their content
    text = re.sub(r"```[\s\S]*?```", "", text)

    # Remove inline code backticks
    text = text.replace("`", "")

    # Remove markdown heading markers
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Remove bold/italic markers
    text = re.sub(r"\*+", "", text)

    # Remove exclamation marks (full-width and half-width)
    text = text.replace("！", "").replace("!", "")

    # Remove question marks (full-width and half-width)
    text = text.replace("？", "").replace("?", "")

    # Remove emoji (Unicode emoji ranges)
    text = _remove_emoji(text)

    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def _remove_emoji(text: str) -> str:
    """Remove emoji characters from text."""
    return "".join(
        c for c in text if unicodedata.category(c) not in ("So", "Sk")
    )


# Basic English letter/digraph to katakana phonetic mapping for unknown words.
# Applied left-to-right, longer patterns first.
_PHONETIC_MAP = [
    ("tion", "ション"),
    ("sion", "ジョン"),
    ("ck", "ック"),
    ("th", "ス"),
    ("sh", "シュ"),
    ("ch", "チ"),
    ("ph", "フ"),
    ("wh", "ウ"),
    ("ght", "ト"),
    ("ng", "ング"),
    ("qu", "クウ"),
    ("oo", "ウー"),
    ("ee", "イー"),
    ("ea", "イー"),
    ("ou", "アウ"),
    ("ai", "エイ"),
    ("ei", "エイ"),
    ("oi", "オイ"),
    ("au", "オー"),
    ("aw", "オー"),
    ("ow", "オウ"),
    ("er", "アー"),
    ("ar", "アー"),
    ("or", "オー"),
    ("ur", "アー"),
    ("ir", "アー"),
    ("a", "ア"),
    ("b", "ブ"),
    ("c", "ク"),
    ("d", "ド"),
    ("e", "エ"),
    ("f", "フ"),
    ("g", "グ"),
    ("h", "ハ"),
    ("i", "イ"),
    ("j", "ジ"),
    ("k", "ク"),
    ("l", "ル"),
    ("m", "ム"),
    ("n", "ン"),
    ("o", "オ"),
    ("p", "プ"),
    ("r", "ル"),
    ("s", "ス"),
    ("t", "ト"),
    ("u", "ウ"),
    ("v", "ブ"),
    ("w", "ウ"),
    ("x", "クス"),
    ("y", "イ"),
    ("z", "ズ"),
]


def _phonetic_fallback(word: str) -> str:
    """Convert unknown English word to katakana using phonetic rules."""
    lower = word.lower()
    result = []
    i = 0
    while i < len(lower):
        matched = False
        for pattern, kana in _PHONETIC_MAP:
            if lower[i:].startswith(pattern):
                result.append(kana)
                i += len(pattern)
                matched = True
                break
        if not matched:
            result.append(lower[i])
            i += 1
    return "".join(result)


def english_to_katakana(text: str) -> str:
    """Convert English words in text to katakana.

    Uses alkana dictionary for known words, phonetic fallback for unknown.
    """
    def replace_match(m: re.Match) -> str:
        word = m.group(0)
        # Try tech terms dictionary first
        if word in _TECH_TERMS:
            return _TECH_TERMS[word]
        # Try alkana dictionary
        kana = alkana.get_kana(word)
        if kana:
            return kana
        # Try lowercase
        kana = alkana.get_kana(word.lower())
        if kana:
            return kana
        # Phonetic fallback
        return _phonetic_fallback(word)

    # Match sequences of ASCII letters (English words)
    return re.sub(r"[a-zA-Z]+", replace_match, text)


def add_tts_pauses(text: str) -> str:
    """Insert pauses after sentence-ending punctuation for natural TTS rhythm.

    edge-tts treats newlines as breath pauses. By ensuring each sentence
    ends with a newline, we get natural breaks between sentences.
    """
    # Add newline after 。if not already followed by one
    text = re.sub(r"。(?!\n)", "。\n", text)
    # Clean up excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def sanitize_for_tts(text: str) -> str:
    """Full sanitization pipeline: unsafe chars removal + English to katakana.

    This is the main entry point. Call this on LLM output before passing to TTS.
    """
    if not text:
        return ""

    text = remove_tts_unsafe_chars(text)
    text = english_to_katakana(text)

    # Remove any remaining dots that aren't part of numbers (e.g., 3.14)
    text = re.sub(r"(?<![0-9])\.(?![0-9])", "", text)

    # Add pauses for natural speech rhythm
    text = add_tts_pauses(text)

    return text.strip()
