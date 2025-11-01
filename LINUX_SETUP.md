# Linux Environment Configuration for NeuroHub

## 🐧 Linuxベース環境設定

### システム要件
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv git

# CentOS/RHEL
sudo yum install python3 python3-pip git

# Arch Linux
sudo pacman -S python python-pip git
```

### 仮想環境セットアップ
```bash
# 仮想環境作成
python3 -m venv venv

# アクティベート
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 権限設定 (Linux)
```bash
# 実行権限設定
chmod +x run_tests_linux.sh
chmod +x tools/git_commit_ai

# ディレクトリ権限設定
chmod 755 agents/ services/ tools/
chmod 644 config/*.yaml

# データディレクトリ作成 (システム全体用)
sudo mkdir -p /var/lib/neurohub
sudo chown $USER:$USER /var/lib/neurohub
chmod 755 /var/lib/neurohub
```

### 環境変数設定
```bash
# ~/.bashrc または ~/.zshrc に追加
export NEUROHUB_HOME=/home/$USER/neurohub
export NEUROHUB_DATA=/var/lib/neurohub
export PYTHONPATH=$NEUROHUB_HOME:$PYTHONPATH
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# API キー設定 (オプション)
export GEMINI_API_KEY="your_gemini_api_key"
export HUGGINGFACE_API_TOKEN="your_hf_token"
```

### Git設定
```bash
# グローバル設定
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main

# NeuroHub用設定
git config --global neurohub.agent.name "NeuroHub Agent"
git config --global neurohub.agent.email "agent@neurohub.local"
```

### Ollama セットアップ (Linux)
```bash
# Ollama インストール
curl -fsSL https://ollama.ai/install.sh | sh

# サービス開始
sudo systemctl start ollama
sudo systemctl enable ollama

# モデルダウンロード
ollama pull llama2
ollama pull codellama
```

### テスト実行
```bash
# Linux専用テストスクリプト実行
./run_tests_linux.sh

# または直接pytest実行
python -m pytest tests/ -v --cov=agents --cov=services
```
