# NeuroHub Linux 開発コマンドガイド

## 🐧 Linux環境でのNeuroHub開発・実行コマンド集

### 📦 初期セットアップ

```bash
# 1. リポジトリクローン
git clone https://github.com/messpy/NeuroHub.git
cd NeuroHub

# 2. 仮想環境セットアップ
python3 -m venv venv
source venv/bin/activate

# 3. 依存関係インストール
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 実行権限設定
chmod +x run_tests_linux.sh
chmod +x tools/git_commit_ai
find . -name "*.py" -exec chmod +x {} \;

# 5. 環境変数設定 (~/.bashrcに追加)
echo 'export NEUROHUB_HOME=$(pwd)' >> ~/.bashrc
echo 'export PYTHONPATH=$NEUROHUB_HOME:$PYTHONPATH' >> ~/.bashrc
echo 'export LC_ALL=C.UTF-8' >> ~/.bashrc
echo 'export LANG=C.UTF-8' >> ~/.bashrc
source ~/.bashrc
```

---

## 🤖 エージェント実行コマンド

### CommandAgent - システムコマンド実行
```bash
# 基本実行
python3 agents/command_agent.py --help

# システム情報取得
python3 agents/command_agent.py --command "uname -a"

# ディレクトリ一覧
python3 agents/command_agent.py --command "ls -la" --cwd /home/user

# 安全モード（危険コマンド制限）
python3 agents/command_agent.py --command "ls" --safe-mode

# ログ出力付き
python3 agents/command_agent.py --command "pwd" --verbose --log-file /tmp/neurohub.log
```

### GitAgent - Git操作
```bash
# Git状態確認
python3 agents/git_agent.py --status

# コミット作成
python3 agents/git_agent.py --commit "Update documentation" --add-all

# ブランチ作成・切り替え
python3 agents/git_agent.py --create-branch feature/new-agent
python3 agents/git_agent.py --checkout feature/new-agent

# ログ確認
python3 agents/git_agent.py --log --limit 5

# プッシュ
python3 agents/git_agent.py --push origin main
```

### LLMAgent - AI応答生成
```bash
# Ollama使用（ローカル）
python3 agents/llm_agent.py --prompt "Hello, how are you?" --provider ollama --model llama2

# Gemini使用（要APIキー）
python3 agents/llm_agent.py --prompt "Explain quantum computing" --provider gemini --model gemini-1.5-flash

# HuggingFace使用
python3 agents/llm_agent.py --prompt "Code review this Python function" --provider huggingface --model gpt2

# 設定付き実行
python3 agents/llm_agent.py --prompt "Write a haiku" --temperature 0.9 --max-tokens 100 --verbose
```

### ConfigAgent - 設定管理
```bash
# 設定読み込み
python3 agents/config_agent.py --load config/config.yaml

# 設定値取得
python3 agents/config_agent.py --get agents.llm_agent.enabled

# 設定値変更
python3 agents/config_agent.py --set agents.llm_agent.default_provider=ollama

# 設定検証
python3 agents/config_agent.py --validate

# 設定バックアップ
python3 agents/config_agent.py --backup /tmp/config_backup.yaml
```

---

## 🔧 サービス実行コマンド

### LLMサービス
```bash
# LLMサービス直接実行
python3 services/llm/llm_cli.py --provider ollama --model llama2 --prompt "Hello Linux!"

# プロバイダーテスト
python3 services/llm/provider_ollama.py --test-connection
python3 services/llm/provider_gemini.py --test-models

# 対話モード
python3 services/llm/llm_cli.py --interactive --provider ollama
```

### データベースサービス
```bash
# SQLiteデータベース初期化
python3 services/db/sqlite_tool.py --init --db-path /var/lib/neurohub/neurohub.db

# データベースクエリ実行
python3 services/db/sqlite_tool.py --query "SELECT * FROM llm_history LIMIT 5"

# バックアップ作成
python3 services/db/sqlite_tool.py --backup /tmp/neurohub_backup.db

# LLM履歴管理
python3 services/db/llm_history_manager.py --add --prompt "Test" --response "OK"
```

### MCPサービス（Model Context Protocol）
```bash
# MCP実行
python3 services/mcp/mcp_run.py "こんにちはをprintして"

# コード生成
python3 services/mcp/mcp_codegen.py --prompt "Create a Python function to calculate fibonacci"

# テスト実行
python3 services/mcp/mcp_test.py --run-all
```

