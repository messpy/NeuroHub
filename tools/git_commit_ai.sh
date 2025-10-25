#!/usr/bin/env bash
# git-commit-ai_auto_smart.sh (安全対応フル版・grep修正版)
# ------------------------------------------------------------
# 完全自動・無対話:
#   - git add -A
#   - ステージ済み変更を自動解析し、
#       1) 同一インターフェイス変更は自動グループ化
#       2) それ以外は1ファイル1コミット
#   - 日本語・絵文字なし・:prefix: 形式（NeuroHub拡張）
#   - Gemini 優先 → 失敗なら Ollama（モデル名と進捗表示）
#   - センシティブファイル自動除外（誤検知軽減）
#   - 自動リトライ（不採用案をプロンプトに渡して改善）
# ------------------------------------------------------------

set -euo pipefail
log() { printf '%s\n' "$*" >&2; }  # 進捗ログをstderrへ

# ===== 調整可能な既定値 =====
LANG_CODE="ja"
MAX_LEN=40
MAX_RETRY=3
DIFF_HEAD_LINES=500
PAIR_CAP_PER_FILE=80
RENAME_MIN_FILES=3
RENAME_RATIO_NUM=1
RENAME_RATIO_DEN=2

# ===== 設定探索 =====
if ! GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  log "Git リポジトリ内で実行してください。"
  exit 1
fi

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

OLLAMA_HOST_VAL="http://127.0.0.1:11434"
OLLAMA_MODEL=""
GEM_API_URL="https://generativelanguage.googleapis.com/v1"
GEM_MODEL="gemini-2.5-flash"
GEM_API_KEY="${GEMINI_API_KEY:-}"

if [[ -f "$CONF_ENV" ]]; then
  if grep -q '^GEMINI_API_KEY=' "$CONF_ENV"; then
    GEM_API_KEY="$(grep '^GEMINI_API_KEY=' "$CONF_ENV" | tail -n1 | cut -d= -f2-)"
  fi
  if grep -q '^OLLAMA_HOST=' "$CONF_ENV"; then
    OLLAMA_HOST_VAL="$(grep '^OLLAMA_HOST=' "$CONF_ENV" | tail -n1 | cut -d= -f2-)"
  fi
fi

if [[ -f "$CONF_YAML" && $(command -v yq) ]]; then
  OLLAMA_HOST_VAL="$(yq -r '.llm.ollama.host // "http://127.0.0.1:11434"' "$CONF_YAML")"
  OLLAMA_MODEL="$(yq -r '.llm.ollama.selected_model // ""' "$CONF_YAML")"
  GEM_API_URL="$(yq -r '.llm.gemini.api_url // "https://generativelanguage.googleapis.com/v1"' "$CONF_YAML")"
  GEM_MODEL="$(yq -r '.llm.gemini.model // "gemini-2.5-flash"' "$CONF_YAML")"
fi
[[ -z "$OLLAMA_MODEL" ]] && OLLAMA_MODEL="qwen2.5:1.5b-instruct"

# ===== セキュリティフィルタ =====
shopt -s nocasematch extglob
SENSITIVE_PATH_GLOBS=(
  '*.pem' '*.key' '*.crt' '*.p12' '*.pfx' '*.der' '*.jks' '*.kdb' '*.keystore' '*.gpg' '*.asc'
  '.env' '.env.*' '*credentials*' '*secrets*'
  '*id_rsa*' '*id_dsa*' '.ssh/*' 'known_hosts'
  '.kube/config' '.aws/*' 'config/secrets.*' 'secrets.*'
  '*service-account*.json' '*-sa.json' '*apiKey*.json'
)
SECRET_REGEXES=(
  '-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----'
  'AKIA[0-9A-Z]{16}'
  'aws_secret_access_key'
  'xox[abpr]-[0-9A-Za-z-]{10,}'
  'AIza[0-9A-Za-z\-_]{35}'
  'ghp_[0-9A-Za-z]{36,}'
  'github_pat_[0-9A-Za-z_]{20,}'
  'client_secret'
  'refresh_token'
  'password[[:space:]]*='
)

is_sensitive_path() {
  local f="$1"
  for pat in "${SENSITIVE_PATH_GLOBS[@]}"; do
    case "$f" in $pat) return 0 ;; esac
  done
  return 1
}

