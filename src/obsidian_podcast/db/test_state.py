"""Tests for SQLite state management."""


import pytest


@pytest.fixture
def state_db(tmp_path):
    from obsidian_podcast.db.state import StateDB

    db_path = tmp_path / "state.db"
    db = StateDB(db_path)
    db.initialize()
    return db


class TestStateDB:
    def test_initialize_creates_table(self, state_db):
        """initialize() should create the articles table."""
        import sqlite3

        conn = sqlite3.connect(state_db.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_add_article(self, state_db):
        """Should insert an article and return its id."""
        article_id = state_db.add_article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
            title="Test Article",
        )
        assert article_id is not None
        assert isinstance(article_id, int)

    def test_add_duplicate_url_raises(self, state_db):
        """Duplicate URLs should raise an error."""
        state_db.add_article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
        )
        with pytest.raises(Exception):
            state_db.add_article(
                url="https://example.com/post",
                feed_url="https://example.com/feed.xml",
            )

    def test_get_article_by_url(self, state_db):
        """Should retrieve an article by URL."""
        state_db.add_article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
            title="Test",
        )
        article = state_db.get_article_by_url("https://example.com/post")
        assert article is not None
        assert article["title"] == "Test"
        assert article["status"] == "pending"

    def test_get_article_by_url_not_found(self, state_db):
        """Should return None for non-existent URL."""
        article = state_db.get_article_by_url("https://nonexistent.com")
        assert article is None

    def test_update_status(self, state_db):
        """Should update article status."""
        article_id = state_db.add_article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
        )
        state_db.update_status(article_id, "completed")
        article = state_db.get_article_by_url("https://example.com/post")
        assert article["status"] == "completed"

    def test_update_status_with_audio_url(self, state_db):
        """Should update status and audio_url."""
        article_id = state_db.add_article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
        )
        state_db.update_status(
            article_id, "completed", audio_url="https://cdn.example.com/audio.mp3"
        )
        article = state_db.get_article_by_url("https://example.com/post")
        assert article["audio_url"] == "https://cdn.example.com/audio.mp3"

    def test_update_status_with_error(self, state_db):
        """Should update status and error_message."""
        article_id = state_db.add_article(
            url="https://example.com/post",
            feed_url="https://example.com/feed.xml",
        )
        state_db.update_status(
            article_id, "failed", error_message="TTS failed"
        )
        article = state_db.get_article_by_url("https://example.com/post")
        assert article["status"] == "failed"
        assert article["error_message"] == "TTS failed"

    def test_list_articles_by_status(self, state_db):
        """Should filter articles by status."""
        state_db.add_article(
            url="https://example.com/1", feed_url="https://example.com/feed.xml"
        )
        aid2 = state_db.add_article(
            url="https://example.com/2", feed_url="https://example.com/feed.xml"
        )
        state_db.update_status(aid2, "completed")

        pending = state_db.list_articles(status="pending")
        assert len(pending) == 1
        assert pending[0]["url"] == "https://example.com/1"

        completed = state_db.list_articles(status="completed")
        assert len(completed) == 1
        assert completed[0]["url"] == "https://example.com/2"

    def test_list_all_articles(self, state_db):
        """Should list all articles when no status filter."""
        state_db.add_article(
            url="https://example.com/1", feed_url="https://example.com/feed.xml"
        )
        state_db.add_article(
            url="https://example.com/2", feed_url="https://example.com/feed.xml"
        )
        articles = state_db.list_articles()
        assert len(articles) == 2
