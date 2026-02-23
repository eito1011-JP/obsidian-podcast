# リリース仕様書: release/project-setup

## 概要

Obsidian Podcast プロジェクトの基盤を構築する。uv によるパッケージ管理、CLI 骨格、設定管理、SQLite 状態管理、共通データモデルを整備し、後続リリースが依存するインフラを確立する。

## リリース分類

- **レイヤー1**: RDD リリース
- **レイヤー2**: developer-only（バージョンタグなし）

## スコープ

### 含めるもの

- `pyproject.toml` + uv セットアップ（Python 3.12+）
- ruff 設定（lint + format）
- pytest 設定
- CLI 骨格（typer ベース）
  - `obsidian-podcast run` コマンド（スタブ）
  - `--feed` オプション（スタブ）
  - `--config` オプション（設定ファイルパス指定）
- 設定管理（pydantic + YAML）
  - `config.yaml` のスキーマ定義
  - XDG 準拠の配置（`~/.config/obsidian-podcast/config.yaml`）
  - デフォルト設定の生成（`obsidian-podcast init`）
- SQLite 状態管理
  - `~/.config/obsidian-podcast/state.db`
  - `articles` テーブル（url, feed_url, title, status, processed_at 等）
  - 基本 CRUD 操作
- 共通データモデル（`models.py`）
  - `Article` dataclass（RSS から抽出される記事情報）
  - `FeedConfig` dataclass（フィード設定）
  - `ProcessingStatus` enum（pending, completed, failed）
- パイプライン骨格（`pipeline.py`）
  - async パイプラインの基本構造（ステップの連鎖）
  - 各ステップのインターフェース定義
- ディレクトリ構成の確立

### 含めないもの

- RSS フィード取得の実装
- スクレイピング
- TTS
- R2 アップロード
- Obsidian 保存

## ディレクトリ構成

```
src/obsidian_podcast/
├── __init__.py
├── __main__.py
├── cli.py              # typer CLI
├── config.py           # pydantic 設定モデル + YAML 読み込み
├── pipeline.py         # async パイプライン骨格
├── models.py           # Article, FeedConfig, ProcessingStatus
├── fetcher/
│   └── __init__.py
├── scraper/
│   └── __init__.py
├── preprocessor/
│   └── __init__.py
├── tts/
│   ├── __init__.py
│   └── base.py         # TTSEngine ABC
├── storage/
│   └── __init__.py
├── writer/
│   └── __init__.py
└── db/
    ├── __init__.py
    └── state.py         # SQLite 状態管理
```

## 技術的詳細

### 設定ファイル（config.yaml）スキーマ

```yaml
feeds:
  - url: str           # RSS フィード URL
    name: str          # フィード名（省略時は URL から生成）
    category: str      # カテゴリ
    tags: list[str]    # タグ
    type: str          # "article" | "podcast"（デフォルト: "article"）

tts:
  engine: str          # "edge-tts"（デフォルト）
  language_detection: bool  # true（デフォルト）
  code_block_handling: str  # "skip" | "announce" | "read"（デフォルト: "skip"）

storage:
  type: str            # "cloudflare-r2"
  bucket: str
  public_url: str      # パブリックバケットの URL

obsidian:
  vault_path: str
  output_dir: str      # "Podcast"（デフォルト）
  folder_structure: str # "monthly" | "feed" | "flat"（デフォルト: "monthly"）

summary:
  enabled: bool        # false（デフォルト、MVP では無効）
  engine: str          # "ollama"
  model: str           # "llama3"
```

### SQLite スキーマ

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    feed_url TEXT NOT NULL,
    title TEXT,
    author TEXT,
    published_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    audio_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
```

### TTS 基底クラス

```python
from abc import ABC, abstractmethod

class TTSEngine(ABC):
    @abstractmethod
    async def synthesize(self, text: str, language: str, output_path: str) -> None:
        """テキストを音声に変換し、output_path に保存する"""
        ...

    @abstractmethod
    def supported_languages(self) -> list[str]:
        """サポートする言語コードのリストを返す"""
        ...
```

## テスト方針

- `config.py`: YAML 読み込み、バリデーション、デフォルト値のテスト
- `db/state.py`: CRUD 操作のテスト（インメモリ SQLite）
- `models.py`: dataclass のシリアライズ/デシリアライズ
- `cli.py`: typer のコマンドテスト（`CliRunner`）
- `pipeline.py`: パイプライン骨格の結合テスト

## 受け入れ基準

- [ ] `uv run obsidian-podcast --help` が動作する
- [ ] `uv run obsidian-podcast init` で `~/.config/obsidian-podcast/config.yaml` が生成される
- [ ] `uv run obsidian-podcast run` が「パイプライン実行（スタブ）」メッセージを出力する
- [ ] SQLite に記事を登録・検索・更新できる
- [ ] 全テストが通る
- [ ] ruff check + ruff format が通る
