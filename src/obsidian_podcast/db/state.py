"""SQLite state management for article processing."""

import sqlite3
from pathlib import Path

CREATE_ARTICLES_TABLE = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    feed_url TEXT NOT NULL,
    title TEXT,
    author TEXT,
    published_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'pending',
    audio_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
)
"""


class StateDB:
    """SQLite-based state management for article processing."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        """Create the database schema."""
        with self._connect() as conn:
            conn.execute(CREATE_ARTICLES_TABLE)

    def add_article(
        self,
        url: str,
        feed_url: str,
        title: str | None = None,
        author: str | None = None,
        published_at: str | None = None,
    ) -> int:
        """Add an article and return its id."""
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO articles (url, feed_url, title, author, published_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (url, feed_url, title, author, published_at),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_article_by_url(self, url: str) -> dict | None:
        """Get an article by its URL."""
        with self._connect() as conn:
            cursor = conn.execute("SELECT * FROM articles WHERE url = ?", (url,))
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(row)

    def update_status(
        self,
        article_id: int,
        status: str,
        audio_url: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update the status of an article."""
        with self._connect() as conn:
            conn.execute(
                """UPDATE articles
                   SET status = ?, audio_url = ?, error_message = ?,
                       processed_at = CASE WHEN ? IN ('completed', 'failed')
                                           THEN CURRENT_TIMESTAMP ELSE processed_at END
                   WHERE id = ?""",
                (status, audio_url, error_message, status, article_id),
            )

    def list_articles(self, status: str | None = None) -> list[dict]:
        """List articles, optionally filtered by status."""
        with self._connect() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM articles WHERE status = ? ORDER BY created_at",
                    (status,),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM articles ORDER BY created_at"
                )
            return [dict(row) for row in cursor.fetchall()]
