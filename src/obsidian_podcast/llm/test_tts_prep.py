"""Tests for TTS pre-processing: sanitize LLM output for Japanese TTS."""


class TestRemoveTTSUnsafeChars:
    def test_removes_exclamation_marks(self):
        from obsidian_podcast.llm.tts_prep import remove_tts_unsafe_chars

        assert "。" not in remove_tts_unsafe_chars("すごい！")
        result = remove_tts_unsafe_chars("すごい！")
        assert "！" not in result
        assert "!" not in result

    def test_removes_question_marks(self):
        from obsidian_podcast.llm.tts_prep import remove_tts_unsafe_chars

        result = remove_tts_unsafe_chars("本当？")
        assert "？" not in result
        assert "?" not in result

    def test_removes_hash_and_markdown(self):
        from obsidian_podcast.llm.tts_prep import remove_tts_unsafe_chars

        result = remove_tts_unsafe_chars("## 見出し")
        assert "#" not in result
        assert "見出し" in result

    def test_removes_backticks_and_code_fences(self):
        from obsidian_podcast.llm.tts_prep import remove_tts_unsafe_chars

        result = remove_tts_unsafe_chars("```javascript\ncode\n```")
        assert "`" not in result

    def test_removes_asterisks(self):
        from obsidian_podcast.llm.tts_prep import remove_tts_unsafe_chars

        result = remove_tts_unsafe_chars("**太字**")
        assert "*" not in result

    def test_preserves_japanese_text(self):
        from obsidian_podcast.llm.tts_prep import remove_tts_unsafe_chars

        text = "これは日本語のテキストです。数字は123です。"
        result = remove_tts_unsafe_chars(text)
        assert "これは日本語のテキストです" in result
        assert "123" in result

    def test_removes_emoji(self):
        from obsidian_podcast.llm.tts_prep import remove_tts_unsafe_chars

        result = remove_tts_unsafe_chars("楽しい😴ですね")
        assert "😴" not in result


class TestEnglishToKatakana:
    def test_converts_simple_english(self):
        from obsidian_podcast.llm.tts_prep import english_to_katakana

        result = english_to_katakana("Router")
        # Should be katakana, not English
        assert "Router" not in result
        assert len(result) > 0

    def test_preserves_japanese(self):
        from obsidian_podcast.llm.tts_prep import english_to_katakana

        result = english_to_katakana("日本語テキスト")
        assert result == "日本語テキスト"

    def test_converts_mixed_text(self):
        from obsidian_podcast.llm.tts_prep import english_to_katakana

        result = english_to_katakana("これはReactの話")
        assert "React" not in result
        assert "これは" in result
        assert "の話" in result


class TestTechTermsDictionary:
    def test_turbopack(self):
        from obsidian_podcast.llm.tts_prep import english_to_katakana

        assert english_to_katakana("Turbopack") == "ターボパック"

    def test_webpack(self):
        from obsidian_podcast.llm.tts_prep import english_to_katakana

        assert english_to_katakana("Webpack") == "ウェブパック"

    def test_app_router(self):
        from obsidian_podcast.llm.tts_prep import english_to_katakana

        result = english_to_katakana("App Router")
        assert "アップ" in result
        assert "ルーター" in result

    def test_tech_terms_in_sentence(self):
        from obsidian_podcast.llm.tts_prep import english_to_katakana

        result = english_to_katakana("TurbopackはRustで書かれた")
        assert "ターボパック" in result
        assert "ラスト" in result


class TestAddTTSPauses:
    def test_adds_newline_after_period(self):
        from obsidian_podcast.llm.tts_prep import add_tts_pauses

        result = add_tts_pauses("最初の文です。次の文です。")
        assert "です。\n" in result

    def test_preserves_comma_without_newline(self):
        from obsidian_podcast.llm.tts_prep import add_tts_pauses

        result = add_tts_pauses("まず、これです。")
        assert "まず、これ" in result

    def test_no_double_newline(self):
        from obsidian_podcast.llm.tts_prep import add_tts_pauses

        result = add_tts_pauses("文です。\n次の文。")
        # Should not add extra newline when one already exists
        assert "。\n\n" not in result


class TestNextJsConversion:
    def test_nextjs_becomes_katakana(self):
        from obsidian_podcast.llm.tts_prep import sanitize_for_tts

        result = sanitize_for_tts("Next.jsの新機能")
        assert "ネクスト" in result
        assert "ジェーエス" in result
        assert "Next" not in result

    def test_ui_becomes_katakana(self):
        from obsidian_podcast.llm.tts_prep import english_to_katakana

        assert english_to_katakana("UI") == "ユーアイ"


class TestSanitizeForTTS:
    def test_full_pipeline(self):
        from obsidian_podcast.llm.tts_prep import sanitize_for_tts

        text = "Next.jsは素晴らしい！Reactベースのフレームワークです。"
        result = sanitize_for_tts(text)
        # No English letters should remain
        assert "Next" not in result
        assert "React" not in result
        # No unsafe chars
        assert "!" not in result
        assert "！" not in result
        assert "." not in result

    def test_empty_text(self):
        from obsidian_podcast.llm.tts_prep import sanitize_for_tts

        assert sanitize_for_tts("") == ""

    def test_pure_japanese(self):
        from obsidian_podcast.llm.tts_prep import sanitize_for_tts

        text = "これは日本語だけのテキストです。"
        result = sanitize_for_tts(text)
        assert "これは日本語だけのテキストです" in result
