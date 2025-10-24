#!/usr/bin/env bash
# git-commit-ai.sh
# --------------------------------------------
# config.yaml（NeuroHub）からモデル/ホストを取得して、
# Ollama でコミットメッセージを自動生成する。
#
# 使い方:
#   bash git-commit-ai.sh
#   bash git-commit-ai.sh -y                # 確認なしでコミット
#   bash git-commit-ai.sh --lang ja --max 20
#
# 依存:
#   - ollama
#   - yq (あれば優先。無ければawkで代替)
# --------------------------------------------

set -euo pipefail

AUTO_YES=0
LANG="ja"
MAX=20

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes) AUTO_YES=1; shift ;;
    --lang) LANG="${2:-ja}"; shift 2 ;;
    --max) MAX="${2:-20}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [-y|--yes] [--lang ja|en] [--max N]"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

# --- Git ルート ---
if ! ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "❌ Git repo 内で実行してください。"
  exit 1
fi

# --- config.yaml の場所（NeuroHub構成を想定） ---
CONF_YAML="$ROOT/config/config.yaml"
if [[ ! -f "$CONF_YAML" ]]; then
  # NeuroHub/_archive から単体で使うケースにも対応
  ALT1="$ROOT/NeuroHub/config/config.yaml"
  ALT2="$ROOT/../NeuroHub/config/config.yaml"
  if   [[ -f "$ALT1" ]]; then CONF_YAML="$ALT1"
  elif [[ -f "$ALT2" ]]; then CONF_YAML="$ALT2"
  fi
fi

# --- YAML から host / model を取得 ---
OLLAMA_HOST_VAL="http://127.0.0.1:11434"
MODEL=""

if [[ -f "$CONF_YAML" ]]; then
  if command -v yq >/dev/null 2>&1; then
    # yq がある場合は厳密に取得
    OLLAMA_HOST_VAL="$(yq -r '.llm.ollama.host // "http://127.0.0.1:11434"' "$CONF_YAML")"
    MODEL="$(yq -r '.llm.ollama.selected_model // ""' "$CONF_YAML")"
    if [[ -z "$MODEL" ]]; then
      # models 配列の先頭にフォールバック
      MODEL="$(yq -r '.llm.ollama.models[0] // ""' "$CONF_YAML")"
    fi
  else
    # yq が無い場合: ollama: セクションだけを素朴にパース
    in_ollama=0
    while IFS= read -r line; do
      # 行頭からの空白数で見ていく（超簡易版）
      case "$line" in
        "  ollama:"*) in_ollama=1; continue ;;
      esac
      if [[ $in_ollama -eq 1 ]]; then
        # ollama節の終わり検出（先頭2スペース以外のキーが来たら終わりとみなす）
        if [[ "$line" =~ ^[a-z] || "$line" =~ ^[A-Za-z] ]]; then
          in_ollama=0
          continue
        fi
        # host
        if [[ "$line" =~ host:\ *(.*) ]]; then
          val="${BASH_REMATCH[1]}"
          OLLAMA_HOST_VAL="${val//\"/}"
        fi
        # selected_model
        if [[ "$line" =~ selected_model:\ *(.*) ]]; then
          val="${BASH_REMATCH[1]}"
          MODEL="${val//\"/}"
        fi
        # models配列の先頭（selectedが空の時のみ拾う）
        if [[ -z "$MODEL" && "$line" =~ ^[[:space:]]*-[[:space:]]*(.+)$ ]]; then
          MODEL="${BASH_REMATCH[1]}"
        fi
      fi
    done < "$CONF_YAML"

    # デフォルト値（最終手段）
    [[ -z "${OLLAMA_HOST_VAL:-}" ]] && OLLAMA_HOST_VAL="http://127.0.0.1:11434"
  fi
fi

# host は .env > config.yaml の順で上書き
if [[ -f "$ROOT/config/.env" ]]; then
  # .env の OLLAMA_HOST があれば採用
  if grep -q '^OLLAMA_HOST=' "$ROOT/config/.env"; then
    env_host="$(grep '^OLLAMA_HOST=' "$ROOT/config/.env" | tail -n1 | cut -d= -f2-)"
    [[ -n "$env_host" ]] && OLLAMA_HOST_VAL="$env_host"
  fi
fi

# MODEL の最終フォールバック
if [[ -z "$MODEL" ]]; then
  # ollama list から先頭モデル
  if command -v ollama >/dev/null 2>&1; then
    if curl -sS --max-time 2 "${OLLAMA_HOST_VAL%/}/api/tags" >/dev/null 2>&1; then
      MODEL="$(ollama list 2>/dev/null | awk 'NR>1{print $1; exit}')"
    fi
  fi
fi
[[ -z "$MODEL" ]] && MODEL="qwen2.5:1.5b-instruct"

# --- Git ステージ確認 ---
git add -A >/dev/null 2>&1 || true
DIFF="$(git diff --cached || true)"
if [[ -z "$DIFF" ]]; then
  echo "⚠️ ステージされた変更がありません。"
  exit 1
fi

# --- 生成プロンプト ---
if [[ "$LANG" == "ja" ]]; then
  PROMPT="次の git diff から、短く要点をまとめたコミットメッセージ（日本語で${MAX}文字以内、句読点や余計な接頭辞なし、1行）を出力してください。"
else
  PROMPT="From the following git diff, output a concise one-line commit message in ${LANG} within ${MAX} characters, no prefixes."
fi

PAYLOAD="$(printf "%s\n\n%s\n" "$PROMPT" "$DIFF")"

# --- 実行（環境変数でホスト指定） ---
export OLLAMA_HOST="$OLLAMA_HOST_VAL"

echo "🔗 OLLAMA_HOST=$OLLAMA_HOST"
echo "🤖 MODEL=$MODEL"
echo "⏳ Generating…"

# ストリームせずに1行だけ抽出（余分な行を弾く）
RAW="$(printf "%s" "$PAYLOAD" | ollama run "$MODEL" 2>/dev/null || true)"
MESSAGE="$(printf "%s" "$RAW" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n 1 | tr -d '\r')"

# 万一空なら再試行（短縮プロンプト）
if [[ -z "$MESSAGE" ]]; then
  RAW="$(printf "Write a one-line commit message in %s within %s chars.\n\n%s\n" "$LANG" "$MAX" "$DIFF" | ollama run "$MODEL" 2>/dev/null || true)"
  MESSAGE="$(printf "%s" "$RAW" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | head -n 1 | tr -d '\r')"
fi

# さらに保険：MAX超なら切り詰め
if [[ -n "$MESSAGE" ]]; then
  # 全角対応でざっくりカット（Bashではバイトになるため、ここは実用優先）
  if (( ${#MESSAGE} > MAX )); then
    MESSAGE="${MESSAGE:0:MAX}"
  fi
fi

if [[ -z "$MESSAGE" ]]; then
  echo "❌ 生成に失敗しました。接続/モデルを確認してください。"
  exit 2
fi

echo
echo "🧠 提案コミットメッセージ:"
echo "--------------------------------"
echo "$MESSAGE"
echo "--------------------------------"

if (( AUTO_YES )); then
  git commit -m "$MESSAGE"
  echo "✅ コミットしました。"
  exit 0
fi

read -r -p "このメッセージでコミットしますか？ (y/N): " yn
case "$yn" in
  [Yy]*) git commit -m "$MESSAGE"; echo "✅ コミットしました。" ;;
  *) echo "キャンセルしました。";;
esac
