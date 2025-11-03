# NeuroHub エージェント直接実行ガイド

## 🎯 概要

NeuroHubでは、各エージェントを個別に直接実行することができます。このガイドでは、WSL環境およびWindows環境での各エージェントの直接実行方法を詳しく説明します。

## 🌍 実行環境

### 推奨環境
- **WSL (Windows Subsystem for Linux)**: 全ユーザー推奨
- **Linux**: ネイティブ環境
- Python 3.8+
- 仮想環境 (`venv_linux`)

### ディレクトリ構造
```
NeuroHub/
├── main.py              # 統一インターフェース
├── agents/
│   ├── agent_llm.py     # LLMエージェント
│   ├── agent_mcp.py     # MCPエージェント
│   ├── agent_git.py     # Gitエージェント
│   └── specialized/
│       ├── web_agent.py    # Webエージェント
│       └── weather_agent.py # 天気エージェント
└── venv_linux/          # Linux用仮想環境
```

## 🚀 基本実行方法

### 1. 統一インターフェース経由（推奨）

#### 基本形式
```bash
# WSL環境
cd /mnt/c/Users/kenny/sandbox/NeuroHub
python main.py "プロンプト"

# Windows PowerShell
cd C:\Users\kenny\sandbox\NeuroHub
python main.py "プロンプト"
```

#### 特定エージェント強制実行
```bash
# MCPエージェント強制
python main.py "Pythonファイルを作成して" --force-agent mcp

# Webエージェント強制
python main.py "Pythonについて調べて" --force-agent web

# LLMエージェント強制
python main.py "質問に答えて" --force-agent llm

# Gitエージェント強制
python main.py "コミットして" --force-agent git

# 天気エージェント強制
python main.py "今日の天気は？" --force-agent weather

# コマンドエージェント強制
python main.py "ファイル一覧を表示" --force-agent command
```

#### プロバイダー指定
```bash
# Ollamaを使用
python main.py "質問" --provider ollama

# Geminiを使用
python main.py "質問" --provider gemini

# HuggingFaceを使用
python main.py "質問" --provider huggingface
```

#### デバッグモード
```bash
# 詳細ログ出力
python main.py "質問" --debug

# 特定エージェント + デバッグ
python main.py "質問" --force-agent mcp --debug
```

### 2. エージェント直接実行

#### LLMエージェント (agent_llm.py)
```bash
# WSL環境
cd /mnt/c/Users/kenny/sandbox/NeuroHub
source venv_linux/bin/activate
python agents/agent_llm.py "こんにちはって何語？"

# プロバイダー指定
python agents/agent_llm.py "質問" --provider ollama
python agents/agent_llm.py "質問" --provider gemini
python agents/agent_llm.py "質問" --provider huggingface
```

#### MCPエージェント (agent_mcp.py)
```bash
# コード生成モード
python agents/agent_mcp.py generate "シンプルなPythonスクリプトを作成"

# プロジェクト作成モード
python agents/agent_mcp.py project "ToDoアプリを作成"

# デバッグモード
python agents/agent_mcp.py debug "既存のコードを修正"

# 最適化モード
python agents/agent_mcp.py optimize "コードを最適化"

# 設計モード
python agents/agent_mcp.py design "アプリの設計書を作成"

# 省略形式（generateがデフォルト）
python agents/agent_mcp.py "簡単なツールを作成"

# 出力ファイル指定
python agents/agent_mcp.py generate "ツール作成" --output tool.py

# プロバイダー指定
python agents/agent_mcp.py generate "コード作成" --provider ollama
```

#### Webエージェント (web_agent.py)
```bash
# URL解析
python agents/specialized/web_agent.py "https://example.com この内容を要約して"

# Web検索
python agents/specialized/web_agent.py "Pythonについて検索"

# 質問とURL組み合わせ
python agents/specialized/web_agent.py "https://github.com この技術について詳しく"
```

#### Gitエージェント (agent_git.py)
```bash
# ステータス確認
python agents/agent_git.py "status"

# コミット
python agents/agent_git.py "add . && commit -m '修正'"

# プッシュ
python agents/agent_git.py "push origin aidev"

# ブランチ操作
python agents/agent_git.py "checkout -b new-feature"

# ログ確認
python agents/agent_git.py "log --oneline -5"
```

## ⚙️ 高度な実行オプション

### 環境変数設定
```bash
# OpenAI API Key (HuggingFaceで使用)
export OPENAI_API_KEY="your_key_here"

# Google API Key (Geminiで使用)
export GOOGLE_API_KEY="your_key_here"

# Nature Remo API Key
export NATURE_REMO_TOKEN="your_token_here"

# Discord Bot Token
export DISCORD_TOKEN="your_token_here"
```

### WSLでの完全実行コマンド
```bash
# 完全なWSL実行コマンド（Windows PowerShellから）
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python main.py 'プロンプト'"

# エージェント直接実行
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && python agents/agent_mcp.py 'コード作成'"
```

