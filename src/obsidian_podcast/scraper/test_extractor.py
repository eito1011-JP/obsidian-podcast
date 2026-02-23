"""Tests for article content extractor."""

from unittest.mock import AsyncMock, MagicMock

import pytest

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Article</title></head>
<body>
<nav>Navigation menu</nav>
<article>
<h1>Test Article Title</h1>
<p>This is the main content of the article. It contains several paragraphs
of meaningful text that should be extracted by readability.</p>
<p>Second paragraph with more content to make readability happy.
The algorithm needs enough text to properly identify main content.</p>
<p>Third paragraph continues with additional information about the topic.
More text helps readability distinguish content from boilerplate.</p>
</article>
<footer>Footer content</footer>
</body>
</html>
"""

MINIMAL_HTML = """
<html><body><p>Short content</p></body></html>
"""


class TestExtractContent:
    """Test readability-based content extraction."""

    def test_extract_from_html(self):
        from obsidian_podcast.scraper.extractor import extract_content

        content = extract_content(SAMPLE_HTML)
        assert content is not None
        # Main content should be present
        assert "main content" in content

    def test_extract_returns_html_string(self):
        from obsidian_podcast.scraper.extractor import extract_content

        content = extract_content(SAMPLE_HTML)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_extract_from_empty_html_returns_none(self):
        from obsidian_podcast.scraper.extractor import extract_content

        content = extract_content("")
        assert content is None

    def test_extract_from_invalid_html_returns_none(self):
        from obsidian_podcast.scraper.extractor import extract_content

        content = extract_content("not html at all")
        # Should not crash; may return something or None
        # The key is it doesn't raise
        assert content is None or isinstance(content, str)


class TestScrapeArticle:
    """Test async article scraping with fallback."""

    @pytest.mark.asyncio
    async def test_scrape_success_sets_full_text(self):
        from obsidian_podcast.models import Article
        from obsidian_podcast.scraper.extractor import scrape_article

        article = Article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
            content="RSS summary fallback",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await scrape_article(mock_client, article)
        assert result.is_full_text is True
        assert result.content is not None
        assert "main content" in result.content

    @pytest.mark.asyncio
    async def test_scrape_failure_falls_back_to_rss(self):
        import httpx

        from obsidian_podcast.models import Article
        from obsidian_podcast.scraper.extractor import scrape_article

        article = Article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
            content="RSS summary fallback",
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "403",
                request=MagicMock(),
                response=MagicMock(status_code=403),
            )
        )

        result = await scrape_article(mock_client, article)
        assert result.is_full_text is False
        assert result.content == "RSS summary fallback"

    @pytest.mark.asyncio
    async def test_scrape_network_error_falls_back(self):
        import httpx

        from obsidian_podcast.models import Article
        from obsidian_podcast.scraper.extractor import scrape_article

        article = Article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
            content="RSS fallback",
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        result = await scrape_article(mock_client, article)
        assert result.is_full_text is False
        assert result.content == "RSS fallback"

    @pytest.mark.asyncio
    async def test_scrape_no_fallback_content(self):
        """When scraping fails and no RSS content, content stays None."""
        import httpx

        from obsidian_podcast.models import Article
        from obsidian_podcast.scraper.extractor import scrape_article

        article = Article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
            content=None,
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("fail")
        )

        result = await scrape_article(mock_client, article)
        assert result.is_full_text is False
        assert result.content is None

    @pytest.mark.asyncio
    async def test_podcast_article_skipped(self):
        """Podcast articles should be skipped (no scraping)."""
        from obsidian_podcast.models import Article
        from obsidian_podcast.scraper.extractor import scrape_article

        article = Article(
            url="https://example.com/ep1",
            feed_url="https://example.com/feed.xml",
            audio_url="https://example.com/ep1.mp3",
            is_podcast=True,
        )

        mock_client = AsyncMock()
        result = await scrape_article(mock_client, article)
        # Should return as-is without making HTTP request
        assert result.is_podcast is True
        mock_client.get.assert_not_called()
