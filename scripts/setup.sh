#!/bin/bash
# -*- coding: utf-8 -*-
"""
NeuroHub 統合セットアップスクリプト
Linux/WSL/Mac環境対応
"""

set -e  # エラー時に停止

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ロゴ表示
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ██╗  ██╗  ║
║   ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██║  ██║  ║
║   ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║███████║  ║
║   ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══██║  ║
║   ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║  ██║  ║
║   ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝  ║
║                                                           ║
║        Multi-LLM AI Assistant Platform Setup             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}🚀 NeuroHub セットアップ開始...${NC}\n"

# プロジェクトルート
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# ===== 1. 環境確認 =====
echo -e "${BLUE}📋 Step 1/7: 環境確認${NC}"
echo "   OS: $(uname -s)"
echo "   Architecture: $(uname -m)"
echo "   Python: $(python3 --version 2>/dev/null || echo '未インストール')"
echo "   Git: $(git --version 2>/dev/null || echo '未インストール')"
echo

# Pythonバージョンチェック
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+' || echo "0.0")
REQUIRED_VERSION="3.9"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python 3.9以上が必要です。現在: $PYTHON_VERSION${NC}"
    exit 1
fi

# ===== 2. 必要パッケージインストール =====
echo -e "${BLUE}📦 Step 2/7: システムパッケージ確認${NC}"

if command -v apt &> /dev/null; then
    # Debian/Ubuntu系
    echo "   Debian/Ubuntu系を検出"
    REQUIRED_PKGS="python3-pip python3-venv git curl sqlite3 build-essential portaudio19-dev"
    
    for pkg in $REQUIRED_PKGS; do
        if ! dpkg -l | grep -q "^ii  $pkg"; then
            echo -e "${YELLOW}   ⚠️ $pkg をインストール中...${NC}"
            sudo apt update -qq
            sudo apt install -y $pkg
        fi
    done
elif command -v yum &> /dev/null; then
    # RHEL/CentOS系
    echo "   RHEL/CentOS系を検出"
    sudo yum install -y python3-pip python3-devel git curl sqlite gcc portaudio-devel
elif command -v brew &> /dev/null; then
    # macOS
    echo "   macOS を検出"
    brew install python3 git curl sqlite3 portaudio
fi

echo -e "${GREEN}   ✅ システムパッケージ準備完了${NC}\n"

# ===== 3. Python仮想環境 =====
echo -e "${BLUE}📦 Step 3/7: Python仮想環境セットアップ${NC}"

VENV_DIR="venv_linux"
if [ "$(uname)" == "Darwin" ]; then
    VENV_DIR="venv_mac"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "   仮想環境を作成中: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}   ✅ 仮想環境作成完了${NC}"
else
    echo "   仮想環境は既に存在します"
fi

# 仮想環境アクティベート
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}   ✅ 仮想環境アクティベート完了${NC}\n"

# ===== 4. Python依存関係 =====
echo -e "${BLUE}📚 Step 4/7: Python依存関係インストール${NC}"

echo "   pip をアップグレード中..."
pip install --upgrade pip -q

echo "   requirements.txt からインストール中..."
pip install -r requirements.txt -q

if [ -f "requirements-dev.txt" ]; then
    echo "   requirements-dev.txt からインストール中..."
    pip install -r requirements-dev.txt -q
fi

echo -e "${GREEN}   ✅ Python依存関係インストール完了${NC}\n"

# ===== 5. 環境変数設定 =====
echo -e "${BLUE}⚙️  Step 5/7: 環境変数設定${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "   .env ファイルを作成中..."
        cp .env.example .env
        echo -e "${YELLOW}   ⚠️ .env ファイルを編集してAPI Keyを設定してください！${NC}"
    else
        echo -e "${RED}   ❌ .env.example が見つかりません${NC}"
    fi
else
    echo "   .env ファイルは既に存在します"
fi

echo -e "${GREEN}   ✅ 環境変数設定完了${NC}\n"

# ===== 6. データベース初期化 =====
echo -e "${BLUE}💾 Step 6/7: データベース初期化${NC}"

if [ -f "scripts/init_database.py" ]; then
    echo "   データベーステーブルを作成中..."
    python3 scripts/init_database.py
    echo -e "${GREEN}   ✅ データベース初期化完了${NC}"
else
    echo -e "${YELLOW}   ⚠️ init_database.py が見つかりません${NC}"
fi
echo

# ===== 7. 実行権限設定 =====
echo -e "${BLUE}🔐 Step 7/7: 実行権限設定${NC}"

# スクリプトに実行権限付与
find scripts -type f -name "*.sh" -exec chmod +x {} \;
find tools -type f -name "*" ! -name "*.md" -exec chmod +x {} \;

echo -e "${GREEN}   ✅ 実行権限設定完了${NC}\n"

# ===== 完了メッセージ =====
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          🎉 NeuroHub セットアップ完了！ 🎉                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${YELLOW}📋 次のステップ:${NC}\n"

echo -e "  ${BLUE}1. API Key設定${NC}"
echo "     .env ファイルを編集して以下を設定:"
echo "     - GEMINI_API_KEY (https://aistudio.google.com/app/apikey)"
echo "     - HUGGINGFACE_API_KEY (https://huggingface.co/settings/tokens)"
echo "     - OLLAMA_HOST (デフォルト: http://localhost:11434)"
echo

echo -e "  ${BLUE}2. 仮想環境アクティベート${NC}"
echo "     source $VENV_DIR/bin/activate"
echo

echo -e "  ${BLUE}3. 基本的な使い方${NC}"
echo "     # メインアプリケーション起動"
echo "     python3 main.py"
echo
echo "     # Git コミット支援"
echo "     ./tools/git_commit_ai"
echo
echo "     # 天気予報"
echo "     python3 -m services.agent.weather_agent 東京"
echo
echo "     # Web解析"
echo "     python3 -m services.agent.web_agent <URL> <質問>"
echo

echo -e "  ${BLUE}4. テスト実行${NC}"
echo "     python3 -m pytest tests/ -v"
echo

echo -e "  ${BLUE}5. Docker起動（推奨）${NC}"
echo "     docker-compose up -d"
echo "     docker-compose logs -f neurohub"
echo

echo -e "${GREEN}🚀 NeuroHubをお楽しみください！${NC}\n"
