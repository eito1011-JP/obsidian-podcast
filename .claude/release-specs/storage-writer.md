# リリース仕様書: release/storage-writer

## 概要

Cloudflare R2 への音声ファイルアップロードと、Obsidian Vault への Markdown ノート生成・保存を実装する。パイプライン後半の出力系を完成させる。

## リリース分類

- **レイヤー1**: RDD リリース
- **レイヤー2**: developer-only（バージョンタグなし）

## 依存

- `release/tts-engine` が完了していること（mp3 ファイルが生成可能）

## スコープ

### 含めるもの

- **R2 アップロード**（`storage/r2.py`）
  - `boto3` で S3 互換 API を使用して R2 にアップロード
  - パブリックバケットの URL を生成
  - ファイルキーの命名規則: `{year}/{month}/{sanitized_title}.mp3`
  - アップロード済みチェック（重複アップロード防止）
  - 認証情報は環境変数から取得
    - `R2_ACCOUNT_ID`
    - `R2_ACCESS_KEY_ID`
    - `R2_SECRET_ACCESS_KEY`
    - `R2_BUCKET_NAME`
    - `R2_PUBLIC_URL`
- **Obsidian Markdown 生成**（`writer/obsidian.py`）
  - Markdown テンプレートに基づくノート生成
  - YAML フロントマター（メタデータ）
  - 日付別フォルダ構成（月単位）
  - Vault パスへのファイル書き込み
  - 全文抽出失敗時の「全文抽出失敗（RSS要約を使用）」フラグ表示
  - 要約欄のプレースホルダー（MVP では「要約: 未生成」）

### 含めないもの

- AI 要約生成
- Podcast RSS の特別処理（pipeline-integration で対応）

## 技術的詳細

### R2 アップロード

```python
# 環境変数
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# boto3 クライアント
s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
)

# アップロード
s3.upload_file(local_path, bucket, key, ExtraArgs={"ContentType": "audio/mpeg"})

# 公開 URL
public_url = f"{R2_PUBLIC_URL}/{key}"
```

### Markdown テンプレート

```markdown
---
title: "{{title}}"
source: "{{url}}"
author: "{{author}}"
published: {{published_at}}
category: "{{category}}"
tags: [{{tags}}]
audio: "{{audio_url}}"
created: {{created_at}}
full_text: {{is_full_text}}
---

# {{title}}

> [!audio] 音声
> [音声を再生]({{audio_url}})

> [!summary] 要約
> {{summary | default: "未生成"}}

{{#unless is_full_text}}
> [!warning] 全文抽出失敗
> この記事は全文取得に失敗したため、RSS要約を使用しています。
> 元記事: [{{url}}]({{url}})
{{/unless}}

---

{{content}}

---

*出典: [{{title}}]({{url}})*
```

### ファイル配置

```
{vault_path}/{output_dir}/{YYYY-MM}/{sanitized_title}.md
```

- `sanitized_title`: ファイル名に使えない文字を除去、長さ制限（100文字）

## テスト方針

- `storage/r2.py`: moto（AWS モックライブラリ）を使用した S3 互換 API テスト
  - アップロード・URL 生成
  - 重複チェック
  - 認証情報の読み込み
- `writer/obsidian.py`:
  - Markdown テンプレートの生成テスト
  - フロントマターのバリデーション
  - フォルダ構成のテスト
  - 全文抽出失敗フラグの表示テスト
  - ファイル名サニタイズのテスト
- 結合テスト: mp3 → R2 アップロード → Markdown 生成 → Vault 保存

## 受け入れ基準

- [ ] mp3 ファイルを R2 にアップロードし、公開 URL を取得できる
- [ ] Markdown ノートが正しいフォーマットで生成される
- [ ] YAML フロントマターに全メタデータが含まれる
- [ ] 日付別フォルダに正しく配置される
- [ ] 全文抽出失敗時に警告ブロックが表示される
- [ ] 要約欄に「未生成」プレースホルダーが表示される
- [ ] 全テストが通る
- [ ] ruff check + ruff format が通る