has_secret_in_diff() {
  local f="$1"
  local added
  added="$(git diff --cached -- "$f" | sed -n 's/^+//p' || true)"
  [[ -z "$added" ]] && return 1

  # BEGIN/END鍵ブロック検出
  local key_begin_re='-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----'
  local key_end_re='-----END (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----'
  if grep -E -q -e "$key_begin_re" <<<"$added" && grep -E -q -e "$key_end_re" <<<"$added"; then
    # 引用符などで囲まれてないなら秘密鍵として扱う
    if ! grep -E -q -e '["'\''#]' <<<"$added"; then
      return 0
    fi
  fi

  # その他の機密パターン
  local rx
  for rx in "${SECRET_REGEXES[@]}"; do
    [[ "$rx" == "$key_begin_re" ]] && continue
    if grep -E -q -e "$rx" <<<"$added"; then
      # コメント行 (#, //, /*) を除外
      if ! grep -E -q -e '^[[:space:]]*(#|//|/\*|\*\*)' <<<"$added"; then
        return 0
      fi
    fi
  done
  return 1
}

# ===== Git情報・AI生成ロジック =====
get_file_status() { git diff --cached --name-status -- "$1" | awk '{print $1}'; }
is_binary_cached() { [[ "$(git diff --cached --numstat -- "$1" | awk '{print $1,$2}')" == "- -" ]]; }

make_base_prompt() {
cat <<EOF
次の差分から、NeuroHubスタイルのコミットメッセージを生成してください。

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
・1行目に :prefix: #issue(optional)
・変更内容は日本語で簡潔に（${MAX_LEN}文字以内）
・句読点なし、敬語不要
EOF
}

build_file_prompt_block() {
  local f="$1" status; status="$(get_file_status "$f")"
  if is_binary_cached "$f"; then
    printf "[ファイル] %s\n[変更種別] %s (binary)\n[差分] バイナリ変更\n\n" "$f" "$status"
  else
    local snippet; snippet="$(git diff --cached -- "$f" | head -n "$DIFF_HEAD_LINES")"
    printf "[ファイル] %s\n[変更種別] %s\n[差分抜粋]\n%s\n\n" "$f" "$status" "$snippet"
  fi
}

