#!/usr/bin/env bash
# git-commit-ai.sh
# --------------------------------------------
# NeuroHubスタイルのコミットメッセージ支援スクリプト
#  - config.yaml / .env から Gemini or Ollama を自動選択
#  - 公式 + NeuroHub拡張Prefix (:add:, :fix:, etc)
#  - 日本語形式, 絵文字なし
#
# 使い方:
#   bash tools/git_commit_ai.sh
#   bash tools/git_commit_ai.sh -y                # 確認なしでコミット
#   bash tools/git_commit_ai.sh --lang ja --max 40
#
# 依存:
#   curl, jq, ollama, (yqがあればより正確)
# --------------------------------------------

set -euo pipefail

AUTO_YES=0
LANG_CODE="ja"
MAX_LEN=40

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes) AUTO_YES=1; shift ;;
    --lang) LANG_CODE="${2:-ja}"; shift 2 ;;
    --max) MAX_LEN="${2:-40}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [-y|--yes] [--lang ja|en] [--max N]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

# --- Git ルート検出 ---
if ! GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "Git リポジトリ内で実行してください。" >&2
  exit 1
fi

# --- 設定ファイル探索 ---
find_config_dir() {
  if [[ -n "${NEUROHUB_CONFIG:-}" && -d "${NEUROHUB_CONFIG}" ]]; then echo "$NEUROHUB_CONFIG"; return; fi
  if [[ -n "${NEUROHUB_ROOT:-}" && -d "${NEUROHUB_ROOT}/config" ]]; then echo "$NEUROHUB_ROOT/config"; return; fi
  local base="$PWD"
  while :; do
    [[ -f "$base/config/config.yaml" ]] && echo "$base/config" && return
    [[ "$base" == "/" ]] && break
    base="$(dirname "$base")"
  done
  [[ -f "$HOME/NeuroHub/config/config.yaml" ]] && echo "$HOME/NeuroHub/config" && return
  [[ -f "$GIT_ROOT/config/config.yaml" ]] && echo "$GIT_ROOT/config" && return
}
CONF_DIR="$(find_config_dir || true)"
CONF_YAML="${CONF_DIR:-}/config.yaml"
CONF_ENV="${CONF_DIR:-}/.env"

# --- デフォルト値 ---
OLLAMA_HOST_VAL="http://127.0.0.1:11434"
OLLAMA_MODEL=""
GEM_API_URL="https://generativelanguage.googleapis.com/v1"
GEM_MODEL="gemini-2.5-flash"
GEM_API_KEY="${GEMINI_API_KEY:-}"

# --- .env読込 ---
if [[ -f "$CONF_ENV" ]]; then
  if grep -q '^GEMINI_API_KEY=' "$CONF_ENV"; then
    val="$(grep '^GEMINI_API_KEY=' "$CONF_ENV" | tail -n1 | cut -d= -f2-)"
    [[ -n "$val" ]] && GEM_API_KEY="$val"
  fi
  if grep -q '^OLLAMA_HOST=' "$CONF_ENV"; then
    val="$(grep '^OLLAMA_HOST=' "$CONF_ENV" | tail -n1 | cut -d= -f2-)"
    [[ -n "$val" ]] && OLLAMA_HOST_VAL="$val"
  fi
fi

# --- YAML読込 ---
if [[ -f "$CONF_YAML" && -z "$OLLAMA_MODEL" ]]; then
  if command -v yq >/dev/null 2>&1; then
    OLLAMA_HOST_VAL="$(yq -r '.llm.ollama.host // "http://127.0.0.1:11434"' "$CONF_YAML")"
    OLLAMA_MODEL="$(yq -r '.llm.ollama.selected_model // ""' "$CONF_YAML")"
    GEM_API_URL="$(yq -r '.llm.gemini.api_url // "https://generativelanguage.googleapis.com/v1"' "$CONF_YAML")"
    GEM_MODEL="$(yq -r '.llm.gemini.model // "gemini-2.5-flash"' "$CONF_YAML")"
  fi
fi
[[ -z "$OLLAMA_MODEL" ]] && OLLAMA_MODEL="qwen2.5:1.5b-instruct"

# --- Git ステージ確認 ---
git add -A >/dev/null 2>&1 || true
STAGED_LIST="$(git diff --cached --name-only || true)"
if [[ -z "$STAGED_LIST" ]]; then
  echo "ステージされた変更がありません。（git add -A 済み？）" >&2
  exit 1
fi

echo "ステージング済みファイル:"
echo "--------------------------------"
echo "$STAGED_LIST"
echo "--------------------------------"

if (( ! AUTO_YES )); then
  read -r -p "このファイル群を対象にコミットメッセージを生成します。続行しますか？ (y/N): " yn
  case "$yn" in [Yy]*) ;; *) echo "キャンセルしました。"; exit 0;; esac
