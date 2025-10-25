#!/usr/bin/env bash
# git-commit-ai.sh
# --------------------------------------------
# NeuroHubスタイルのコミットメッセージ支援スクリプト
# - config.yaml / .env を見て Gemini 優先 → Ollama フォールバック
# - 日本語・絵文字なし・:prefix: 形式
# - ステージ一覧表示後、即生成（確認プロンプトは廃止）
# - Retryで不採用案を蓄積し、次回生成時に回避・改善させる
#
# 使い方:
#   bash tools/git_commit_ai.sh
#   bash tools/git_commit_ai.sh -y                # 生成後即コミット（編集/メニューもスキップ）
#   bash tools/git_commit_ai.sh --lang ja --max 40
# --------------------------------------------

set -euo pipefail

AUTO_YES=0
LANG_CODE="ja"
MAX_LEN=40
MAX_RETRY=5

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes) AUTO_YES=1; shift ;;
    --lang) LANG_CODE="${2:-ja}"; shift 2 ;;
    --max) MAX_LEN="${2:-40}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [-y|--yes] [--lang ja|en] [--max N]"
      exit 0 ;;
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

# --- 既定値 ---
OLLAMA_HOST_VAL="http://127.0.0.1:11434"
OLLAMA_MODEL=""
GEM_API_URL="https://generativelanguage.googleapis.com/v1"
GEM_MODEL="gemini-2.5-flash"
GEM_API_KEY="${GEMINI_API_KEY:-}"

# --- .env 読み込み ---
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

# --- YAML（任意） ---
if [[ -f "$CONF_YAML" ]]; then
  if command -v yq >/dev/null 2>&1; then
    OLLAMA_HOST_VAL="$(yq -r '.llm.ollama.host // "http://127.0.0.1:11434"' "$CONF_YAML")"
    OLLAMA_MODEL="$(yq -r '.llm.ollama.selected_model // ""' "$CONF_YAML")"
    GEM_API_URL="$(yq -r '.llm.gemini.api_url // "https://generativelanguage.googleapis.com/v1"' "$CONF_YAML")"
    GEM_MODEL="$(yq -r '.llm.gemini.model // "gemini-2.5-flash"' "$CONF_YAML")"
  fi
fi
[[ -z "$OLLAMA_MODEL" ]] && OLLAMA_MODEL="qwen2.5:1.5b-instruct"

# --- ステージング（自動）＆一覧表示 ---
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

# 差分
DIFF="$(git diff --cached || true)"

# --- NeuroHub 形式ベースプロンプト ---
make_base_prompt() {
  if [[ "$LANG_CODE" == "ja" ]]; then
cat <<'EOF'
次の git diff をもとに、NeuroHubスタイルのコミットメッセージを生成してください。

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

EOF
  else
cat <<'EOF'
From the following git diff, generate a NeuroHub-style commit message.

Format:
:prefix: #Issue description
Examples:
:add: #123 Add new API endpoint
:fix: Correct log encoding bug

Rules:
- No emoji
- Start with :prefix:
- Description concise, imperative, within ${MAX_LEN} chars
- Optional body from 2nd line
- Prefer accurate prefix: add, fix, feat, docs, style, refactor, perf, test, chore, etc.

EOF
  fi
}

# --- 生成関数（Rejectedを考慮） ---
generate_message() {
  local diff_text="$1"
  shift
  local rejects=("$@")

  local BASE PROMPT_FULL
  BASE="$(make_base_prompt)"

  PROMPT_FULL="${BASE}
==== 対象差分 ====
${diff_text}
"

  if (( ${#rejects[@]} > 0 )); then
    PROMPT_FULL+="
==== 不採用例（この表現・言い回し・語尾は避け、より良く改善して1行目を出力） ====
"
    for r in "${rejects[@]}"; do
      PROMPT_FULL+="- ${r}\n"
    done
  fi

  # 送信（Gemini→Ollama）
  local msg="" GEM_STATUS="NO_KEY"
  if [[ -n "${GEM_API_KEY:-}" ]]; then
    GEM_STATUS="TRY"
    local url req resp
    url="${GEM_API_URL%/}/models/${GEM_MODEL}:generateContent?key=${GEM_API_KEY}"
    req="$(jq -nc --arg t "$PROMPT_FULL" '{contents:[{parts:[{text:$t}]}]}')"
    resp="$(curl -sS -H "Content-Type: application/json" -d "$req" "$url" || true)"
    if jq -e '.error' >/dev/null 2>&1 <<<"$resp"; then
      GEM_STATUS="ERR"
    else
      GEM_STATUS="OK"
      msg="$(jq -r '.candidates[0].content.parts[0].text // ""' <<<"$resp" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n1)"
    fi
  fi
  if [[ -z "$msg" ]]; then
    export OLLAMA_HOST="$OLLAMA_HOST_VAL"
    local raw
    raw="$(printf "%s" "$PROMPT_FULL" | ollama run "$OLLAMA_MODEL" 2>/dev/null || true)"
    msg="$(printf "%s" "$raw" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n1)"
  fi

  # 長さ制約
  if [[ -n "$msg" && ${#msg} -gt $MAX_LEN ]]; then
    msg="${msg:0:$MAX_LEN}"
  fi

  printf '%s\n' "$msg"
}

# === 生成 → 確定/編集/再生成 ループ ===
REJECTS=()
MESSAGE="$(generate_message "$DIFF" "${REJECTS[@]}")"

if [[ -z "$MESSAGE" ]]; then
  echo "生成に失敗しました。Gemini/Ollama の設定をご確認ください。" >&2
  exit 3
fi

# -y なら即コミット
if (( AUTO_YES )); then
  git commit -m "$MESSAGE"
  echo "コミットしました。"
  exit 0
fi

retry_count=0
while :; do
  echo
  echo "AI提案メッセージ:"
  echo "--------------------------------"
  echo "$MESSAGE"
  echo "--------------------------------"
  echo "[Enter=確定 / e=編集 / r=再生成 / n=中止]"
  read -r -p "> " choice
  case "$choice" in
    "" )
      git commit -m "$MESSAGE"
      echo "コミットしました。"
      break
      ;;
    [Nn]* )
      echo "キャンセルしました。"
      exit 0
      ;;
    [Ee]* )
      TMPFILE=$(mktemp)
      echo "$MESSAGE" > "$TMPFILE"
      ${EDITOR:-nano} "$TMPFILE"
      MESSAGE="$(head -n 1 "$TMPFILE" | tr -d '\r\n')"
      rm -f "$TMPFILE"
      [[ -z "$MESSAGE" ]] && echo "空行は不可です。" && continue
      if [[ ${#MESSAGE} -gt $MAX_LEN ]]; then MESSAGE="${MESSAGE:0:$MAX_LEN}"; fi
      git commit -m "$MESSAGE"
      echo "コミットしました。"
      break
      ;;
    [Rr]* )
      REJECTS+=("$MESSAGE")
      ((retry_count++))
      if (( retry_count > MAX_RETRY )); then
        echo "再生成回数が上限(${MAX_RETRY})に達しました。"
        continue
      fi
      MESSAGE="$(generate_message "$DIFF" "${REJECTS[@]}")"
      if [[ -z "$MESSAGE" ]]; then
        echo "再生成に失敗しました。"
        exit 3
      fi
      ;;
    * )
      # 予期しない入力は案内のみ
      echo "Enter/e/r/n のいずれかを入力してください。"
      ;;
  esac
done
