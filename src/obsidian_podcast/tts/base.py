"""TTS engine base class and factory."""

from abc import ABC, abstractmethod

_registry: dict[str, type["TTSEngine"]] = {}


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    async def synthesize(self, text: str, language: str, output_path: str) -> None:
        """Convert text to speech and save to output_path."""
        ...

    @abstractmethod
    def supported_languages(self) -> list[str]:
        """Return list of supported language codes."""
        ...


def register_tts_engine(name: str, engine_class: type[TTSEngine]) -> None:
    """Register a TTS engine class by name."""
    _registry[name] = engine_class


def get_tts_engine(name: str) -> TTSEngine:
    """Create a TTS engine instance by name."""
    if name not in _registry:
        msg = f"Unknown TTS engine: {name}. Available: {list(_registry.keys())}"
        raise ValueError(msg)
    return _registry[name]()
