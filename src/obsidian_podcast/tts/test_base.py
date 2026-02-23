"""Tests for TTS base class and factory."""

import pytest


class TestTTSEngine:
    def test_is_abstract(self):
        """TTSEngine should not be instantiable directly."""
        from obsidian_podcast.tts.base import TTSEngine

        with pytest.raises(TypeError):
            TTSEngine()  # type: ignore[abstract]

    def test_concrete_implementation(self):
        """A concrete subclass should be instantiable."""
        from obsidian_podcast.tts.base import TTSEngine

        class MockTTS(TTSEngine):
            async def synthesize(
                self, text: str, language: str, output_path: str
            ) -> None:
                pass

            def supported_languages(self) -> list[str]:
                return ["en", "ja"]

        engine = MockTTS()
        assert engine.supported_languages() == ["en", "ja"]

    def test_missing_method_raises(self):
        """Subclass missing abstract methods should not be instantiable."""
        from obsidian_podcast.tts.base import TTSEngine

        class IncompleteTTS(TTSEngine):  # type: ignore[abstract]
            pass

        with pytest.raises(TypeError):
            IncompleteTTS()  # type: ignore[abstract]


class TestTTSFactory:
    def test_get_engine_not_found(self):
        """Unknown engine name should raise ValueError."""
        from obsidian_podcast.tts.base import get_tts_engine

        with pytest.raises(ValueError, match="Unknown TTS engine"):
            get_tts_engine("nonexistent")

    def test_register_and_get_engine(self):
        """Should be able to register and retrieve a TTS engine."""
        from obsidian_podcast.tts.base import (
            TTSEngine,
            get_tts_engine,
            register_tts_engine,
        )

        class DummyTTS(TTSEngine):
            async def synthesize(
                self, text: str, language: str, output_path: str
            ) -> None:
                pass

            def supported_languages(self) -> list[str]:
                return ["en"]

        register_tts_engine("dummy", DummyTTS)
        engine = get_tts_engine("dummy")
        assert isinstance(engine, DummyTTS)
