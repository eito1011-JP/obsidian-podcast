"""Tests for data models: Article, FeedConfig, ProcessingStatus."""

from datetime import datetime


class TestProcessingStatus:
    def test_enum_values(self):
        from obsidian_podcast.models import ProcessingStatus

        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"

    def test_from_string(self):
        from obsidian_podcast.models import ProcessingStatus

        assert ProcessingStatus("pending") == ProcessingStatus.PENDING
        assert ProcessingStatus("completed") == ProcessingStatus.COMPLETED


class TestFeedConfig:
    def test_minimal_creation(self):
        from obsidian_podcast.models import FeedConfig

        feed = FeedConfig(url="https://example.com/feed.xml")
        assert feed.url == "https://example.com/feed.xml"
        assert feed.name == ""
        assert feed.category == ""
        assert feed.tags == []
        assert feed.type == "article"

    def test_full_creation(self):
        from obsidian_podcast.models import FeedConfig

        feed = FeedConfig(
            url="https://example.com/feed.xml",
            name="Example Feed",
            category="tech",
            tags=["python", "ai"],
            type="podcast",
        )
        assert feed.name == "Example Feed"
        assert feed.category == "tech"
        assert feed.tags == ["python", "ai"]
        assert feed.type == "podcast"


class TestArticle:
    def test_minimal_creation(self):
        from obsidian_podcast.models import Article, ProcessingStatus

        article = Article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
        )
        assert article.url == "https://example.com/post"
        assert article.feed_url == "https://example.com/feed.xml"
        assert article.title is None
        assert article.author is None
        assert article.published_at is None
        assert article.status == ProcessingStatus.PENDING
        assert article.audio_url is None
        assert article.error_message is None

    def test_full_creation(self):
        from obsidian_podcast.models import Article, ProcessingStatus

        now = datetime.now()
        article = Article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
            title="Test Article",
            author="Author",
            published_at=now,
            status=ProcessingStatus.COMPLETED,
            audio_url="https://cdn.example.com/audio.mp3",
        )
        assert article.title == "Test Article"
        assert article.status == ProcessingStatus.COMPLETED
        assert article.audio_url == "https://cdn.example.com/audio.mp3"
