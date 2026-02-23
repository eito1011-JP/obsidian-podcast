"""Tests for config management: pydantic + YAML, XDG compliance."""


import pytest
import yaml


class TestAppConfig:
    def test_default_config(self):
        from obsidian_podcast.config import AppConfig

        config = AppConfig()
        assert config.feeds == []
        assert config.tts.engine == "edge-tts"
        assert config.tts.language_detection is True
        assert config.tts.code_block_handling == "skip"
        assert config.obsidian.output_dir == "Podcast"
        assert config.obsidian.folder_structure == "monthly"
        assert config.summary.enabled is False

    def test_feeds_config(self):
        from obsidian_podcast.config import AppConfig, FeedConfigModel

        config = AppConfig(
            feeds=[
                FeedConfigModel(
                    url="https://example.com/feed.xml",
                    name="Example",
                    category="tech",
                    tags=["python"],
                )
            ]
        )
        assert len(config.feeds) == 1
        assert config.feeds[0].url == "https://example.com/feed.xml"
        assert config.feeds[0].type == "article"

    def test_from_yaml(self, tmp_path):
        from obsidian_podcast.config import AppConfig

        yaml_content = {
            "feeds": [
                {
                    "url": "https://example.com/feed.xml",
                    "name": "Test Feed",
                    "category": "tech",
                    "tags": ["python"],
                }
            ],
            "tts": {"engine": "edge-tts"},
            "obsidian": {"vault_path": "/tmp/vault", "output_dir": "Audio"},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(yaml_content))

        config = AppConfig.from_yaml(config_file)
        assert len(config.feeds) == 1
        assert config.obsidian.output_dir == "Audio"

    def test_from_yaml_missing_file(self, tmp_path):
        from obsidian_podcast.config import AppConfig

        missing = tmp_path / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            AppConfig.from_yaml(missing)


class TestConfigPaths:
    def test_default_config_dir(self, monkeypatch, tmp_path):
        from obsidian_podcast.config import get_config_dir

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_dir = get_config_dir()
        assert config_dir == tmp_path / "obsidian-podcast"

    def test_xdg_fallback(self, monkeypatch, tmp_path):
        from obsidian_podcast.config import get_config_dir

        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        config_dir = get_config_dir()
        assert config_dir == tmp_path / ".config" / "obsidian-podcast"

    def test_generate_default_config(self, tmp_path):
        from obsidian_podcast.config import generate_default_config

        config_path = tmp_path / "config.yaml"
        generate_default_config(config_path)
        assert config_path.exists()

        with open(config_path) as f:
            data = yaml.safe_load(f)
        assert "feeds" in data
        assert "tts" in data
        assert "obsidian" in data


class TestLLMConfig:
    def test_llm_config_defaults(self):
        from obsidian_podcast.config import LLMConfig

        config = LLMConfig()
        assert config.enabled is False
        assert config.engine == "openai"
        assert config.model == "qwen2.5"
        assert config.api_key_env == ""
        assert config.base_url is None
        assert config.max_chunk_chars == 4000

    def test_app_config_has_llm_field(self):
        from obsidian_podcast.config import AppConfig, LLMConfig

        config = AppConfig()
        assert isinstance(config.llm, LLMConfig)
        assert config.llm.enabled is False

    def test_llm_config_from_yaml(self, tmp_path):
        from obsidian_podcast.config import AppConfig

        yaml_content = {
            "llm": {
                "enabled": True,
                "engine": "claude",
                "model": "claude-sonnet-4-20250514",
                "api_key_env": "ANTHROPIC_API_KEY",
                "base_url": "https://api.anthropic.com",
                "max_chunk_chars": 8000,
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(yaml_content))

        config = AppConfig.from_yaml(config_file)
        assert config.llm.enabled is True
        assert config.llm.engine == "claude"
        assert config.llm.model == "claude-sonnet-4-20250514"
        assert config.llm.api_key_env == "ANTHROPIC_API_KEY"
        assert config.llm.base_url == "https://api.anthropic.com"
        assert config.llm.max_chunk_chars == 8000
