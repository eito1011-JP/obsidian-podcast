"""RSS/Atom feed fetching and parsing."""

import logging

import feedparser
import httpx

from obsidian_podcast.db.state import StateDB
from obsidian_podcast.models import Article

logger = logging.getLogger(__name__)


def parse_feed(xml_content: str, feed_url: str) -> list[Article]:
    """Parse RSS/Atom XML content and return Article objects.

    Stores RSS description/content in Article.content for fallback use.
    Detects podcast entries by the presence of enclosure tags.
    """
    feed = feedparser.parse(xml_content)
    articles: list[Article] = []

    for entry in feed.entries:
        url = entry.get("link", "")
        if not url:
            continue

        title = entry.get("title")
        author = entry.get("author")

        # Extract description/content for fallback
        content = None
        if entry.get("content"):
            # Atom content (list of dicts)
            content = entry.content[0].get("value", "")
        elif entry.get("summary"):
            content = entry.summary
        elif entry.get("description"):
            content = entry.description

        # Detect podcast: check for enclosure with audio
        audio_url = None
        is_podcast = False
        enclosures = entry.get("enclosures", [])
        for enc in enclosures:
            enc_url = enc.get("href", enc.get("url", ""))
            enc_type = enc.get("type", "")
            if enc_url and (
                enc_type.startswith("audio/") or enc_url.endswith(".mp3")
            ):
                audio_url = enc_url
                is_podcast = True
                break

        article = Article(
            url=url,
            feed_url=feed_url,
            title=title,
            author=author,
            content=content,
            audio_url=audio_url,
            is_podcast=is_podcast,
        )
        articles.append(article)

    return articles


def filter_new_articles(
    articles: list[Article], db: StateDB
) -> list[Article]:
    """Filter out articles that are already in the database."""
    return [a for a in articles if db.get_article_by_url(a.url) is None]


async def fetch_feed(
    client: httpx.AsyncClient,
    feed_url: str,
) -> list[Article]:
    """Fetch and parse an RSS/Atom feed via HTTP.

    Returns parsed articles on success, empty list on error.
    """
    try:
        response = await client.get(feed_url)
        response.raise_for_status()
        return parse_feed(response.text, feed_url)
    except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
        logger.warning("Failed to fetch feed %s: %s", feed_url, e)
        return []
