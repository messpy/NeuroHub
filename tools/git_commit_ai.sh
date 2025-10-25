#!/usr/bin/env bash
# git-commit-ai.sh
# --------------------------------------------
# NeuroHub の config.yaml / .env から設定を拾い、
# 1) Gemini が使えれば Gemini でコミットメッセージ生成
# 2) ダメなら Ollama にフォールバック
#
# 使い方:
#   bash tools/git_commit_ai.sh
#   bash tools/git_commit_ai.sh -y                # 確認なしでコミット
#   bash tools/git_commit_ai.sh --lang ja --max 20
#
# 依存:
#   - curl, jq
#   - ollama
#   - yq（任意。あれば厳密に YAML 解析）
# --------------------------------------------

set -euo pipefail

AUTO_YES=0
LANG_CODE="ja"
MAX_LEN=20

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes) AUTO_YES=1; shift ;;
    --lang) LANG_CODE="${2:-ja}"; shift 2 ;;
    --max) MAX_LEN="${2:-20}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [-y|--yes] [--lang ja|en] [--max N]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

# --- Git ルート（今いるリポジトリ） ---
if ! GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "Git リポジトリ内で実行してください。" >&2
  exit 1
fi

# --- NeuroHub の config を探す ---
# 優先度: $NEUROHUB_CONFIG -> $NEUROHUB_ROOT/config -> カレントから上へ config/ -> ~/NeuroHub/config
find_config_dir() {
  if [[ -n "${NEUROHUB_CONFIG:-}" && -d "${NEUROHUB_CONFIG}" ]]; then
    printf '%s\n' "${NEUROHUB_CONFIG}"
    return
  fi
  if [[ -n "${NEUROHUB_ROOT:-}" && -d "${NEUROHUB_ROOT}/config" ]]; then
    printf '%s\n' "${NEUROHUB_ROOT}/config"
    return
  fi
  local base="$PWD"
  while :; do
    if [[ -f "$base/config/config.yaml" ]]; then
      printf '%s\n' "$base/config"
      return
    fi
    [[ "$base" == "/" ]] && break
    base="$(dirname "$base")"
  done
  if [[ -f "$HOME/NeuroHub/config/config.yaml" ]]; then
    printf '%s\n' "$HOME/NeuroHub/config"
    return
  fi
  if [[ -f "$GIT_ROOT/config/config.yaml" ]]; then
    printf '%s\n' "$GIT_ROOT/config"
    return
  fi
}
CONF_DIR="$(find_config_dir || true)"
CONF_YAML="${CONF_DIR:-}/config.yaml"
CONF_ENV="${CONF_DIR:-}/.env"

# --- 既定値 ---
OLLAMA_HOST_VAL="http://127.0.0.1:11434"
OLLAMA_MODEL=""
GEM_API_URL="https://generativelanguage.googleapis.com/v1"
GEM_MODEL="gemini-2.5-flash"
GEM_API_KEY="${GEMINI_API_KEY:-}"  # 環境変数があれば先に採用

# --- .env からキー読み込み（上書き） ---
if [[ -f "$CONF_ENV" ]]; then
  # GEMINI_API_KEY
  if grep -q '^GEMINI_API_KEY=' "$CONF_ENV"; then
    val="$(grep '^GEMINI_API_KEY=' "$CONF_ENV" | tail -n1 | cut -d= -f2-)"
    [[ -n "$val" ]] && GEM_API_KEY="$val"
  fi
  # OLLAMA_HOST
  if grep -q '^OLLAMA_HOST=' "$CONF_ENV"; then
    val="$(grep '^OLLAMA_HOST=' "$CONF_ENV" | tail -n1 | cut -d= -f2-)"
    [[ -n "$val" ]] && OLLAMA_HOST_VAL="$val"
  fi
fi

# --- YAML から設定を取得 ---
if [[ -f "$CONF_YAML" ]]; then
  if command -v yq >/dev/null 2>&1; then
    OLLAMA_HOST_VAL="$(yq -r '.llm.ollama.host // "http://127.0.0.1:11434"' "$CONF_YAML")"
    OLLAMA_MODEL="$(yq -r '.llm.ollama.selected_model // ""' "$CONF_YAML")"
    if [[ -z "$OLLAMA_MODEL" ]]; then
      OLLAMA_MODEL="$(yq -r '.llm.ollama.models[0] // ""' "$CONF_YAML")"
    fi
    GEM_API_URL="$(yq -r '.llm.gemini.api_url // "https://generativelanguage.googleapis.com/v1"' "$CONF_YAML")"
    GEM_MODEL="$(yq -r '.llm.gemini.model // "gemini-2.5-flash"' "$CONF_YAML")"
  else
    in_ollama=0; in_gemini=0
    while IFS= read -r line; do
      case "$line" in
        "  ollama:"*) in_ollama=1; in_gemini=0; continue ;;
        "  gemini:"*) in_gemini=1; in_ollama=0; continue ;;
      esac
      if [[ "$line" =~ ^[a-zA-Z] ]]; then in_ollama=0; in_gemini=0; fi
      if (( in_ollama )); then
        if [[ "$line" =~ host:\ *(.*) ]]; then OLLAMA_HOST_VAL="${BASH_REMATCH[1]//\"/}"; fi
        if [[ "$line" =~ selected_model:\ *(.*) ]]; then OLLAMA_MODEL="${BASH_REMATCH[1]//\"/}"; fi
        if [[ -z "$OLLAMA_MODEL" && "$line" =~ ^[[:space:]]*-[[:space:]]*(.+)$ ]]; then
          OLLAMA_MODEL="${BASH_REMATCH[1]}"
        fi
      elif (( in_gemini )); then
        if [[ "$line" =~ api_url:\ *(.*) ]]; then GEM_API_URL="${BASH_REMATCH[1]//\"/}"; fi
        if [[ "$line" =~ model:\ *(.*) ]]; then GEM_MODEL="${BASH_REMATCH[1]//\"/}"; fi
      fi
    done < "$CONF_YAML"
  fi
