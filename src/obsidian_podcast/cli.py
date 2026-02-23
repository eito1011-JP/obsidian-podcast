"""CLI interface using typer."""

from pathlib import Path

import typer

from obsidian_podcast.config import generate_default_config, get_config_dir

app = typer.Typer(
    name="obsidian-podcast",
    help="RSS feed articles to audio for Obsidian.",
)


@app.command()
def init() -> None:
    """Initialize configuration file."""
    config_dir = get_config_dir()
    config_path = config_dir / "config.yaml"

    if config_path.exists():
        typer.echo(f"Configuration already exists: {config_path}")
        return

    generate_default_config(config_path)
    typer.echo(f"Configuration created: {config_path}")


@app.command()
def run(
    feed: str | None = typer.Option(None, "--feed", help="RSS feed URL to process"),
    config: Path | None = typer.Option(
        None, "--config", help="Path to configuration file"
    ),
) -> None:
    """Run the podcast pipeline (stub)."""
    if config:
        typer.echo(f"Using config: {config}")
    if feed:
        typer.echo(f"Processing feed: {feed}")
    typer.echo("Pipeline execution (stub) - not yet implemented")
