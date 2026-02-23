"""Article content extraction using readability-lxml."""

import logging

import httpx
from readability import Document

from obsidian_podcast.models import Article

logger = logging.getLogger(__name__)


def extract_content(html: str) -> str | None:
    """Extract main content from HTML using readability-lxml.

    Returns the extracted HTML content string, or None if extraction fails.
    """
    if not html or not html.strip():
        return None

    try:
        doc = Document(html)
        content = doc.summary()
        # readability wraps in <html><body>; extract inner content
        if not content or len(content.strip()) < 10:
            return None
        return content
    except Exception:
        logger.warning("readability extraction failed", exc_info=True)
        return None


async def scrape_article(
    client: httpx.AsyncClient,
    article: Article,
) -> Article:
    """Scrape full article content from its URL.

    On success, sets article.content and article.is_full_text = True.
    On failure, keeps existing RSS content and sets is_full_text = False.
    Podcast articles are skipped entirely.
    """
    if article.is_podcast:
        return article

    rss_fallback = article.content

    try:
        response = await client.get(article.url)
        response.raise_for_status()
        extracted = extract_content(response.text)
        if extracted:
            article.content = extracted
            article.is_full_text = True
            return article
    except (
        httpx.HTTPStatusError,
        httpx.ConnectError,
        httpx.TimeoutException,
    ) as e:
        logger.warning(
            "Failed to scrape %s: %s", article.url, e
        )

    # Fallback to RSS content
    article.content = rss_fallback
    article.is_full_text = False
    return article
