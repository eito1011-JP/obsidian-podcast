"""Text preprocessing for TTS output."""

import re

from bs4 import BeautifulSoup
from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

# Make langdetect deterministic
DetectorFactory.seed = 0

CODE_ANNOUNCE_TEXT = "(コード省略)"


def remove_images(html: str) -> str:
    """Remove img and figure tags from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["img", "figure"]):
        tag.decompose()
    return str(soup)


def handle_code_blocks(html: str, mode: str = "skip") -> str:
    """Handle code blocks according to the specified mode.

    Modes:
        skip: Remove code blocks entirely (default)
        announce: Replace with announcement text
        read: Keep code as-is
    """
    soup = BeautifulSoup(html, "html.parser")

    if mode == "read":
        return str(soup)

    for tag in soup.find_all("pre"):
        if mode == "skip":
            tag.decompose()
        elif mode == "announce":
            new_tag = soup.new_tag("p")
            new_tag.string = CODE_ANNOUNCE_TEXT
            tag.replace_with(new_tag)

    return str(soup)


def table_to_text(html: str) -> str:
    """Convert HTML tables to readable text representation."""
    soup = BeautifulSoup(html, "html.parser")

    for table in soup.find_all("table"):
        rows: list[str] = []
        for tr in table.find_all("tr"):
            cells = [
                td.get_text(strip=True)
                for td in tr.find_all(["td", "th"])
            ]
            rows.append(" | ".join(cells))
        text_repr = "\n".join(rows)
        table.replace_with(text_repr)

    return str(soup)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace and newlines."""
    # Collapse multiple spaces/tabs to single space
    text = re.sub(r"[^\S\n]+", " ", text)
    # Collapse 3+ newlines to double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()


def detect_language(text: str) -> str | None:
    """Detect the language of the given text.

    Returns ISO 639-1 language code or None on failure.
    """
    if not text or not text.strip():
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None


def preprocess(html: str, code_block_handling: str = "skip") -> str:
    """Run the full preprocessing pipeline on HTML content.

    Steps:
    1. Handle code blocks
    2. Remove images
    3. Convert tables to text
    4. Extract text from HTML
    5. Normalize whitespace
    """
    result = handle_code_blocks(html, code_block_handling)
    result = remove_images(result)
    result = table_to_text(result)
    # Extract plain text from remaining HTML
    soup = BeautifulSoup(result, "html.parser")
    text = soup.get_text(separator="\n")
    text = normalize_whitespace(text)
    return text
