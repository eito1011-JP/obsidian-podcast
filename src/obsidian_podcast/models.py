"""Common data models for Obsidian Podcast."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ProcessingStatus(StrEnum):
    """Status of article processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FeedConfig:
    """Configuration for an RSS feed."""

    url: str
    name: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    type: str = "article"


@dataclass
class Article:
    """An article extracted from an RSS feed."""

    url: str
    feed_url: str
    title: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    audio_url: str | None = None
    error_message: str | None = None
    content: str | None = None
    is_full_text: bool = True
    language: str | None = None
    is_podcast: bool = False
