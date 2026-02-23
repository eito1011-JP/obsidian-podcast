# リリース仕様書: release/tts-engine

## 概要

TTS プラグインアーキテクチャ（ストラテジーパターン）を完成させ、edge-tts エンジンを実装する。記事テキストを言語自動判定に基づいて適切な音声で mp3 に変換する。

## リリース分類

- **レイヤー1**: RDD リリース
- **レイヤー2**: developer-only（バージョンタグなし）

## 依存

- `release/feed-scraper` が完了していること（入力テキストの前処理が利用可能）

## スコープ

### 含めるもの

- **TTS 基底クラスの完成**（`tts/base.py`）
  - `TTSEngine` ABC の最終仕様
  - エンジンのファクトリ関数（config の `tts.engine` から動的にエンジンを選択）
- **edge-tts エンジン**（`tts/edge.py`）
  - `edge-tts` ライブラリを使用した音声合成
  - 言語コードに基づく音声（voice）の自動選択
  - mp3 出力
  - 長文記事の分割処理（edge-tts の制限に対応）
- **言語 → 音声マッピング**
  - 日本語: `ja-JP-NanamiNeural` 等
  - 英語: `en-US-AriaNeural` 等
  - その他言語のデフォルトマッピング
- **一時ファイル管理**
  - TTS 出力を一時ディレクトリに保存
  - アップロード完了後にクリーンアップ

### 含めないもの

- Kokoro TTS / OpenAI TTS 等の追加エンジン（将来リリース）
- R2 アップロード
- Obsidian 保存

## 技術的詳細

### ファクトリパターン

```python
# tts/base.py
_ENGINE_REGISTRY: dict[str, type[TTSEngine]] = {}

def register_engine(name: str):
    """デコレータでエンジンを登録"""
    def decorator(cls):
        _ENGINE_REGISTRY[name] = cls
        return cls
    return decorator

def create_engine(config: TTSConfig) -> TTSEngine:
    """config.tts.engine の値からエンジンを生成"""
    engine_cls = _ENGINE_REGISTRY[config.engine]
    return engine_cls(config)
```

### edge-tts エンジンの処理フロー

```
1. Article.language から voice を選択
2. テキストを適切なチャンクに分割（edge-tts の制限対応）
3. 各チャンクを edge-tts で音声化
4. チャンクを結合して1つの mp3 ファイルに
5. 一時ファイルのパスを返却
```

### 音声選択マッピング（デフォルト）

| 言語コード | 音声 |
|-----------|------|
| ja | ja-JP-NanamiNeural |
| en | en-US-AriaNeural |
| zh | zh-CN-XiaoxiaoNeural |
| ko | ko-KR-SunHiNeural |
| de | de-DE-KatjaNeural |
| fr | fr-FR-DeniseNeural |
| (その他) | en-US-AriaNeural (フォールバック) |

## テスト方針

- `tts/base.py`: ファクトリ、レジストリ、ABC 制約のテスト
- `tts/edge.py`: edge-tts のモックテスト（実際の API 呼び出しはモック）
  - 言語に応じた voice 選択
  - テキスト分割ロジック
  - mp3 ファイル出力の検証
- 結合テスト: テキスト入力 → mp3 出力の E2E（モック使用）

## 受け入れ基準

- [ ] `create_engine("edge-tts")` で EdgeTTSEngine が生成される
- [ ] 日本語テキストを mp3 に変換できる
- [ ] 英語テキストを mp3 に変換できる
- [ ] 言語に応じた音声が自動選択される
- [ ] 長文記事でもエラーなく処理できる
- [ ] 全テストが通る
- [ ] ruff check + ruff format が通る