fi

# --- Ollama モデル最終フォールバック ---
if [[ -z "$OLLAMA_MODEL" ]]; then
  if command -v ollama >/dev/null 2>&1; then
    if curl -sS --max-time 3 "${OLLAMA_HOST_VAL%/}/api/tags" >/dev/null 2>&1; then
      OLLAMA_MODEL="$(ollama list 2>/dev/null | awk 'NR>1{print $1; exit}')"
    fi
  fi
fi
[[ -z "$OLLAMA_MODEL" ]] && OLLAMA_MODEL="qwen2.5:1.5b-instruct"

# --- Git ステージの確認（自動 add はそのまま維持） ---
git add -A >/dev/null 2>&1 || true

# 追加: ステージング済みファイル一覧を最初に表示
STAGED_LIST="$(git diff --cached --name-only || true)"
if [[ -z "$STAGED_LIST" ]]; then
  echo "ステージされた変更がありません。（git add -A 済み？）" >&2
  exit 1
fi
echo "ステージング済みファイル:"
echo "--------------------------------"
echo "$STAGED_LIST"
echo "--------------------------------"

# 差分本文
DIFF="$(git diff --cached || true)"

# --- プロンプト（言語別） ---
if [[ "$LANG_CODE" == "ja" ]]; then
  PROMPT="次の git diff から、短く要点をまとめたコミットメッセージ（日本語で${MAX_LEN}文字以内、句読点や接頭辞なし、1行）を出力してください。"
else
  PROMPT="From the following git diff, output a concise one-line commit message in ${LANG_CODE} within ${MAX_LEN} characters, no prefixes or boilerplate."
fi
PAYLOAD_TEXT="$(printf "%s\n\n%s\n" "$PROMPT" "$DIFF")"

# =========================
# 1) Gemini で試す
# =========================
MESSAGE=""
if [[ -n "${GEM_API_KEY:-}" ]]; then
  GEM_URL="${GEM_API_URL%/}/models/${GEM_MODEL}:generateContent?key=${GEM_API_KEY}"
  GEM_REQ="$(jq -nc --arg t "$PAYLOAD_TEXT" '{contents:[{parts:[{text:$t}]}]}')"
  GEM_RESP="$(curl -sS -H "Content-Type: application/json" -d "$GEM_REQ" "$GEM_URL" || true)"
  if jq -e '.error' >/dev/null 2>&1 <<<"$GEM_RESP"; then
    GEM_STATUS="ERR"
  else
    GEM_STATUS="OK"
    MESSAGE="$(jq -r '.candidates[0].content.parts[0].text // ""' <<<"$GEM_RESP" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | tr -d '\r' | head -n1)"
  fi
else
  GEM_STATUS="NO_KEY"
fi

# =========================
# 2) Ollama フォールバック
# =========================
if [[ -z "$MESSAGE" ]]; then
  export OLLAMA_HOST="$OLLAMA_HOST_VAL"
  RAW="$(printf "%s" "$PAYLOAD_TEXT" | ollama run "$OLLAMA_MODEL" 2>/dev/null || true)"
  MESSAGE="$(printf "%s" "$RAW" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n 1 | tr -d '\r')"
  if [[ -z "$MESSAGE" ]]; then
    RAW="$(printf "Write a one-line commit message in %s within %s chars.\n\n%s\n" "$LANG_CODE" "$MAX_LEN" "$DIFF" | ollama run "$OLLAMA_MODEL" 2>/dev/null || true)"
    MESSAGE="$(printf "%s" "$RAW" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n 1 | tr -d '\r')"
  fi
fi

# --- MAX 文字超えは切り詰め ---
if [[ -n "$MESSAGE" && ${#MESSAGE} -gt $MAX_LEN ]]; then
  MESSAGE="${MESSAGE:0:$MAX_LEN}"
fi

if [[ -z "$MESSAGE" ]]; then
  echo "生成に失敗しました。Gemini/Ollama の設定・接続をご確認ください。" >&2
  exit 3
fi

echo
echo "OLLAMA_HOST=$OLLAMA_HOST_VAL"
echo "OLLAMA_MODEL=$OLLAMA_MODEL"
echo "GEMINI_MODEL=$GEM_MODEL  (status: ${GEM_STATUS})"
echo
echo "提案コミットメッセージ:"
echo "--------------------------------"
echo "$MESSAGE"
echo "--------------------------------"

if (( AUTO_YES )); then
  git commit -m "$MESSAGE"
  echo "コミットしました。"
  exit 0
fi

read -r -p "このメッセージでコミットしますか？ (y/N): " yn
case "$yn" in
  [Yy]*) git commit -m "$MESSAGE"; echo "コミットしました。" ;;
  *) echo "キャンセルしました。";;
esac
