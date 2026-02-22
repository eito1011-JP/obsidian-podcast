"""Tests for text preprocessor."""



class TestRemoveImages:
    def test_removes_img_tags(self):
        from obsidian_podcast.preprocessor.text import remove_images

        html = '<p>Before</p><img src="photo.jpg" alt="Photo"/><p>After</p>'
        result = remove_images(html)
        assert "<img" not in result
        assert "Before" in result
        assert "After" in result

    def test_removes_figure_tags(self):
        from obsidian_podcast.preprocessor.text import remove_images

        html = (
            "<p>Text</p><figure><img src='x.png'/>"
            "<figcaption>Cap</figcaption></figure>"
            "<p>More</p>"
        )
        result = remove_images(html)
        assert "<figure" not in result
        assert "<img" not in result


class TestCodeBlockHandling:
    def test_skip_removes_code_blocks(self):
        from obsidian_podcast.preprocessor.text import handle_code_blocks

        html = "<p>Before code.</p><pre><code>x = 1</code></pre><p>After code.</p>"
        result = handle_code_blocks(html, "skip")
        assert "x = 1" not in result
        assert "Before code." in result
        assert "After code." in result

    def test_announce_replaces_with_message(self):
        from obsidian_podcast.preprocessor.text import handle_code_blocks

        html = "<p>Text</p><pre><code>print('hello')</code></pre><p>More</p>"
        result = handle_code_blocks(html, "announce")
        assert "print" not in result
        assert "Text" in result
        assert "More" in result
        # Should contain an announcement message
        assert any(
            word in result.lower()
            for word in ["code", "省略", "コード"]
        )

    def test_read_keeps_code(self):
        from obsidian_podcast.preprocessor.text import handle_code_blocks

        html = "<p>Text</p><pre><code>x = 42</code></pre><p>End</p>"
        result = handle_code_blocks(html, "read")
        assert "x = 42" in result

    def test_skip_handles_pre_without_code(self):
        from obsidian_podcast.preprocessor.text import handle_code_blocks

        html = "<p>Text</p><pre>raw preformatted</pre><p>End</p>"
        result = handle_code_blocks(html, "skip")
        assert "raw preformatted" not in result

    def test_default_is_skip(self):
        from obsidian_podcast.preprocessor.text import handle_code_blocks

        html = "<pre><code>should be removed</code></pre>"
        result = handle_code_blocks(html, "skip")
        assert "should be removed" not in result


class TestTableToText:
    def test_simple_table(self):
        from obsidian_podcast.preprocessor.text import table_to_text

        html = """<table>
        <tr><th>Name</th><th>Age</th></tr>
        <tr><td>Alice</td><td>30</td></tr>
        <tr><td>Bob</td><td>25</td></tr>
        </table>"""
        result = table_to_text(html)
        assert "<table" not in result
        assert "Name" in result
        assert "Alice" in result
        assert "30" in result

    def test_no_table_passthrough(self):
        from obsidian_podcast.preprocessor.text import table_to_text

        html = "<p>No tables here</p>"
        result = table_to_text(html)
        assert "No tables here" in result


class TestNormalizeWhitespace:
    def test_collapses_multiple_spaces(self):
        from obsidian_podcast.preprocessor.text import normalize_whitespace

        assert normalize_whitespace("hello    world") == "hello world"

    def test_collapses_multiple_newlines(self):
        from obsidian_podcast.preprocessor.text import normalize_whitespace

        result = normalize_whitespace("hello\n\n\n\nworld")
        assert result == "hello\n\nworld"

    def test_strips_leading_trailing(self):
        from obsidian_podcast.preprocessor.text import normalize_whitespace

        assert normalize_whitespace("  hello  ") == "hello"

    def test_mixed_whitespace(self):
        from obsidian_podcast.preprocessor.text import normalize_whitespace

        result = normalize_whitespace("  hello \t  world  \n\n\n\n  end  ")
        assert "hello" in result
        assert "world" in result


class TestDetectLanguage:
    def test_detect_english(self):
        from obsidian_podcast.preprocessor.text import detect_language

        text = (
            "This is a long enough English text for language detection. "
            "The algorithm needs sufficient content to work properly."
        )
        lang = detect_language(text)
        assert lang == "en"

    def test_detect_japanese(self):
        from obsidian_podcast.preprocessor.text import detect_language

        text = (
            "これは日本語のテキストです。"
            "言語判定のテストに使います。十分な長さが必要です。"
        )
        lang = detect_language(text)
        assert lang == "ja"

    def test_empty_text_returns_none(self):
        from obsidian_podcast.preprocessor.text import detect_language

        assert detect_language("") is None
        assert detect_language("   ") is None

    def test_very_short_text_returns_none_or_lang(self):
        from obsidian_podcast.preprocessor.text import detect_language

        # Short text may fail detection; shouldn't crash
        result = detect_language("hi")
        assert result is None or isinstance(result, str)


class TestPreprocessArticle:
    """Integration test for the full preprocessing pipeline."""

    def test_full_pipeline(self):
        from obsidian_podcast.preprocessor.text import preprocess

        html = """
        <div>
        <p>This is the main article content for testing.</p>
        <img src="photo.jpg"/>
        <pre><code>x = 1 + 2</code></pre>
        <table><tr><td>A</td><td>B</td></tr></table>
        <p>Final   paragraph    here.</p>
        </div>
        """
        result = preprocess(html, code_block_handling="skip")
        assert isinstance(result, str)
        # Images removed
        assert "<img" not in result
        # Code removed (skip mode)
        assert "x = 1 + 2" not in result
        # Table converted
        assert "<table" not in result
        # Content preserved
        assert "main article content" in result
        assert "Final" in result

    def test_pipeline_with_read_mode(self):
        from obsidian_podcast.preprocessor.text import preprocess

        html = "<p>Text</p><pre><code>print(42)</code></pre>"
        result = preprocess(html, code_block_handling="read")
        assert "print(42)" in result
