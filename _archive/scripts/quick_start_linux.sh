#!/bin/bash
# NeuroHub Quick Start Script for Linux
# Linux環境でのNeuroHub クイックスタートスクリプト

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ロゴ表示
echo -e "${BLUE}"
cat << 'EOF'
 _   _                      _   _       _
| \ | | ___ _   _ _ __ ___ | | | |_   _| |__
|  \| |/ _ \ | | | '__/ _ \| |_| | | | | '_ \
| |\  |  __/ |_| | | | (_) |  _  | |_| | |_) |
|_| \_|\___|\__,_|_|  \___/|_| |_|\__,_|_.__/

Linux Quick Start Guide
EOF
echo -e "${NC}"

echo -e "${CYAN}🐧 NeuroHub Linux環境 クイックスタートガイド${NC}"
echo "=============================================="

# 環境チェック関数
check_environment() {
    echo -e "\n${BLUE}📋 環境チェック${NC}"
    echo "----------------"

    # OS確認
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "✅ ${GREEN}Linux環境確認済み${NC}"
        echo "   Distribution: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown')"
    else
        echo -e "⚠️  ${YELLOW}Linux以外の環境です${NC}"
    fi

    # Python確認
    if command -v python3 &> /dev/null; then
        echo -e "✅ ${GREEN}Python3: $(python3 --version)${NC}"
    else
        echo -e "❌ ${RED}Python3が見つかりません${NC}"
        echo -e "   ${YELLOW}インストール: sudo apt-get install python3 python3-pip python3-venv${NC}"
        return 1
    fi

    # Git確認
    if command -v git &> /dev/null; then
        echo -e "✅ ${GREEN}Git: $(git --version)${NC}"
    else
        echo -e "❌ ${RED}Gitが見つかりません${NC}"
        echo -e "   ${YELLOW}インストール: sudo apt-get install git${NC}"
        return 1
    fi

    return 0
}

# セットアップ実行
setup_neurohub() {
    echo -e "\n${BLUE}🚀 NeuroHub セットアップ${NC}"
    echo "------------------------"

    # 仮想環境作成
    if [[ ! -d "venv" ]]; then
        echo -e "${YELLOW}仮想環境を作成中...${NC}"
        python3 -m venv venv
        echo -e "✅ ${GREEN}仮想環境作成完了${NC}"
    else
        echo -e "✅ ${GREEN}仮想環境が既に存在します${NC}"
    fi

    # 仮想環境アクティベート
    echo -e "${YELLOW}仮想環境をアクティベート中...${NC}"
    source venv/bin/activate
    echo -e "✅ ${GREEN}仮想環境アクティベート完了${NC}"

    # 依存関係インストール
    echo -e "${YELLOW}依存関係をインストール中...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    echo -e "✅ ${GREEN}依存関係インストール完了${NC}"

    # 実行権限設定
    echo -e "${YELLOW}実行権限を設定中...${NC}"
    chmod +x run_tests_linux.sh 2>/dev/null || true
    chmod +x tools/git_commit_ai 2>/dev/null || true
    find . -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
    echo -e "✅ ${GREEN}実行権限設定完了${NC}"

    # 環境変数設定
    export NEUROHUB_HOME=$(pwd)
    export PYTHONPATH=$NEUROHUB_HOME:$PYTHONPATH
    export LC_ALL=C.UTF-8
    export LANG=C.UTF-8
    echo -e "✅ ${GREEN}環境変数設定完了${NC}"
}

# 使用例表示
show_examples() {
    echo -e "\n${PURPLE}💡 よく使うコマンド例${NC}"
    echo "===================="

    echo -e "\n${CYAN}🤖 エージェント実行:${NC}"
    echo "  python3 agents/git_agent.py --status"
    echo "  python3 agents/llm_agent.py --prompt 'Hello Linux!' --provider ollama"
    echo "  python3 agents/command_agent.py --command 'ls -la'"

    echo -e "\n${CYAN}🧪 テスト実行:${NC}"
    echo "  ./run_tests_linux.sh"
    echo "  python3 -m pytest tests/ -v"

    echo -e "\n${CYAN}🔧 開発ツール:${NC}"
    echo "  python3 -m flake8 agents/ services/"
    echo "  python3 -m black agents/ services/"

    echo -e "\n${CYAN}📊 設定管理:${NC}"
    echo "  python3 agents/config_agent.py --get"
    echo "  python3 agents/config_agent.py --validate"
}

# メニュー表示
show_menu() {
    echo -e "\n${PURPLE}🎯 クイックアクション${NC}"
    echo "=================="
    echo "1) エージェントテスト実行"
    echo "2) Git状態確認"
    echo "3) LLM動作テスト (Ollama)"
    echo "4) 設定確認"
    echo "5) 全テスト実行"
    echo "q) 終了"
    echo
    read -p "選択してください [1-5, q]: " choice

    case $choice in
        1)
            echo -e "\n${YELLOW}エージェントテスト実行中...${NC}"
            python3 -m pytest tests/agents/ -v --tb=short
            ;;
        2)
            echo -e "\n${YELLOW}Git状態確認中...${NC}"
            python3 agents/git_agent.py --status
            ;;
        3)
            echo -e "\n${YELLOW}LLM動作テスト中...${NC}"
            if command -v ollama &> /dev/null; then
                python3 agents/llm_agent.py --prompt "Hello from Linux!" --provider ollama --model llama2 2>/dev/null || \
                echo -e "${RED}Ollamaが起動していないか、モデルがインストールされていません${NC}"
            else
                echo -e "${YELLOW}Ollama未インストール。Geminiで試行...${NC}"
                python3 agents/llm_agent.py --prompt "Hello from Linux!" --provider gemini 2>/dev/null || \
                echo -e "${RED}API キーが設定されていません${NC}"
            fi
            ;;
        4)
            echo -e "\n${YELLOW}設定確認中...${NC}"
            python3 agents/config_agent.py --validate
            ;;
        5)
            echo -e "\n${YELLOW}全テスト実行中...${NC}"
            ./run_tests_linux.sh
            ;;
        q|Q)
            echo -e "${GREEN}NeuroHub クイックスタートを終了します${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}無効な選択です${NC}"
            ;;
    esac
}

# メイン実行
main() {
    # 環境チェック
    if ! check_environment; then
        echo -e "\n${RED}❌ 環境要件が満たされていません${NC}"
        echo -e "${YELLOW}📋 必要な環境:${NC}"
        echo "  - Linux OS"
        echo "  - Python 3.7+"
        echo "  - Git"
        echo "  - pip, venv"
        exit 1
    fi

    # セットアップ実行
    setup_neurohub

    # 使用例表示
    show_examples

    # インタラクティブメニュー
    while true; do
        show_menu
        echo
        read -p "続けますか？ [y/N]: " continue_choice
        if [[ ! $continue_choice =~ ^[Yy] ]]; then
            break
        fi
    done

    echo -e "\n${GREEN}🎉 NeuroHub Linux クイックスタート完了！${NC}"
    echo -e "${CYAN}詳細なコマンドガイド: LINUX_COMMANDS.md${NC}"
    echo -e "${CYAN}インターフェース設計: docs/INTERFACE_DESIGN.md${NC}"
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