### 実行時オプション一覧

#### main.py オプション
```bash
python main.py [プロンプト] [オプション]

オプション:
  --force-agent {weather,web,mcp,git,command,config,llm}
                        特定エージェントを強制実行
  --provider {ollama,gemini,huggingface}
                        LLMプロバイダーを指定
  --debug               デバッグモードでログ詳細出力
  --help                ヘルプメッセージ表示
```

#### agent_mcp.py オプション
```bash
python agents/agent_mcp.py [mode] [プロンプト] [オプション]

モード:
  generate              コード生成（デフォルト）
  project               プロジェクト作成
  debug                 コードデバッグ
  optimize              コード最適化
  design                設計書作成

オプション:
  --output OUTPUT       出力ファイル名
  --provider {ollama,gemini,huggingface}
                        LLMプロバイダー指定
  --model MODEL         特定モデル指定
  --help                ヘルプメッセージ表示

使用例:
  python agents/agent_mcp.py generate "ツール作成"
  python agents/agent_mcp.py "ツール作成"  # generateは省略可能
  python agents/agent_mcp.py project "アプリ作成" --output app.py
```

#### agent_llm.py オプション
```bash
python agents/agent_llm.py [プロンプト] [オプション]

オプション:
  --provider {ollama,gemini,huggingface}
                        LLMプロバイダー指定
  --model MODEL         特定モデル指定
  --help                ヘルプメッセージ表示
```

## 🔧 トラブルシューティング

### よくあるエラーと解決策

#### 1. インポートエラー
```bash
エラー: ModuleNotFoundError: No module named 'xxx'

解決策:
# 仮想環境をアクティベート
source venv_linux/bin/activate

# パッケージインストール
pip install -r requirements.txt
```

#### 2. パス関連エラー
```bash
エラー: FileNotFoundError

解決策:
# 正しいディレクトリに移動
cd /mnt/c/Users/kenny/sandbox/NeuroHub

# PYTHONPATHを設定
export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub
```

#### 3. 権限エラー
```bash
エラー: PermissionError

解決策:
# ファイル権限を確認
ls -la agents/

# 実行権限を付与
chmod +x agents/agent_*.py
```

#### 4. 仮想環境エラー
```bash
エラー: Command not found: python

解決策:
# 仮想環境再作成
python3 -m venv venv_linux
source venv_linux/bin/activate
pip install -r requirements.txt
```

### パフォーマンス最適化

#### 1. プロバイダー選択
```bash
# 高速・高品質（制限あり）
--provider gemini

# 中速・安定
--provider huggingface

# 低速・無制限（ローカル）
--provider ollama
```

#### 2. 実行時間短縮
```bash
# 統一インターフェース経由（推奨）
python main.py "質問"

# 直接実行（開発・デバッグ用）
python agents/agent_llm.py "質問"
```

## 📊 ログとモニタリング

### ログファイル場所
```bash
logs/
├── neurohub_YYYYMMDD.log    # メインログ
├── mcp.log                  # MCPエージェントログ
├── database.log             # データベースログ
└── weather_agent.log        # 天気エージェントログ
```

### ログ確認方法
```bash
# 今日のメインログ
tail -f logs/neurohub_$(date +%Y%m%d).log

# MCPエージェントログ
tail -f logs/mcp.log

# 全ログ概要
ls -la logs/
```

## 🎯 実践例

### 1. 開発ワークフロー
```bash
# 1. アイデアから設計書作成
python main.py "ToDoアプリの設計書を作成" --force-agent mcp

# 2. プロジェクト作成
python agents/agent_mcp.py project "ToDoアプリ実装"

# 3. コード最適化
python agents/agent_mcp.py optimize "生成されたコードを改善"

# 4. Gitコミット
python main.py "変更をコミット" --force-agent git
```

### 2. 調査・学習ワークフロー
```bash
# 1. 基本的な質問（AI回答）
python main.py "Pythonとは何ですか？"

# 2. 詳細調査（Web検索付き）
python main.py "Python最新バージョンの新機能"

# 3. 技術的な質問
python main.py "FastAPIとFlaskの違い" --force-agent llm
```

### 3. プロジェクト管理ワークフロー
```bash
# 1. 現在の状況確認
python main.py "gitステータス確認" --force-agent git

# 2. コード生成
python agents/agent_mcp.py generate "設定ファイル作成"

# 3. 変更をコミット
python agents/agent_git.py "add . && commit -m 'feat: 設定ファイル追加'"

# 4. プッシュ
python agents/agent_git.py "push origin aidev"
```

## 📚 参考資料

- [NeuroHub アーキテクチャ設計書](./ARCHITECTURE_DESIGN.md)
- [タスク管理](./TASK_MANAGEMENT.md)
- [MCPマニュアルガイド](./MCP_MANUAL_GUIDE.md)
- [Docker セットアップガイド](./DOCKER_SETUP.md)

---

*最終更新: 2025年11月3日*
*WSL環境での動作を前提として作成*
