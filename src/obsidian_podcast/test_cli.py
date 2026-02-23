"""Tests for CLI commands."""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    def test_help(self, runner):
        from obsidian_podcast.cli import app

        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "obsidian-podcast" in result.output.lower() or "Usage" in result.output

    def test_init_creates_config(self, runner, tmp_path, monkeypatch):
        from obsidian_podcast.cli import app

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        config_file = tmp_path / "obsidian-podcast" / "config.yaml"
        assert config_file.exists()

    def test_init_does_not_overwrite(self, runner, tmp_path, monkeypatch):
        from obsidian_podcast.cli import app

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        # First init
        runner.invoke(app, ["init"])
        # Second init should warn
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        output = result.output.lower()
        assert "already exists" in output or "exists" in output

    def test_run_stub(self, runner):
        from obsidian_podcast.cli import app

        result = runner.invoke(app, ["run"])
        assert result.exit_code == 0
        assert "stub" in result.output.lower() or "pipeline" in result.output.lower()

    def test_run_with_feed_option(self, runner):
        from obsidian_podcast.cli import app

        result = runner.invoke(app, ["run", "--feed", "https://example.com/feed.xml"])
        assert result.exit_code == 0

    def test_run_with_config_option(self, runner, tmp_path):
        from obsidian_podcast.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text("feeds: []\n")
        result = runner.invoke(app, ["run", "--config", str(config_file)])
        assert result.exit_code == 0
