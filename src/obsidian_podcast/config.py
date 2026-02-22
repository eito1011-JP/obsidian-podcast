"""Configuration management: pydantic models + YAML loading, XDG compliant."""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

APP_NAME = "obsidian-podcast"


class FeedConfigModel(BaseModel):
    """Configuration for a single RSS feed."""

    url: str
    name: str = ""
    category: str = ""
    tags: list[str] = Field(default_factory=list)
    type: str = "article"


class TTSConfig(BaseModel):
    """TTS engine configuration."""

    engine: str = "edge-tts"
    language_detection: bool = True
    code_block_handling: str = "skip"


class StorageConfig(BaseModel):
    """Storage configuration."""

    type: str = "cloudflare-r2"
    bucket: str = ""
    public_url: str = ""


class ObsidianConfig(BaseModel):
    """Obsidian vault configuration."""

    vault_path: str = ""
    output_dir: str = "Podcast"
    folder_structure: str = "monthly"


class SummaryConfig(BaseModel):
    """Summary generation configuration."""

    enabled: bool = False
    engine: str = "ollama"
    model: str = "llama3"


class AppConfig(BaseModel):
    """Root application configuration."""

    feeds: list[FeedConfigModel] = Field(default_factory=list)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    obsidian: ObsidianConfig = Field(default_factory=ObsidianConfig)
    summary: SummaryConfig = Field(default_factory=SummaryConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        """Load configuration from a YAML file."""
        if not path.exists():
            msg = f"Configuration file not found: {path}"
            raise FileNotFoundError(msg)
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)


def get_config_dir() -> Path:
    """Get the XDG-compliant configuration directory."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        base = Path(xdg_config)
    else:
        base = Path.home() / ".config"
    return base / APP_NAME


def generate_default_config(path: Path) -> None:
    """Generate a default configuration YAML file."""
    config = AppConfig()
    data = config.model_dump()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
