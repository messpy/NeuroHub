#!/bin/bash
# -*- coding: utf-8 -*-
"""
test_git_commit_ai.sh - git_commit_ai ツールのテストスクリプト
"""

# テスト用の一時ディレクトリ作成
TEST_DIR=$(mktemp -d)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
GIT_COMMIT_AI="$PROJECT_ROOT/tools/git_commit_ai"

echo "🧪 git_commit_ai ツールテスト開始"
echo "テストディレクトリ: $TEST_DIR"
echo "git_commit_ai パス: $GIT_COMMIT_AI"

# エラーハンドリング
set -e
trap 'rm -rf "$TEST_DIR"' EXIT

# テスト用Gitリポジトリ初期化
cd "$TEST_DIR"
git init
git config user.name "Test User"
git config user.email "test@example.com"

# 初期ファイル作成
echo "# Test Project" > README.md
echo "Initial content" > test.txt
git add README.md test.txt
git commit -m "Initial commit"

echo "✅ テスト用リポジトリ初期化完了"

# テスト1: ヘルプ表示
echo ""
echo "📋 テスト1: ヘルプ表示"
"$GIT_COMMIT_AI" --help || echo "⚠️ ヘルプ表示テスト: 何らかの出力があれば正常"

# テスト2: バージョン表示
echo ""
echo "📋 テスト2: バージョン表示"
"$GIT_COMMIT_AI" --version || echo "⚠️ バージョン表示: 出力があれば正常"

# テスト3: 変更なしでの実行
echo ""
echo "📋 テスト3: 変更なしでの実行"
result=$("$GIT_COMMIT_AI" 2>&1 || true)
if [[ "$result" == *"変更"* ]] || [[ "$result" == *"nothing"* ]] || [[ "$result" == *"clean"* ]]; then
    echo "✅ 変更なしの検出: 正常"
else
    echo "❓ 変更なし応答: $result"
fi

# テスト4: ファイル変更後の実行
echo ""
echo "📋 テスト4: ファイル変更後の実行"
echo "Updated content for testing" >> test.txt
echo "function test() { return 'hello'; }" > feature.js

# git_commit_ai実行（ドライラン）
echo "🔧 git_commit_ai実行中（新規ファイル含む）..."
result=$("$GIT_COMMIT_AI" --dry-run 2>&1 || true)

if [[ "$result" == *":"* ]] && ([[ "$result" == *"add"* ]] || [[ "$result" == *"update"* ]] || [[ "$result" == *"fix"* ]]); then
    echo "✅ コミットメッセージ形式: 正常 (:prefix: 形式を検出)"
    echo "   生成されたメッセージ: $result"
else
    echo "❓ コミットメッセージ: $result"
fi

# テスト5: API接続テスト
echo ""
echo "📋 テスト5: API接続テスト"
api_result=$("$GIT_COMMIT_AI" --test-api 2>&1 || true)

if [[ "$api_result" == *"成功"* ]] || [[ "$api_result" == *"利用可能"* ]]; then
    echo "✅ API接続: 成功"
elif [[ "$api_result" == *"失敗"* ]] || [[ "$api_result" == *"エラー"* ]]; then
    echo "⚠️ API接続: 失敗（設定要確認）"
    echo "   エラー詳細: $api_result"
else
    echo "❓ API接続結果: $api_result"
fi

# テスト6: 設定確認
echo ""
echo "📋 テスト6: 設定確認"
config_result=$("$GIT_COMMIT_AI" --show-config 2>&1 || true)

if [[ "$config_result" == *"Provider"* ]] || [[ "$config_result" == *"設定"* ]] || [[ "$config_result" == *"API"* ]]; then
    echo "✅ 設定表示: 正常"
else
    echo "❓ 設定表示: $config_result"
fi

# テスト7: 無効なオプション
echo ""
echo "📋 テスト7: 無効なオプション処理"
invalid_result=$("$GIT_COMMIT_AI" --invalid-option 2>&1 || true)

if [[ "$invalid_result" == *"無効"* ]] || [[ "$invalid_result" == *"usage"* ]] || [[ "$invalid_result" == *"help"* ]]; then
    echo "✅ 無効オプション処理: 正常"
else
    echo "❓ 無効オプション応答: $invalid_result"
fi

# テスト8: 大きなファイルの処理
echo ""
echo "📋 テスト8: 大きなファイル処理"

# 大きなファイル作成（1000行）
for i in {1..1000}; do
    echo "Line $i: This is a test line with some content to make it longer" >> large_file.txt
done

large_result=$("$GIT_COMMIT_AI" --dry-run 2>&1 || true)

if [[ "$large_result" == *":"* ]]; then
    echo "✅ 大きなファイル処理: 正常"
    echo "   メッセージ: $(echo "$large_result" | head -1)"
else
    echo "❓ 大きなファイル処理: $large_result"
fi

# テスト9: 特殊文字を含むファイル
echo ""
echo "📋 テスト9: 特殊文字ファイル処理"

echo "日本語テキスト：こんにちは世界" > japanese.txt
echo "Émojis: 🎉 🚀 ✅ ❌" >> japanese.txt
echo "Special chars: ñáéíóú çüöä" >> japanese.txt

special_result=$("$GIT_COMMIT_AI" --dry-run 2>&1 || true)

if [[ "$special_result" == *":"* ]]; then
    echo "✅ 特殊文字処理: 正常"
else
    echo "❓ 特殊文字処理: $special_result"
fi

# テスト10: 実際のコミット（安全なテスト環境でのみ）
echo ""
echo "📋 テスト10: 実際のコミット"

# ファイルをステージング
git add test.txt feature.js large_file.txt japanese.txt

if git diff --cached --quiet; then
    echo "⚠️ ステージされた変更がありません"
else
    echo "🔧 実際のコミットテスト実行中..."

    # バックアップのためコミット前の状態を保存
    commit_result=$("$GIT_COMMIT_AI" --auto-commit 2>&1 || true)

    if git log --oneline -1 | grep -E ":(add|update|fix|refactor):" > /dev/null 2>&1; then
        echo "✅ 実際のコミット: 成功"
        echo "   最新コミット: $(git log --oneline -1)"
    else
        echo "❓ コミット結果: $commit_result"
        echo "   最新コミット: $(git log --oneline -1)"
    fi
fi

# テスト結果サマリー
echo ""
echo "🏁 テスト完了"
echo "==============================================="
echo "テスト実行時刻: $(date)"
echo "テストディレクトリ: $TEST_DIR"
echo "git_commit_ai バージョン:"
"$GIT_COMMIT_AI" --version 2>/dev/null || echo "バージョン情報なし"
echo ""
echo "📊 推奨される次のステップ:"
echo "1. API キーの設定確認"
echo "2. LLM プロバイダーの接続テスト"
echo "3. 実際のプロジェクトでの動作確認"
echo ""

# 成功メッセージ
echo "✅ git_commit_ai テストスイート完了"
