# リリース仕様書: release/feed-scraper

## 概要

RSS フィード取得、記事全文スクレイピング、テキスト前処理を実装する。フィードから新着記事を検出し、元記事ページから全文を抽出し、TTS 用にテキストを整形するまでのパイプライン前半を完成させる。

## リリース分類

- **レイヤー1**: RDD リリース
- **レイヤー2**: developer-only（バージョンタグなし）

## 依存

- `release/project-setup` が完了していること

## スコープ

### 含めるもの

- **RSS フィード取得**（`fetcher/rss.py`）
  - `feedparser` で RSS/Atom フィードをパース
  - 新着記事の検出（SQLite の処理済みリストと照合）
  - フィードごとの取得（async httpx）
  - Podcast RSS の判定（`enclosure` タグの有無）
- **全文スクレイピング**（`scraper/extractor.py`）
  - `httpx` で記事ページを取得
  - `readability-lxml` で本文抽出
  - HTML → テキスト変換
  - スクレイピング失敗時のフォールバック: RSS の description/content を使用し、Markdown に「全文抽出失敗（RSS要約を使用）」フラグ付与
  - 公開記事のみ対応（認証不要）
- **テキスト前処理**（`preprocessor/text.py`）
  - コードブロック処理（設定で切り替え可能）
    - `skip`: 完全に無視して前後の文章を繋げる（デフォルト）
    - `announce`: 「コード省略」とアナウンス
    - `read`: コードもそのまま読み上げ
  - 画像の除去
  - テーブルのテキスト化
  - 不要な空白・改行の正規化
  - 言語判定（`langdetect`）

### 含めないもの

- TTS 音声合成
- R2 アップロード
- Obsidian 保存
- 認証付きサイトのスクレイピング

## 技術的詳細

### RSS フィード取得フロー

```
1. config.yaml からフィード一覧を読み込み
2. 各フィードを async で並列取得
3. feedparser でパース
4. 各記事の URL を SQLite と照合
5. 未処理の記事のみを Article モデルとして返却
6. Podcast RSS（enclosure あり）は audio_url を Article に設定し、スクレイピング・TTS をスキップするフラグを立てる
```

### スクレイピングフロー

```
1. Article.url に httpx で GET リクエスト
2. readability-lxml で本文を抽出
3. 失敗時: RSS の content または description をフォールバックとして使用
4. Article.content にテキストを設定
5. Article.is_full_text フラグを設定（True: 全文取得成功, False: RSS フォールバック）
```

### 前処理フロー

```
1. HTML タグの除去（BeautifulSoup）
2. コードブロック処理（config.tts.code_block_handling に応じて）
3. 画像タグの除去
4. テーブルのテキスト化
5. 空白・改行の正規化
6. 言語判定 → Article.language に設定
```

## テスト方針

- `fetcher/rss.py`: モックフィード XML でのパースと差分検出テスト
- `scraper/extractor.py`: モック HTML での本文抽出テスト、フォールバックテスト
- `preprocessor/text.py`: コードブロック処理の各モード、テーブル変換、言語判定のテスト
- 結合テスト: フィード取得 → スクレイピング → 前処理の一連フロー

## 受け入れ基準

- [ ] RSS フィードから新着記事を検出できる
- [ ] 記事ページから全文を抽出できる
- [ ] スクレイピング失敗時に RSS 内容でフォールバックし、フラグが付く
- [ ] コードブロックがデフォルトで完全に無視される
- [ ] Podcast RSS が正しく判定される
- [ ] 言語判定が動作する
- [ ] 全テストが通る
- [ ] ruff check + ruff format が通る
