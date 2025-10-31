# Git AI Tools - 強化されたGitコミット支援ツール

このディレクトリには、AIを活用した高度なGitワークフロー支援ツールが含まれています。

## 🚀 主要機能

### git_commit_ai（強化版）
AI を使用してコミットメッセージを自動生成する高機能ツール

**新機能:**
- ✅ **3つのAIプロバイダー対応**: HuggingFace, Gemini, Ollama
- ✅ **リモートとの差分チェック**: コンフリクトを事前に回避
- ✅ **センシティブ内容検出**: 秘密情報の自動検出・スキップ
- ✅ **AI コメント付き編集**: 推奨フォーマット付きでメッセージ編集
- ✅ **ステージ済みファイル対応**: 既にaddされたファイルも適切に処理
- ✅ **PR作成支援**: コミット後のプルリクエスト作成サポート

### git_utils
追加のGit便利コマンド集

**機能:**
- 🧹 **ブランチクリーンアップ**: マージ済みブランチの自動削除
- 📊 **統計情報表示**: リポジトリの詳細分析
- 🔧 **コンフリクト解決支援**: インタラクティブな競合解決
- 🔄 **rebase支援**: 安全なインタラクティブrebase
- 📦 **コミット統合**: 複数コミットのsquash操作
- ↩️ **操作取り消し**: 各種Git操作のundo機能

## 📋 使用方法

### git_commit_ai基本使用法

```bash
# 通常のAIコミット
./tools/git_commit_ai

# リモート同期後にコミット（推奨）
./tools/git_commit_ai --sync

# 詳細なgit状況確認
./tools/git_commit_ai --status

# コミット後PR作成サポート
./tools/git_commit_ai --pr

# 強制モード（警告無視）
./tools/git_commit_ai --force
```

### git_utils使用法

```bash
# ヘルプ表示
./tools/git_utils help

# マージ済みブランチクリーンアップ
./tools/git_utils cleanup

# リポジトリ統計表示
./tools/git_utils stats --detailed

# コンフリクト解決支援
./tools/git_utils conflicts

# 直近3コミットを統合
./tools/git_utils squash 3

# 現在の状態をバックアップ
./tools/git_utils backup
```

## ⚙️ 設定

### 必要な環境変数
```bash
# .env ファイルまたは環境変数に設定
GEMINI_API_KEY=your_gemini_api_key
HF_TOKEN=your_huggingface_token
OLLAMA_HOST=http://127.0.0.1:11434  # オプション
```

### config.yaml設定例
```yaml
llm:
  gemini:
    model: "gemini-2.5-flash"
    api_url: "https://generativelanguage.googleapis.com/v1"
  huggingface:
    model: "openai/gpt-oss-20b:groq"
    host: "https://router.huggingface.co/v1"
  ollama:
    model: "qwen2.5:1.5b-instruct"
    host: "http://127.0.0.1:11434"
```

## 🛡️ セキュリティ機能

### センシティブ内容検出
- 秘密鍵、APIキー、トークンの自動検出
- センシティブファイル名の識別
- 検出時の自動スキップ機能

### コンフリクト回避
- リモートブランチとの差分チェック
- 変更競合の事前警告
- 安全な同期オプション

## 📝 コミットメッセージフォーマット

NeuroHubスタイルのコミットメッセージ：

```
:prefix: #Issue 内容

利用可能なprefix:
:add:      新規追加
:fix:      バグ修正
:update:   機能更新
:refactor: リファクタリング
:docs:     ドキュメント
:test:     テスト
:style:    スタイル
:config:   設定
```

## 🔄 ワークフロー例

### 1. 安全なAIコミットワークフロー
```bash
# 1. 状況確認
./tools/git_commit_ai --status

# 2. リモート同期付きコミット
./tools/git_commit_ai --sync

# 3. PR作成
./tools/git_commit_ai --pr
```

### 2. ブランチクリーンアップワークフロー
```bash
# 1. 統計確認
./tools/git_utils stats

# 2. クリーンアップ
./tools/git_utils cleanup

# 3. バックアップ作成
./tools/git_utils backup
```

## 🐛 トラブルシューティング

### よくある問題

**AIプロバイダーが応答しない**
- 各プロバイダーのAPIキー設定を確認
- ネットワーク接続を確認
- Ollamaサーバーの起動状況を確認

**コンフリクトが発生する**
- `--sync` オプションを使用してリモート同期
- `./tools/git_utils conflicts` でコンフリクト解決支援を利用

**センシティブ情報が検出される**
- `.gitignore` に適切なパターンを追加
- 手動でファイルをスキップまたは編集

## 📚 関連ドキュメント

- [services/llm/README.md](../services/llm/README.md) - LLMプロバイダー詳細
- [config/README.md](../config/README.md) - 設定ファイル詳細
- [docs/](../docs/) - 追加ドキュメント

## 🤝 貢献

このツールの改善提案やバグ報告は、GitHubのIssueまたはPull Requestでお願いします。

```bash
# 貢献者情報確認
./tools/git_utils contributors
```
