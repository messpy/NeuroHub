#!/usr/bin/env bash
# ============================================
# Ollama にコミットメッセージを生成させるスクリプト
# ============================================

MODEL=$(ollama list 2>/dev/null | awk 'NR>1{print $1; exit}')
[ -z "$MODEL" ] && MODEL="qwen2.5:1.5b-instruct"

DIFF=$(git diff --cached)
if [ -z "$DIFF" ]; then
  echo "⚠️ ステージされた変更がありません。"
  exit 1
fi

PROMPT="次の git diff から、短く要点をまとめたコミットメッセージ（日本語で20文字以内）を作ってください:"

MESSAGE=$(printf "%s\n\n%s" "$PROMPT" "$DIFF" | ollama run "$MODEL" | head -n 3)

echo "🧠 提案コミットメッセージ:"
echo "--------------------------------"
echo "$MESSAGE"
echo "--------------------------------"

read -p "このメッセージでコミットしますか？ (y/N): " yn
case "$yn" in
  [Yy]*) git commit -m "$MESSAGE" ;;
  *) echo "キャンセルしました。" ;;
esac