---

## 🧪 テスト・開発コマンド

### テスト実行
```bash
# Linux最適化テスト実行
./run_tests_linux.sh

# 特定テストファイル実行
python3 -m pytest tests/agents/test_git_agent.py -v

# カバレッジレポート生成
python3 -m pytest tests/ --cov=agents --cov=services --cov-report=html

# テスト詳細ログ
python3 -m pytest tests/ -v --tb=long --capture=no

# パフォーマンステスト
python3 -m pytest tests/ --durations=10
```

### デバッグ・ログ
```bash
# デバッグモード実行
python3 agents/llm_agent.py --prompt "test" --debug

# ログファイル確認
tail -f /var/log/neurohub/neurohub.log

# 環境変数確認
python3 -c "import os; print('NEUROHUB_HOME:', os.getenv('NEUROHUB_HOME'))"
```

### 開発ツール
```bash
# コード品質チェック
python3 -m flake8 agents/ services/ --max-line-length=100

# タイプチェック
python3 -m mypy agents/ services/

# フォーマット
python3 -m black agents/ services/ tests/

# import整理
python3 -m isort agents/ services/ tests/
```

---

## 🛠️ ユーティリティコマンド

### Git支援ツール
```bash
# AI支援Git コミット
./tools/git_commit_ai --auto --scope agents

# Git統計
./tools/git_utils --stats --since "1 week ago"

# ブランチクリーンアップ
./tools/git_utils --cleanup-branches
```

### システム管理
```bash
# プロセス確認
ps aux | grep neurohub

# ポート確認（Ollama）
netstat -tlnp | grep :11434

# ディスク使用量
du -sh /var/lib/neurohub/

# ログローテーション
logrotate -f /etc/logrotate.d/neurohub
```

---

## 🚀 よく使う開発ワークフロー

### 1. 新機能開発
```bash
# ブランチ作成
python3 agents/git_agent.py --create-branch feature/new-feature

# 開発
vim agents/new_agent.py

# テスト作成
vim tests/agents/test_new_agent.py

# テスト実行
python3 -m pytest tests/agents/test_new_agent.py -v

# コミット
python3 agents/git_agent.py --commit "Add new agent" --add-all
```

### 2. バグ修正
```bash
# 問題箇所特定
python3 agents/llm_agent.py --prompt "debug this" --debug --verbose

# テスト実行（失敗確認）
python3 -m pytest tests/ -x --tb=short

# 修正
vim agents/target_agent.py

# テスト再実行
python3 -m pytest tests/ -v

# コミット
./tools/git_commit_ai --type fix --scope agents
```

### 3. 設定調整
```bash
# 現在設定確認
python3 agents/config_agent.py --get

# 設定変更
python3 agents/config_agent.py --set services.ollama.base_url=http://192.168.1.100:11434

# 設定テスト
python3 services/llm/provider_ollama.py --test-connection

# 設定コミット
python3 agents/git_agent.py --commit "Update Ollama configuration"
```

---

## 📊 監視・運用コマンド

### リアルタイム監視
```bash
# システムリソース監視
htop

# ログ監視
tail -f /var/log/neurohub/neurohub.log | grep ERROR

# ネットワーク監視
watch -n 1 'netstat -tlnp | grep :11434'
```

### 定期メンテナンス
```bash
# データベース最適化
python3 services/db/sqlite_tool.py --vacuum

# ログクリーンアップ
find /var/log/neurohub/ -name "*.log" -mtime +7 -delete

# モデルアップデート
ollama pull llama2:latest
```

---

## 🆘 トラブルシューティング

### 権限問題
```bash
# 実行権限確認・修正
ls -la agents/
chmod +x agents/*.py

# ディレクトリ権限修正
sudo chown -R $USER:$USER /var/lib/neurohub
chmod -R 755 /var/lib/neurohub
```

### 依存関係問題
```bash
# 仮想環境再作成
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# パッケージアップデート
pip install --upgrade -r requirements.txt
```

### サービス問題
```bash
# Ollamaサービス確認
sudo systemctl status ollama
sudo systemctl restart ollama

# ポート確認
sudo lsof -i :11434
```

---

*このガイドに沿ってLinux環境でNeuroHubを快適に開発・運用できます！*
