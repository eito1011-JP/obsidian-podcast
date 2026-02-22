# VDD Framework セットアップ手順

getting-started.md に沿った Obsidian Podcast プロジェクトへの VDD 導入手順。

> **ステータス**: Level 4 (Vision-Aligned) でセットアップ済み

## 前提条件

| ツール | 用途 |
|--------|------|
| git 2.30+ | バージョン管理、worktree |
| Claude Code CLI | AI 自律開発 |
| jq 1.6+ | 設定ファイル処理 |
| bash 4.0+ | hook スクリプト |

```bash
# Claude Code のインストール（未導入の場合）
npm install -g @anthropic-ai/claude-code
claude login
```

## Step 1: 初期化

### 1-1. git リポジトリの準備

プロジェクトルートがまだ git リポジトリでない場合:

```bash
cd /Users/eito/obsidian-podcast
git init
git branch -m main
```

### 1-2. init.sh の実行

プロジェクトルートで以下を実行:

```bash
cd /Users/eito/obsidian-podcast
bash vdd-framework/scripts/init.sh
```

対話形式で以下を設定します:

1. **プロジェクト名**: デフォルト `obsidian-podcast` で Enter
2. **テストコマンド**: 技術スタック未決定なら空 Enter（後で CLAUDE.md で設定）
3. **チェックコマンド**: 同上
4. **ビルドコマンド**: 同上
5. **インストールコマンド**: 同上
6. **テストファイルパターン**: 同上
7. **採用レベル**: `1`（Safe Development）から開始推奨
8. **確認**: `Y` で実行

### 1-3. 検証

```bash
bash vdd-framework/scripts/validate.sh
```

## Step 2: CLAUDE.md のカスタマイズ

生成された `CLAUDE.md` の `<!-- CUSTOMIZE -->` マーカー付きセクションを編集:

1. プロジェクト概要
2. 技術スタック（設計対話で決定後に記入）
3. コマンド（同上）
4. アーキテクチャ（同上）

## Step 3: 初回コミット

```bash
git add .claude/ CLAUDE.md .gitignore
git add process/  # L2 以上の場合
git commit -m "chore: setup VDD Framework (Level N)"
```

## 次のステップ

- **L2 以上**: `git checkout -b develop` で develop ブランチを作成
- **設計対話**: 技術スタック・アーキテクチャを AI と壁打ちして決定
- **リリース仕様書**: `.claude/release-specs/` に最初のリリース仕様を作成