fi

DIFF="$(git diff --cached || true)"

# --- NeuroHub形式プロンプト（絵文字なし） ---
if [[ "$LANG_CODE" == "ja" ]]; then
  PROMPT="次の git diff をもとに、NeuroHubスタイルのコミットメッセージを生成してください。

==== Commit Message Format ====
:prefix: #Issue番号 変更内容
例:
:add: #123 新しいAPIエンドポイント追加
:fix: ログ出力の不具合修正
:docs: README更新

==== Prefix一覧 ====
:add: 新規機能・ファイル追加
:fix: バグ修正
:hotfix: 緊急バグ修正
:feat: 新機能
:update: 機能修正（バグではない）
:change: 仕様変更
:docs: ドキュメント修正
:disable: 無効化
:remove: ファイルやコード削除
:rename: ファイル名変更
:upgrade: バージョンアップ
:revert: 修正取り消し
:style: コードスタイル修正
:refactor: リファクタリング
:test: テスト修正・追加
:chore: ビルドツールや依存ライブラリ変更

==== ルール ====
・絵文字は使わない
・1行目に :prefix: #issue(optional) の形式で書く
・変更内容は日本語で簡潔に（${MAX_LEN}文字以内）
・句読点なし、敬語不要
・2行目以降に詳細説明が必要なら追記（任意）

==== 対象差分 ====
$DIFF
"
else
  PROMPT="From the following git diff, generate a commit message in NeuroHub-style format:
:prefix: #Issue description
Example:
:add: #123 Add new API endpoint
:fix: Correct encoding bug

Rules:
- No emoji
- Start with :prefix:
- Description concise, imperative, within ${MAX_LEN} chars
- Follow prefix list: add, fix, feat, docs, style, refactor, etc."
fi

# --- Gemini or Ollama ---
MESSAGE=""
if [[ -n "${GEM_API_KEY:-}" ]]; then
  GEM_URL="${GEM_API_URL%/}/models/${GEM_MODEL}:generateContent?key=${GEM_API_KEY}"
  GEM_REQ="$(jq -nc --arg t "$PROMPT" '{contents:[{parts:[{text:$t}]}]}')"
  GEM_RESP="$(curl -sS -H "Content-Type: application/json" -d "$GEM_REQ" "$GEM_URL" || true)"
  if jq -e '.error' >/dev/null 2>&1 <<<"$GEM_RESP"; then
    GEM_STATUS="ERR"
  else
    GEM_STATUS="OK"
    MESSAGE="$(jq -r '.candidates[0].content.parts[0].text // ""' <<<"$GEM_RESP" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n1)"
  fi
else
  GEM_STATUS="NO_KEY"
fi

if [[ -z "$MESSAGE" ]]; then
  export OLLAMA_HOST="$OLLAMA_HOST_VAL"
  RAW="$(printf "%s" "$PROMPT" | ollama run "$OLLAMA_MODEL" 2>/dev/null || true)"
  MESSAGE="$(printf "%s" "$RAW" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n1)"
fi

if [[ -z "$MESSAGE" ]]; then
  echo "生成に失敗しました。Gemini/Ollamaの設定を確認してください。" >&2
  exit 3
fi

if [[ ${#MESSAGE} -gt $MAX_LEN ]]; then MESSAGE="${MESSAGE:0:$MAX_LEN}"; fi

echo
echo "OLLAMA_HOST=$OLLAMA_HOST_VAL"
echo "OLLAMA_MODEL=$OLLAMA_MODEL"
echo "GEMINI_MODEL=$GEM_MODEL (status: ${GEM_STATUS:-none})"
echo
echo "AI提案メッセージ:"
echo "--------------------------------"
echo "$MESSAGE"
echo "--------------------------------"

FINAL_MSG="$MESSAGE"
if (( ! AUTO_YES )); then
  echo "Enterでそのまま採用、eで編集、nで中止。"
  read -r -p "[Enter/e/n]: " choice
  case "$choice" in
    "" ) ;;
    [Nn]* ) echo "キャンセルしました。"; exit 0 ;;
    [Ee]* )
      if read -e -p "Commit message: " -i "$MESSAGE" INPUT 2>/dev/null; then
        FINAL_MSG="${INPUT:-$MESSAGE}"
      else
        read -r -p "Commit message: " INPUT
        FINAL_MSG="${INPUT:-$MESSAGE}"
      fi
      if [[ ${#FINAL_MSG} -gt $MAX_LEN ]]; then FINAL_MSG="${FINAL_MSG:0:$MAX_LEN}"; fi
      ;;
  esac
fi

git commit -m "$FINAL_MSG"
echo "コミットしました。"
