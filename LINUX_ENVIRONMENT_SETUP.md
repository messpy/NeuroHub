# NeuroHub Linux環境セットアップガイド

## 🐧 真のLinux環境でNeuroHubを実行する方法

現在Windows環境でLinuxコマンドを実行しようとしてエラーが発生しています。
NeuroHubはLinuxベースで設計されているため、以下のいずれかの方法で真のLinux環境を用意してください。

---

## 🔧 方法1: WSL (Windows Subsystem for Linux) 推奨

### WSLのインストール
```powershell
# PowerShellを管理者として実行
wsl --install
# または特定のディストリビューション
wsl --install -d Ubuntu
```

### WSL内でのNeuroHub設定
```bash
# WSLにアクセス
wsl

# 必要パッケージインストール
sudo apt update
sudo apt install python3 python3-pip python3-venv git curl

# NeuroHubプロジェクトをWSL内にコピー
cp -r /mnt/c/Users/kenny/sandbox/NeuroHub ~/neurohub
cd ~/neurohub

# 仮想環境セットアップ
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 実行権限設定
chmod +x quick_start_linux.sh
chmod +x run_tests_linux.sh
chmod +x tools/git_commit_ai

# クイックスタート実行
./quick_start_linux.sh
```

---

## 🔧 方法2: Docker Linux コンテナ

### Dockerfileの作成
```dockerfile
FROM ubuntu:22.04

# 基本パッケージインストール
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /neurohub

# プロジェクトファイルコピー
COPY . .

# Python依存関係インストール
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# 実行権限設定
RUN chmod +x quick_start_linux.sh run_tests_linux.sh tools/git_commit_ai

# デフォルトコマンド
CMD ["bash"]
```

### Docker実行
```bash
# イメージビルド
docker build -t neurohub-linux .

# コンテナ実行
docker run -it neurohub-linux

# コンテナ内でNeuroHub実行
source venv/bin/activate
./quick_start_linux.sh
```

---

## 🔧 方法3: VirtualBox Linux VM

### Ubuntu VMセットアップ
1. VirtualBoxをダウンロード・インストール
2. Ubuntu 22.04 LTS ISOをダウンロード
3. 新規VM作成（メモリ4GB以上推奨）
4. Ubuntu インストール

### VM内でのNeuroHub設定
```bash
# Git設定
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# NeuroHubクローン
git clone https://github.com/messpy/NeuroHub.git
cd NeuroHub

# 環境セットアップ
chmod +x quick_start_linux.sh
./quick_start_linux.sh
```

---

## 🔧 方法4: GitHub Codespaces (クラウド)

### Codespacesでの実行
1. GitHubでNeuroHubリポジトリにアクセス
2. "Code" → "Codespaces" → "Create codespace"
3. VSCode in browserが開く

```bash
# Codespace内で実行
chmod +x quick_start_linux.sh
./quick_start_linux.sh

# エージェント実行例
python3 agents/git_agent.py --status
python3 agents/llm_agent.py --prompt "Hello from Codespaces!"
```

---

## 🚀 推奨セットアップ手順（WSL使用）

### 1. WSL Ubuntu インストール
```powershell
# PowerShell（管理者）で実行
wsl --install -d Ubuntu-22.04
# 再起動後、Ubuntuユーザー作成
```

### 2. WSL Ubuntu 内でNeuroHubセットアップ
```bash
# WSL Ubuntu起動
wsl

# システム更新
sudo apt update && sudo apt upgrade -y

# 必要パッケージインストール
sudo apt install -y python3 python3-pip python3-venv git curl build-essential

# NeuroHubプロジェクトコピー
mkdir -p ~/projects
cp -r /mnt/c/Users/kenny/sandbox/NeuroHub ~/projects/neurohub
cd ~/projects/neurohub

# Linux環境でのセットアップ
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 実行権限設定
chmod +x *.sh tools/*

# 環境変数設定
echo 'export NEUROHUB_HOME=~/projects/neurohub' >> ~/.bashrc
echo 'export PYTHONPATH=$NEUROHUB_HOME:$PYTHONPATH' >> ~/.bashrc
echo 'export LC_ALL=C.UTF-8' >> ~/.bashrc
echo 'export LANG=C.UTF-8' >> ~/.bashrc
source ~/.bashrc
```

### 3. Ollama インストール（オプション）
```bash
# Ollama for Linux
curl -fsSL https://ollama.ai/install.sh | sh

# モデルダウンロード
ollama pull llama2
ollama pull codellama
```

### 4. NeuroHub実行確認
```bash
# クイックスタート
./quick_start_linux.sh

# 個別エージェント実行
python3 agents/git_agent.py --status
python3 agents/command_agent.py --command "uname -a"
python3 agents/config_agent.py --validate

# テスト実行
./run_tests_linux.sh
```

---

## 📋 現在の問題の原因

```
$ python -v
did not find executable at '/usr/bin\python.exe': ????????????????
```

この問題は以下が原因です：

1. **Windows環境でLinuxパスを参照**: `/usr/bin\python.exe` は存在しない
2. **PowerShell環境**: Linux bash ではなくWindows PowerShell
3. **パス区切り文字混在**: `/` と `\` が混在
4. **Linux専用コマンド**: `ls -la`, `which`, `python3` が Windows で認識されない

## ✅ 解決方法

**最も簡単**: WSL Ubuntu をインストールして、そこでNeuroHubを実行する

```bash
# WSLで正しく動作する例
wsl
cd ~/projects/neurohub
source venv/bin/activate
python3 --version  # Python 3.x.x
python3 agents/git_agent.py --status  # 正常動作
```

これでLinux環境でNeuroHubが期待通りに動作します！