generate_message_once() {
  local prompt_full="$1" msg=""
  if [[ -n "${GEM_API_KEY:-}" ]]; then
    log "geminiでコミットメッセージ作成中... (${GEM_MODEL})"
    local url req resp
    url="${GEM_API_URL%/}/models/${GEM_MODEL}:generateContent?key=${GEM_API_KEY}"
    req="$(jq -nc --arg t "$prompt_full" '{contents:[{parts:[{text:$t}]}]}')"
    resp="$(curl -sS -H "Content-Type: application/json" -d "$req" "$url" || true)"
    if jq -e '.error' >/dev/null 2>&1 <<<"$resp"; then
      log "geminiでコミットメッセージ作成中... (${GEM_MODEL}) → 失敗"
    else
      msg="$(jq -r '.candidates[0].content.parts[0].text // ""' <<<"$resp" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n1)"
    fi
  fi
  if [[ -z "$msg" ]]; then
    log "ollamaでコミットメッセージ作成中... (${OLLAMA_MODEL})"
    export OLLAMA_HOST="$OLLAMA_HOST_VAL"
    local raw; raw="$(printf "%s" "$prompt_full" | ollama run "$OLLAMA_MODEL" 2>/dev/null || true)"
    msg="$(printf "%s" "$raw" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n1)"
  fi
  [[ -n "$msg" && ${#msg} -gt $MAX_LEN ]] && msg="${msg:0:$MAX_LEN}"
  printf '%s\n' "$msg"
}

generate_message() {
  local body="$1"; shift || true
  local rejects=("${@:-}") base msg prompt_full
  base="$(make_base_prompt)"
  prompt_full="${base}\n==== 対象差分 ====\n${body}\n"
  if (( ${#rejects[@]} > 0 )); then
    prompt_full+="\n==== 不採用例 ====\n"
    for r in "${rejects[@]}"; do [[ -n "$r" ]] && prompt_full+="- ${r}\n"; done
  fi
  msg="$(generate_message_once "$prompt_full")"
  printf '%s\n' "$msg"
}

# ===== ステージング + センシティブ除外 =====
git add -A >/dev/null 2>&1 || true
mapfile -t FILES < <(git diff --cached --name-only)

SAFE_FILES=()
for f in "${FILES[@]}"; do
  if is_sensitive_path "$f" || has_secret_in_diff "$f"; then
    log "⚠ センシティブ検出により除外: $f"
  else
    SAFE_FILES+=("$f")
  fi
done
FILES=("${SAFE_FILES[@]}")

(( ${#FILES[@]} == 0 )) && { log "コミット対象なし"; exit 0; }

# ===== Smart Grouping =====
declare -A FILE_REMOVED_TOKENS FILE_ADDED_TOKENS
for f in "${FILES[@]}"; do
  DIFF_TEXT="$(git diff --cached -- "$f" || true)"
  mapfile -t removed < <(printf "%s\n" "$DIFF_TEXT" | sed -n 's/^-//p' | grep -oE '[A-Za-z_][A-Za-z0-9_]{2,}' | sort -u || true)
  mapfile -t added   < <(printf "%s\n" "$DIFF_TEXT" | sed -n 's/^+//p' | grep -oE '[A-Za-z_][A-Za-z0-9_]{2,}' | sort -u || true)
  FILE_REMOVED_TOKENS["$f"]="${removed[*]:-}"
  FILE_ADDED_TOKENS["$f"]="${added[*]:-}"
done

declare -A PAIR_TO_FILES
for f in "${FILES[@]}"; do
  IFS=' ' read -r -a rem_arr <<<"${FILE_REMOVED_TOKENS[$f]:-}"
  IFS=' ' read -r -a add_arr <<<"${FILE_ADDED_TOKENS[$f]:-}"
  (( ${#rem_arr[@]} == 0 || ${#add_arr[@]} == 0 )) && continue
  local_count=0
  for old in "${rem_arr[@]}"; do
    for new in "${add_arr[@]}"; do
      [[ "$old" == "$new" ]] && continue
      key="${old}=>${new}"
      current="${PAIR_TO_FILES[$key]:-}"
      case " $current " in *" $f "*) : ;; *) PAIR_TO_FILES["$key"]="${current:+$current }$f" ;; esac
      ((local_count++))
      (( local_count >= PAIR_CAP_PER_FILE )) && break 2
    done
  done
done

GROUPS=() GROUP_KEYS=() declare -A USED
total="${#FILES[@]}"
for key in "${!PAIR_TO_FILES[@]}"; do
  read -r -a arr <<<"${PAIR_TO_FILES[$key]}"
  filtered=()
  for f in "${arr[@]}"; do [[ -z "${USED[$f]:-}" ]] && filtered+=("$f"); done
  count=${#filtered[@]}
  if (( count >= RENAME_MIN_FILES )) && (( count * RENAME_RATIO_DEN >= total * RENAME_RATIO_NUM )); then
    GROUPS+=("$(printf "%s " "${filtered[@]}")")
    GROUP_KEYS+=("$key")
    for f in "${filtered[@]}"; do USED["$f"]=1; done
  fi
done
REMAINING=()
for f in "${FILES[@]}"; do [[ -z "${USED[$f]:-}" ]] && REMAINING+=("$f"); done

log "Smart Grouping: グループ=${#GROUPS[@]} / 単体=${#REMAINING[@]}"

# ===== コミット実行 =====
build_body_for_files() {
  local arr=("$@")
  for f in "${arr[@]}"; do build_file_prompt_block "$f"; done
}

commit_with_ai_for_files() {
  local files=("$@") body MESSAGE
  body="$(build_body_for_files "${files[@]}")"
  local -a REJECTS=()
  for ((i=0; i<=MAX_RETRY; i++)); do
    MESSAGE="$(generate_message "$body" "${REJECTS[@]}")"
    [[ -n "$MESSAGE" ]] && break
    REJECTS+=("$MESSAGE")
  done
  if [[ -z "$MESSAGE" ]]; then log "生成失敗: ${files[*]}"; return 1; fi
  git commit -m "$MESSAGE" -- "${files[@]}"
  log "コミット完了: (${#files[@]}ファイル) → $MESSAGE"
}

commit_with_ai_for_single_file() {
  local f="$1" body MESSAGE
  body="$(build_file_prompt_block "$f")"
  local -a REJECTS=()
  for ((i=0; i<=MAX_RETRY; i++)); do
    MESSAGE="$(generate_message "$body" "${REJECTS[@]}")"
    [[ -n "$MESSAGE" ]] && break
    REJECTS+=("$MESSAGE")
  done
  if [[ -z "$MESSAGE" ]]; then log "生成失敗: $f"; return 1; fi
  git commit -m "$MESSAGE" -- "$f"
  log "コミット完了: $f → $MESSAGE"
}

for idx in "${!GROUPS[@]}"; do
  read -r -a group_files <<<"${GROUPS[$idx]}"
  key="${GROUP_KEYS[$idx]-}"
  log "=== グループコミット開始: ${#group_files[@]}件（${key}) ==="
  commit_with_ai_for_files "${group_files[@]}" || true
done

for f in "${REMAINING[@]}"; do
  log "=== 単体コミット開始: $f ==="
  commit_with_ai_for_single_file "$f" || true
done

log "自動コミット処理が完了しました。"

