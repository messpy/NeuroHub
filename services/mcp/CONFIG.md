# MCP設定ガイド

## 📋 概要

MCPモジュールの設定方法と環境構築ガイドです。

## 🔧 LLM設定

### 設定ファイル

MCPは以下の設定ファイルを使用：

1. **`config/llm_config.yaml`**: グローバルLLM設定
2. **`services/ai/config/llm_config.yaml`**: AI専用設定
3. **`.env`**: API キー管理

### llm_config.yaml 構造

```yaml
# デフォルトプロバイダー
default_provider: ollama

# プロバイダー設定
providers:
  ollama:
    base_url: "http://localhost:11434"
    default_model: "llama3.2:latest"
    timeout: 120

  gemini:
    api_key: "${GEMINI_API_KEY}"  # .envから読み込み
    default_model: "gemini-2.5-flash"
    timeout: 60

  huggingface:
    api_key: "${HUGGINGFACE_API_KEY}"
    base_url: "https://router.huggingface.co/v1"
    default_model: "openai/gpt-oss-20b:groq"
    timeout: 60

# プロンプトテンプレート
prompts:
  system_default: "あなたは親切なAIアシスタントです。"
  coding_assistant: "あなたは優秀なプログラマーです。Pythonコードを生成してください。"
  debug_assistant: "コードのエラーを修正してください。"
```

### .env ファイル

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# HuggingFace API
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Ollama設定（ローカル実行時）
OLLAMA_BASE_URL=http://localhost:11434

# データベース設定
DB_PATH=data/neurohub.db

# ログ設定
LOG_LEVEL=INFO
LOG_PATH=logs/
```

## 🚀 初期セットアップ

### 1. WSL環境構築

```bash
# WSLインストール（Windows PowerShell管理者権限）
wsl --install

# Ubuntu起動
wsl

# Python環境確認
python3 --version  # Python 3.11以上推奨
```

### 2. 仮想環境作成

```bash
# NeuroHubディレクトリに移動
cd /mnt/c/Users/kenny/sandbox/NeuroHub

# 仮想環境作成
python3 -m venv venv_linux

# 仮想環境有効化
source venv_linux/bin/activate

# 依存関係インストール
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Ollamaセットアップ

```bash
# Ollamaインストール（Linux/WSL）
curl -fsSL https://ollama.com/install.sh | sh

# Ollama起動
ollama serve &

# モデルダウンロード
ollama pull llama3.2:latest
ollama pull qwen2.5-coder:7b
```

### 4. API キー設定

```bash
# .envファイル作成
cp .env.example .env

# エディタで編集
nano .env

# 以下を設定
# GEMINI_API_KEY=your_key
# HUGGINGFACE_API_KEY=your_key
```

## 🧪 動作確認

### LLMプロバイダーテスト

```bash
# WSL仮想環境で実行
source venv_linux/bin/activate

# Ollamaテスト
python3 -m pytest tests/test_provider_ollama.py -v

# Geminiテスト
python3 -m pytest tests/test_provider_gemini.py -v

# HuggingFaceテスト
python3 -m pytest tests/test_provider_huggingface.py -v

# 全プロバイダーテスト
python3 -m pytest tests/test_provider_*.py -v
```

### MCP機能テスト

```bash
# MCP自動プロジェクト生成テスト
python3 -m services.mcp.auto_project_generator --test

# MCP自動デバッグテスト
python3 -m services.mcp.auto_debugger --test
```

## 📁 データベース設定

### 初期化

```python
from services.db.db_initializer import DBInitializer

# データベース初期化
initializer = DBInitializer()
initializer.initialize_all_tables()
```

### テーブル構造

```sql
-- ユーザー情報
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM履歴
CREATE TABLE llm_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知識ベース
CREATE TABLE knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔍 トラブルシューティング

### よくある問題

#### 1. Ollamaが起動しない

**症状**: `ConnectionError: Ollama server not running`

**解決**:
```bash
# Ollamaプロセス確認
ps aux | grep ollama

# Ollama起動
ollama serve &

# ポート確認
netstat -tulpn | grep 11434
```

#### 2. Gemini APIエラー

**症状**: `HTTP 401: Invalid API key`

**解決**:
```bash
# .env確認
cat .env | grep GEMINI_API_KEY

# API キー再設定
export GEMINI_API_KEY="your_new_key"
```

#### 3. WSL仮想環境が見つからない

**症状**: `venv_linux/bin/activate: No such file`

**解決**:
```bash
# 仮想環境再作成
python3 -m venv venv_linux

# 依存関係再インストール
source venv_linux/bin/activate
pip install -r requirements.txt
```

#### 4. pytest実行時のカバレッジエラー

**症状**: `Coverage failure: total of 3% is less than fail-under=40%`

**解決**:
```bash
# カバレッジ無効化して実行
pytest tests/ --no-cov -v

# または特定テストのみ実行
pytest tests/test_provider_ollama.py --no-cov -v
```

## ⚙️ 高度な設定

### プロバイダー優先順位設定

```yaml
# llm_config.yaml
provider_priority:
  - ollama      # 第1優先（ローカル、無制限）
  - huggingface # 第2優先（無料、Router API）
  - gemini      # 第3優先（高品質、1日250回制限）

# フォールバック設定
fallback:
  enabled: true
  max_retries: 3
  retry_delay: 1  # 秒
```

### プロンプト最適化設定

```yaml
# prompt_optimizer設定
prompt_optimization:
  enabled: true
  max_tokens: 4096
  temperature: 0.7
  top_p: 0.9

  # コンテキスト圧縮
  compression:
    enabled: true
    max_context_length: 2000
    strategy: "truncate"  # truncate / summarize
```

### MCP自動デバッグ設定

```yaml
# auto_debugger設定
auto_debugger:
  max_retries: 5
  timeout: 300  # 秒

  # エラー検知パターン
  error_patterns:
    - "SyntaxError"
    - "IndentationError"
    - "NameError"
    - "TypeError"

  # 修正手法
  fix_strategies:
    - "syntax_check"
    - "import_fix"
    - "indentation_fix"
    - "type_fix"
```

## 📚 参考リンク

- [Ollama公式](https://ollama.com/)
- [Gemini API](https://ai.google.dev/)
- [HuggingFace Router](https://router.huggingface.co/)
- [Python-dotenv](https://github.com/theskumar/python-dotenv)

## 🔄 更新履歴

- **2025-11-02**: 初版作成
  - 基本設定ガイド
  - トラブルシューティング追加
