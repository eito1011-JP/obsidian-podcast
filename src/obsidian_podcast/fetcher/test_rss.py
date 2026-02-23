"""Tests for RSS feed fetcher."""

from unittest.mock import AsyncMock, MagicMock

import pytest

# Sample RSS feed XML for testing
SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Blog</title>
    <link>https://example.com</link>
    <item>
      <title>Article One</title>
      <link>https://example.com/article-1</link>
      <author>author@example.com (Author One)</author>
      <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
      <description>Summary of article one</description>
    </item>
    <item>
      <title>Article Two</title>
      <link>https://example.com/article-2</link>
      <description>Summary of article two</description>
    </item>
  </channel>
</rss>
"""

SAMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Blog</title>
  <entry>
    <title>Atom Entry</title>
    <link href="https://example.com/atom-1"/>
    <author><name>Atom Author</name></author>
    <published>2024-01-01T00:00:00Z</published>
    <summary>Atom summary</summary>
  </entry>
</feed>
"""

SAMPLE_PODCAST_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Podcast</title>
    <item>
      <title>Episode 1</title>
      <link>https://example.com/ep1</link>
      <enclosure url="https://example.com/ep1.mp3"
                 type="audio/mpeg" length="12345"/>
      <description>Episode description</description>
    </item>
    <item>
      <title>Blog Post</title>
      <link>https://example.com/post1</link>
      <description>Regular post</description>
    </item>
  </channel>
</rss>
"""


class TestParseFeed:
    """Test feedparser-based RSS/Atom parsing."""

    def test_parse_rss_entries(self):
        from obsidian_podcast.fetcher.rss import parse_feed

        entries = parse_feed(SAMPLE_RSS, "https://example.com/feed.xml")
        assert len(entries) == 2
        assert entries[0].url == "https://example.com/article-1"
        assert entries[0].title == "Article One"
        assert entries[0].feed_url == "https://example.com/feed.xml"

    def test_parse_atom_entries(self):
        from obsidian_podcast.fetcher.rss import parse_feed

        entries = parse_feed(SAMPLE_ATOM, "https://atom.example.com/feed")
        assert len(entries) == 1
        assert entries[0].url == "https://example.com/atom-1"
        assert entries[0].title == "Atom Entry"

    def test_parse_podcast_rss_sets_audio_url(self):
        from obsidian_podcast.fetcher.rss import parse_feed

        entries = parse_feed(
            SAMPLE_PODCAST_RSS, "https://example.com/podcast.xml"
        )
        # Episode with enclosure
        ep = [e for e in entries if e.title == "Episode 1"][0]
        assert ep.audio_url == "https://example.com/ep1.mp3"
        assert ep.is_podcast is True

        # Regular post without enclosure
        post = [e for e in entries if e.title == "Blog Post"][0]
        assert post.audio_url is None
        assert post.is_podcast is False

    def test_parse_empty_feed(self):
        from obsidian_podcast.fetcher.rss import parse_feed

        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel><title>Empty</title></channel></rss>"""
        entries = parse_feed(xml, "https://example.com/feed.xml")
        assert entries == []

    def test_rss_description_stored(self):
        """RSS description/content is stored for fallback use."""
        from obsidian_podcast.fetcher.rss import parse_feed

        entries = parse_feed(SAMPLE_RSS, "https://example.com/feed.xml")
        assert entries[0].content == "Summary of article one"


class TestFilterNewArticles:
    """Test filtering articles against SQLite state."""

    def test_filters_already_processed(self, tmp_path):
        from obsidian_podcast.db.state import StateDB
        from obsidian_podcast.fetcher.rss import filter_new_articles, parse_feed

        db = StateDB(tmp_path / "test.db")
        db.initialize()
        db.add_article(
            url="https://example.com/article-1",
            feed_url="https://example.com/feed.xml",
        )

        articles = parse_feed(SAMPLE_RSS, "https://example.com/feed.xml")
        new = filter_new_articles(articles, db)
        assert len(new) == 1
        assert new[0].url == "https://example.com/article-2"

    def test_all_new_when_db_empty(self, tmp_path):
        from obsidian_podcast.db.state import StateDB
        from obsidian_podcast.fetcher.rss import filter_new_articles, parse_feed

        db = StateDB(tmp_path / "test.db")
        db.initialize()

        articles = parse_feed(SAMPLE_RSS, "https://example.com/feed.xml")
        new = filter_new_articles(articles, db)
        assert len(new) == 2


class TestFetchFeed:
    """Test async HTTP feed fetching."""

    @pytest.mark.asyncio
    async def test_fetch_feed_success(self):
        from obsidian_podcast.fetcher.rss import fetch_feed

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_RSS
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        articles = await fetch_feed(
            mock_client,
            "https://example.com/feed.xml",
        )
        assert len(articles) == 2
        mock_client.get.assert_called_once_with("https://example.com/feed.xml")

    @pytest.mark.asyncio
    async def test_fetch_feed_http_error(self):
        import httpx

        from obsidian_podcast.fetcher.rss import fetch_feed

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )
        )

        articles = await fetch_feed(
            mock_client,
            "https://example.com/bad-feed.xml",
        )
        assert articles == []

    @pytest.mark.asyncio
    async def test_fetch_feed_network_error(self):
        import httpx

        from obsidian_podcast.fetcher.rss import fetch_feed

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        articles = await fetch_feed(
            mock_client,
            "https://example.com/feed.xml",
        )
        assert articles == []
