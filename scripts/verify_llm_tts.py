"""検証スクリプト: LLM台本変換 → TTS前処理 → edge-tts 音声生成の E2E テスト。

使い方:
    uv run python scripts/verify_llm_tts.py

前提:
    - Ollama が起動中 (ollama serve)
    - qwen2.5 モデルがインストール済み (ollama pull qwen2.5)
    - edge-tts がインストール済み (uv pip install edge-tts)
"""

import asyncio
import sys
from pathlib import Path

# サンプル記事テキスト（箇条書き・技術用語を含む）
SAMPLE_ARTICLE = """\
## Next.jsの新機能

Next.js 15がリリースされました。主な変更点は以下の通りです：

- App Routerがデフォルトに
- Turbopackが安定版に昇格
- Server Actionsの改善
- React 19のサポート

### Turbopackについて

TurbopackはRustで書かれた新しいバンドラーです。\
Webpackと比較して最大10倍の高速化を実現しています。

```javascript
// next.config.js
module.exports = {
  experimental: {
    turbo: true
  }
}
```

開発者はこの設定を追加するだけでTurbopackを有効にできます。
"""


async def main():
    # 1. LLM台本変換
    print("=" * 60)
    print("Step 1: LLM台本変換 (Ollama qwen2.5)")
    print("=" * 60)

    from obsidian_podcast.config import LLMConfig
    from obsidian_podcast.llm.base import create_llm_engine, generate_podcast_script
    from obsidian_podcast.llm.tts_prep import sanitize_for_tts

    # Ollama 向け設定
    config = LLMConfig(
        enabled=True,
        engine="openai",
        model="qwen2.5",
        base_url="http://localhost:11434/v1",
        api_key_env="",
        max_chunk_chars=4000,
    )

    # プロバイダ登録をトリガー
    import obsidian_podcast.llm  # noqa: F401

    provider = create_llm_engine(config)

    print("\n--- 元テキスト ---")
    print(SAMPLE_ARTICLE[:200] + "...")
    print()

    print("LLM変換中...")
    script = await generate_podcast_script(
        SAMPLE_ARTICLE, provider, max_chunk_chars=config.max_chunk_chars
    )

    print("\n--- LLM変換後 ---")
    print(script)
    print()

    # 2. TTS前処理（記号除去 + 英語→カタカナ変換）
    print("=" * 60)
    print("Step 2: TTS前処理 (sanitize_for_tts)")
    print("=" * 60)

    sanitized = sanitize_for_tts(script)

    print("\n--- サニタイズ後 ---")
    print(sanitized)
    print()

    # 3. edge-tts で音声生成
    print("=" * 60)
    print("Step 3: edge-tts 音声生成")
    print("=" * 60)

    import edge_tts

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    files = [
        ("original", SAMPLE_ARTICLE),
        ("script_raw", script),
        ("script_sanitized", sanitized),
    ]
    for label, text in files:
        output_path = output_dir / f"verify_{label}.mp3"
        communicate = edge_tts.Communicate(text, "ja-JP-NanamiNeural")
        await communicate.save(str(output_path))
        print(f"  {label}: {output_path} ({output_path.stat().st_size:,} bytes)")

    print()
    print("=" * 60)
    print("検証完了")
    print("  output/verify_original.mp3         — 元テキストの音声")
    print("  output/verify_script_raw.mp3       — LLM台本変換後（サニタイズなし）")
    print("  output/verify_script_sanitized.mp3 — LLM台本変換後（サニタイズ済み）")
    print("3つを聴き比べて効果を確認してください。")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
