# Obsidian Podcast 要件定義書

## 1. プロジェクト概要

複数の RSS フィードから記事を取得し、全文を音声化して Obsidian に保存するCLIツール。
「読みたい記事が溜まって消化できない」問題を、通勤中に聴けるポッドキャスト形式で解決する。

## 2. ユーザーストーリー

- **通勤リスナー**: 通勤中にスマホで技術ブログやニュース記事を「聴きたい」
- **ナレッジ蓄積者**: 聴いた記事を Obsidian ノートとして蓄積し、後から検索・参照したい

## 3. システム構成

```
[RSS Feeds] → [記事取得] → [全文スクレイピング] → [テキスト前処理] → [TTS音声化]
                                                                            ↓
[Obsidian Vault] ← [Markdown生成] ← [AI要約]          [Cloudflare R2] ← [音声アップロード]
                                                                            ↓
                                      [Markdown内に音声URLリンクを埋め込み] ←┘
```

## 4. 機能要件

### 4.1 RSS フィード取得

- 対象: 技術ブログ、ニュースサイト、企業ブログ、ポッドキャスト等あらゆる RSS
- フィード数: 可変（設定ファイルで管理）
- 新着記事の差分取得（既に処理済みの記事はスキップ）

### 4.2 記事全文抽出

- 元記事ページをスクレイピングして全文を取得
- **MVP では公開記事のみ**（認証不要のページ）
- 将来: ログイン対応（Cookie/トークン認証）の拡張余地を残す
- HTML → テキスト変換（本文抽出）

### 4.3 テキスト前処理（音声化用）

- コードブロックの処理: **設定で切り替え可能**
  - デフォルト: コードブロックを**完全に無視**（アナウンスもせず前後の文章を繋げる）
  - オプション: 「コード省略」とアナウンス / コードもそのまま読み上げ
- 画像: 無視（alt テキストがあれば読み上げるオプションも検討）
- テーブル: テキスト化して読み上げ

### 4.4 音声合成（TTS）

- **デフォルトエンジン: `edge-tts`**（無料）
- **ストラテジーパターン（プラグインアーキテクチャ）で設計**（絶対条件）
  - TTS 基底クラス/インターフェースを定義
  - `config.yaml` の設定で TTS エンジンを切り替え可能
  - 将来追加予定: Kokoro TTS, OpenAI TTS 等
- 言語: **記事の言語を自動判定**して適切な音声で読み上げ
- 出力形式: mp3

### 4.5 音声ファイル管理

- **Cloudflare R2 にアップロード**
- Obsidian Vault には音声ファイルを保存しない
- Markdown 内に音声の URL リンクを埋め込む

### 4.6 Obsidian 保存

**Markdown ファイルに含める情報:**

- 記事タイトル
- ソース URL
- 著者名
- 公開日
- タグ / カテゴリ
- 記事本文（テキスト）
- 音声ファイルへの URL リンク
- AI 生成要約

**ファイル構成: 日付別（月単位）**

```
Podcast/
├── 2026-02/
│   ├── 記事タイトル.md
│   └── ...
├── 2026-03/
│   └── ...
```

**Vault パス:** `/Users/eito/Library/Mobile Documents/iCloud~md~obsidian/Documents/my vault/my vault`

### 4.7 AI 要約

- **ローカル LLM（Ollama 等）**で記事を要約
- 要約は Markdown ノートに掲載
- 音声はフルテキストで読み上げ（要約ではない）

### 4.8 ポッドキャスト RSS の特別処理

- 既に音声データがあるポッドキャスト RSS の場合:
  - 音声はそのまま使う（TTS は行わない）
  - メタデータのみ Obsidian に保存
  - 既存の音声 URL をリンクする

### 4.9 複数フィード管理

- `config.yaml` でフィード URL を一覧管理
- フィードごとにカテゴリ/タグを設定可能

## 5. 非機能要件

| 項目 | 要件 |
|------|------|
| 実行方法 | CLI コマンド（将来: 自動化） |
| 実行環境 | ローカル Mac |
| 言語 | Python |
| コスト | TTS は無料（edge-tts）、AI 要約はローカル LLM |
| ストレージ | Cloudflare R2 |

## 6. 設定ファイル（config.yaml）イメージ

```yaml
# フィード設定
feeds:
  - url: "https://zenn.dev/feed"
    category: "tech"
    tags: ["zenn", "技術"]
  - url: "https://example.com/podcast/feed.xml"
    type: "podcast"  # 音声そのまま使う
    category: "podcast"

# TTS 設定
tts:
  engine: "edge-tts"  # edge-tts | kokoro | openai（将来）
  language_detection: true
  code_block_handling: "skip"  # skip | announce | read

# ストレージ設定
storage:
  type: "cloudflare-r2"
  bucket: "obsidian-podcast"
  # 認証情報は環境変数から読み取り

# Obsidian 設定
obsidian:
  vault_path: "/Users/eito/Library/Mobile Documents/iCloud~md~obsidian/Documents/my vault/my vault"
  output_dir: "Podcast"
  folder_structure: "monthly"  # monthly | feed | flat

# AI 要約設定
summary:
  engine: "ollama"
  model: "llama3"
```

## 7. MVP スコープ（優先順位順）

| 優先度 | 機能 | MVP |
|--------|------|-----|
| 1 | RSS フィード取得 | o |
| 2 | 記事全文抽出（スクレイピング） | o |
| 3 | 音声合成（TTS / edge-tts） | o |
| 4 | Obsidian Vault への保存 | o |
| 5 | 複数フィード管理（config.yaml） | o |
| 6 | 定期実行 | - |

## 8. 将来機能（MVP 外）

- AI による記事要約（Ollama）— MVP 直後に対応
- 記事のフィルタリング（キーワード / カテゴリ）
- 音声の再生速度調整
- Obsidian 内での再生 UI
- 定期実行（cron / スケジューラ）
- 有料記事・認証付きサイト対応

## 9. 技術スタック（案）

| レイヤー | 技術 |
|----------|------|
| 言語 | Python 3.12+ |
| RSS パース | `feedparser` |
| スクレイピング | `httpx` + `readability-lxml` or `newspaper3k` |
| TTS | `edge-tts`（デフォルト）+ プラグイン基盤 |
| 言語判定 | `langdetect` |
| AI 要約 | `ollama` (Python SDK) |
| ストレージ | `boto3`（S3 互換で R2 接続） |
| CLI | `click` or `typer` |
| 設定管理 | `pydantic` + YAML |
| テスト | `pytest` |
| Lint | `ruff` |

## 10. アーキテクチャ方針

- **パイプライン設計**: 取得 → 抽出 → 前処理 → TTS → アップロード → 保存の各ステップを独立したモジュールに
- **TTS はストラテジーパターン**: 基底クラス `TTSEngine` を定義し、各エンジンはサブクラスで実装
- **冪等性**: 同じ記事を二重処理しない（処理済み記事の管理）
- **エラーハンドリング**: 1記事の失敗が全体を止めない（個別スキップ + ログ）
