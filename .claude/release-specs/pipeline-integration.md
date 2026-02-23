# リリース仕様書: release/pipeline-integration

## 概要

パイプライン全体を統合し、CLI を完成させる。RSS 取得からObsidian 保存まで一気通貫で動作するエンドツーエンドのフローを構築する。Podcast RSS の分岐処理も含む。

## リリース分類

- **レイヤー1**: RDD リリース
- **レイヤー2**: user-facing (feature) → minor バージョンタグ + GitHub Release

## 依存

- `release/storage-writer` が完了していること（全ステップの実装が利用可能）

## スコープ

### 含めるもの

- **パイプライン統合**（`pipeline.py`）
  - 全ステップの連鎖: 取得 → スクレイピング → 前処理 → TTS → R2 → Obsidian 保存
  - async パイプラインの完成
  - 記事単位のエラーハンドリング（1記事の失敗が全体を止めない）
  - SQLite 状態更新（処理開始→成功/失敗）
  - 処理結果サマリーの出力（成功/失敗/スキップ件数）
- **Podcast RSS 分岐**
  - `type: "podcast"` のフィード: TTS をスキップ、既存の音声 URL を使用
  - Podcast 記事用の Markdown テンプレート（音声 URL は enclosure から取得）
- **CLI 完成**（`cli.py`）
  - `obsidian-podcast run`: 全フィード一括処理
  - `obsidian-podcast run --feed <name>`: 特定フィードのみ処理
  - `obsidian-podcast list-feeds`: 設定済みフィードの一覧表示
  - `obsidian-podcast status`: 処理状態の表示（SQLite から集計）
  - 進捗表示（処理中の記事名、成功/失敗カウント）
  - ログレベル設定（`--verbose` / `--quiet`）
- **エラーリカバリ**
  - 失敗した記事の再処理: `obsidian-podcast run --retry-failed`
  - ステータスリセット: `obsidian-podcast reset <url>`

### 含めないもの

- AI 要約生成（Ollama）
- 定期実行（cron）
- 記事フィルタリング

## 技術的詳細

### パイプラインフロー

```
                              ┌─────────────────────┐
                              │ config.yaml 読み込み │
                              └──────────┬──────────┘
                                         ▼
                              ┌──────────────────────┐
                              │ RSS フィード一括取得   │
                              │ (async 並列)          │
                              └──────────┬───────────┘
                                         ▼
                              ┌──────────────────────┐
                              │ 新着記事フィルタリング │
                              │ (SQLite 照合)         │
                              └──────────┬───────────┘
                                         ▼
                          ┌──────────────┴──────────────┐
                          ▼                              ▼
                   type: "article"               type: "podcast"
                          │                              │
                          ▼                              ▼
               ┌──────────────────┐          ┌──────────────────┐
               │ スクレイピング    │          │ enclosure から    │
               │ (フォールバック付)│          │ audio_url 取得    │
               └────────┬─────────┘          └────────┬─────────┘
                        ▼                              │
               ┌──────────────────┐                    │
               │ テキスト前処理    │                    │
               └────────┬─────────┘                    │
                        ▼                              │
               ┌──────────────────┐                    │
               │ TTS (edge-tts)   │                    │
               └────────┬─────────┘                    │
                        ▼                              │
               ┌──────────────────┐                    │
               │ R2 アップロード   │                    │
               └────────┬─────────┘                    │
                        ▼                              ▼
                        └──────────────┬───────────────┘
                                       ▼
                              ┌──────────────────┐
                              │ Obsidian 保存     │
                              │ (Markdown 生成)   │
                              └──────────┬────────┘
                                         ▼
                              ┌──────────────────┐
                              │ SQLite 状態更新   │
                              │ + 結果サマリー    │
                              └──────────────────┘
```

### CLI コマンド一覧

| コマンド | 説明 |
|---------|------|
| `obsidian-podcast init` | 設定ファイル初期化（R1 で実装済み） |
| `obsidian-podcast run` | 全フィード一括処理 |
| `obsidian-podcast run --feed <name>` | 特定フィード処理 |
| `obsidian-podcast run --retry-failed` | 失敗記事の再処理 |
| `obsidian-podcast list-feeds` | フィード一覧表示 |
| `obsidian-podcast status` | 処理状態表示 |
| `obsidian-podcast reset <url>` | 特定記事のステータスリセット |

### 結果サマリー出力例

```
処理完了:
  成功: 12 件
  失敗: 2 件
  スキップ（処理済み）: 35 件
  スキップ（Podcast）: 3 件

失敗した記事:
  - https://example.com/article1 (スクレイピング失敗)
  - https://example.com/article2 (TTS エラー)
```

## テスト方針

- `pipeline.py`: 全ステップのモック結合テスト
  - 正常系: 記事 → Markdown + 音声 URL の完全フロー
  - 異常系: 各ステップでの失敗がスキップされ他の記事に影響しない
  - Podcast RSS: TTS スキップフロー
  - 冪等性: 同じ記事が二重処理されない
- `cli.py`: 全コマンドのテスト（typer CliRunner）
- E2E テスト（モック使用）: config.yaml → run → Markdown 生成の全フロー

## 受け入れ基準

- [ ] `obsidian-podcast run` で全フィードが一括処理される
- [ ] 記事がスクレイピング → TTS → R2 → Obsidian の全フローで処理される
- [ ] Podcast RSS は TTS をスキップして音声 URL を直接使用する
- [ ] 1記事の失敗が全体を止めない
- [ ] 処理済み記事がスキップされる（冪等性）
- [ ] `--retry-failed` で失敗記事が再処理される
- [ ] 処理結果のサマリーが表示される
- [ ] 全テストが通る
- [ ] ruff check + ruff format が通る
