#!/bin/bash
# -*- coding: utf-8 -*-
"""
NeuroHub Linux環境セットアップ＆ファイル整理スクリプト
Linux環境に最適化し、不要ファイルを整理
"""

echo "🐧 NeuroHub Linux環境セットアップ開始..."
echo "================================================"

# 1. 環境確認
echo "📋 環境確認:"
echo "   OS: $(uname -a)"
echo "   Python: $(python3 --version 2>/dev/null || echo 'Python3未インストール')"
echo "   Git: $(git --version 2>/dev/null || echo 'Git未インストール')"
echo

# 2. 必要パッケージインストール（Ubuntu/Debian）
if command -v apt &> /dev/null; then
    echo "📦 システムパッケージ更新..."
    sudo apt update && sudo apt upgrade -y

    echo "🔧 必要パッケージインストール..."
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        build-essential \
        sqlite3 \
        jq
fi

# 3. Python仮想環境セットアップ
echo "🐍 Python仮想環境セットアップ..."
if [ ! -d "venv_linux" ]; then
    python3 -m venv venv_linux
    echo "✅ 仮想環境作成完了"
else
    echo "ℹ️ 仮想環境既存"
fi

source venv_linux/bin/activate

# 4. Python依存関係インストール
echo "📚 Python依存関係インストール..."
pip install --upgrade pip
pip install -r requirements.txt
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
fi

# 5. データベース初期化
echo "💾 データベース初期化..."
python3 setup_database.py

# 6. 実行権限設定
echo "🔐 実行権限設定..."
chmod +x scripts/quick_start_linux.sh 2>/dev/null || true
chmod +x tests/run_tests_linux.sh 2>/dev/null || true
chmod +x tools/git_commit_ai 2>/dev/null || true
find . -name "*.py" -path "./agents/*" -exec chmod +x {} \; 2>/dev/null || true
find . -name "*.py" -path "./services/*" -exec chmod +x {} \; 2>/dev/null || true

# 7. 不要ファイル削除
echo "🗑️ 不要ファイル削除..."
rm -f test_git_smart_agent.py test_command_agent.py scan_unused_files.py 2>/dev/null || true
echo "✅ 一時ファイル削除完了"

# 8. Linux環境設定
echo "⚙️ Linux環境設定..."
export NEUROHUB_HOME="$(pwd)"
export PYTHONPATH="$NEUROHUB_HOME:$PYTHONPATH"
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# ~/.bashrcに追加（重複チェック）
if ! grep -q "NEUROHUB_HOME" ~/.bashrc 2>/dev/null; then
    echo "# NeuroHub環境変数" >> ~/.bashrc
    echo "export NEUROHUB_HOME=\"$NEUROHUB_HOME\"" >> ~/.bashrc
    echo "export PYTHONPATH=\"\$NEUROHUB_HOME:\$PYTHONPATH\"" >> ~/.bashrc
    echo "export LC_ALL=C.UTF-8" >> ~/.bashrc
    echo "export LANG=C.UTF-8" >> ~/.bashrc
    echo "✅ 環境変数を~/.bashrcに追加"
else
    echo "ℹ️ 環境変数は既に設定済み"
fi

# 9. 基本動作テスト
echo "🧪 基本動作テスト..."

echo "  📡 LLMAgent接続テスト..."
if python3 -c "from agents.llm_agent import LLMAgent; agent = LLMAgent(); print('✅ LLMAgent初期化成功')"; then
    echo "  ✅ LLMAgent OK"
else
    echo "  ⚠️ LLMAgent 要確認（.env設定が必要）"
fi

echo "  🔧 Git機能テスト..."
if python3 -c "from agents.git_smart_agent import GitSmartAgent; agent = GitSmartAgent(); print('✅ GitSmartAgent初期化成功')"; then
    echo "  ✅ GitSmartAgent OK"
else
    echo "  ⚠️ GitSmartAgent 要確認"
fi

# 10. 完了メッセージ
echo
echo "================================================"
echo "🎉 NeuroHub Linux環境セットアップ完了！"
echo "================================================"
echo
echo "📋 次のステップ:"
echo "   1. .envファイルでAPI keyを設定:"
echo "      GEMINI_API_KEY=your_key_here"
echo "      HUGGINGFACE_API_KEY=your_key_here"
echo
echo "   2. 基本的な使用方法:"
echo "      source venv_linux/bin/activate"
echo "      python3 agents/llm_agent.py"
echo "      python3 agents/git_smart_agent.py"
echo "      ./tools/git_commit_ai"
echo
echo "   3. テスト実行:"
echo "      python3 tests/test_comprehensive_working.py"
echo "      python3 -m pytest tests/ -v"
echo
echo "   4. 独立ユーティリティ:"
echo "      python3 services/agent/weather_agent.py"
echo "      python3 services/agent/web_agent.py <URL> <question>"
echo
echo "🚀 Linux環境で最適化された開発環境の準備完了！"
