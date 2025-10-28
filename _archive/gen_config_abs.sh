#!/usr/bin/env bash
# gen_config_preview.sh
# - config.yaml を上書きせず、期待YAMLを標準出力にプレビュー
# - Ollama が停止中でも、必要なら一時的に起動してモデルを検出（起動できたらそのまま稼働）
# - 末尾に、Ollama にチャット用モデルが無い場合のみ注意を stderr に出力

set -euo pipefail
IFS=$'\n\t'

DEBUG=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log(){ echo "[gen_config] $*" >&2; }
dbg(){ [[ $DEBUG -eq 1 ]] && echo "[gen_config:debug] $*" >&2 || true; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug) DEBUG=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

# ---------- System 情報 ----------
HOSTNAME="$(hostname)"
USER_NAME="$(id -un)"
if [[ -r /etc/os-release ]]; then . /etc/os-release; OS_NAME="${NAME:-Linux} ${VERSION:-}"; else OS_NAME="$(uname -s)"; fi
KERNEL="$(uname -r)"
ARCH="$(uname -m)"
CPU_CORES="$(nproc || echo 1)"
CPU_MODEL=""
if command -v lscpu >/dev/null 2>&1; then CPU_MODEL="$(lscpu | awk -F: '/Model name/ {sub(/^[ \t]+/,"",$2); print $2; exit}')"; fi
[[ -z "${CPU_MODEL}" ]] && CPU_MODEL="$(awk -F: '/model name/ {gsub(/^[ \t]+/,"",$2); print $2; exit}' /proc/cpuinfo 2>/dev/null || true)"
MEM_MB="$(awk '/MemTotal:/ {printf "%.0f", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)"
IPV4_LIST="$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | paste -sd, -)"
[[ -z "${IPV4_LIST}" ]] && IPV4_LIST="$(hostname -I 2>/dev/null | tr ' ' ',' | sed 's/,$//')"
IPV4_LIST="${IPV4_LIST:-}"
if [[ -r /etc/machine-id ]]; then MACHINE_ID="$(tr -d '\n' </etc/machine-id)"; else MACHINE_ID="$(printf '%s' "${HOSTNAME}-${USER_NAME}" | md5sum | awk '{print $1}')"; fi
LANG_VAL="${LANG:-}"; LC_ALL_VAL="${LC_ALL:-}"; LANGUAGE_VAL="${LANGUAGE:-}"
SYSTEM_LOCALE_LINE="$(grep -E '^LANG=' /etc/default/locale 2>/dev/null | head -n1)"
VC_KEYMAP="$(localectl status 2>/dev/null | awk -F: '/VC Keymap/ {gsub(/^[ \t]+/,"",$2); print $2; exit}')"
X11_LAYOUT="$(localectl status 2>/dev/null | awk -F: '/X11 Layout/ {gsub(/^[ \t]+/,"",$2); print $2; exit}')"
X11_MODEL="$(localectl status 2>/dev/null | awk -F: '/X11 Model/ {gsub(/^[ \t]+/,"",$2); print $2; exit}')"
X11_VARIANT="$(localectl status 2>/dev/null | awk -F: '/X11 Variant/ {gsub(/^[ \t]+/,"",$2); print $2; exit}')"
X11_OPTIONS="$(localectl status 2>/dev/null | awk -F: '/X11 Options/ {gsub(/^[ \t]+/,"",$2); print $2; exit}')"
CUR_DESKTOP="${XDG_CURRENT_DESKTOP:-}"; CUR_SESSION="${DESKTOP_SESSION:-}"
CREATED_AT="$(TZ=Asia/Tokyo date +%Y-%m-%dT%H:%M:%S%z | sed -E 's/([+-][0-9]{2})([0-9]{2})$/\1:\2/')"

# ---------- LLM 雛形 ----------
G_API_URL="https://generativelanguage.googleapis.com/v1"
G_MODEL="gemini-2.5-flash"
G_ENABLED=0

HF_API_BASE="https://router.huggingface.co"
HF_CHAT_TMPL="${HF_API_BASE}/hf-inference/models/{model}/v1/chat/completions"
HF_INFER_TMPL="https://api-inference.huggingface.co/models/{model}"
HF_MODELS=( "Qwen/Qwen2.5-0.5B-Instruct" "google/gemma-2-2b-it" "HuggingFaceH4/zephyr-7b-beta" )
HF_SELECTED="${HF_MODELS[0]}"
HF_ENABLED=0

# ---------- Ollama 検出（未起動なら起動） ----------
# PATH 追加（/usr/local/bin にいるケース）
if ! command -v ollama >/dev/null 2>&1 && [[ -x "/usr/local/bin/ollama" ]]; then
  export PATH="/usr/local/bin:${PATH}"
fi

OLLAMA_HOST="http://127.0.0.1:11434"
ver_ok=0
if command -v curl >/dev/null 2>&1; then
  code="$(curl -s -o /dev/null -w '%{http_code}' "${OLLAMA_HOST}/api/version" || true)"
  [[ "${code}" == "200" ]] && ver_ok=1
fi

started_by_me=0
if [[ $ver_ok -eq 0 ]] && command -v ollama >/dev/null 2>&1; then
  # 1) systemd --user での起動を優先（ある場合）
  if command -v systemctl >/dev/null 2>&1; then
    dbg "trying: systemctl --user start ollama"
    systemctl --user start ollama >/dev/null 2>&1 || true
  fi
  # 2) まだ応答なしなら、バックグラウンドで直接起動
  code="$(curl -s -o /dev/null -w '%{http_code}' "${OLLAMA_HOST}/api/version" || true)"
  if [[ "${code}" != "200" ]]; then
    dbg "trying: nohup ollama serve &"
    nohup ollama serve >/dev/null 2>&1 &
    started_by_me=1
  fi
  # 3) 起動待機（最大 8 秒）
  for _ in {1..16}; do
    sleep 0.5
    code="$(curl -s -o /dev/null -w '%{http_code}' "${OLLAMA_HOST}/api/version" || true)"
    if [[ "${code}" == "200" ]]; then ver_ok=1; break; fi
  done
fi

# モデル一覧取得
declare -a OLLAMA_ALL=()
if command -v ollama >/dev/null 2>&1; then
  mapfile -t OLLAMA_ALL < <( (ollama list 2>/dev/null || true) | awk 'NR>1 {print $1}' )
fi

OLLAMA_ENABLED=0
(( ${#OLLAMA_ALL[@]} > 0 )) && OLLAMA_ENABLED=1

is_embed(){ grep -Eiq '(embed|embedding|nomic-embed|all-minilm|e5-|bge-|gte-|text-embedding)' <<<"$1"; }

declare -a OLLAMA_CHAT_CAND=()
if (( ${#OLLAMA_ALL[@]} > 0 )); then
  for m in "${OLLAMA_ALL[@]}"; do
    if ! is_embed "$m"; then OLLAMA_CHAT_CAND+=("$m"); fi
  done
fi

pick_chat(){
  local -a names=("$@")
  local -a pref=( "qwen2.5:0.5b-instruct" "llama3.2:1b-instruct" "qwen2.5:1.5b-instruct" "qwen2.5:3b-instruct" "tinyllama:1.1b" "moondream:latest" )
  for p in "${pref[@]}"; do for n in "${names[@]}"; do [[ "$n" == "$p" ]] && { echo "$n"; return; }; done; done
  for n in "${names[@]}"; do [[ "$n" =~ instruct|chat ]] && { echo "$n"; return; }; done
  for n in "${names[@]}"; do [[ "$n" =~ moondream ]] && { echo "$n"; return; }; done
  echo ""
}
OLLAMA_SELECTED="$(pick_chat "${OLLAMA_CHAT_CAND[@]}")"

PROVIDERS=( gemini huggingface ollama )
SELECTED_PROVIDER="none"
for p in "${PROVIDERS[@]}"; do
  case "$p" in
    gemini)      [[ $G_ENABLED -eq 1 ]] && { SELECTED_PROVIDER="gemini"; break; } ;;
    huggingface) [[ $HF_ENABLED -eq 1 ]] && { SELECTED_PROVIDER="huggingface"; break; } ;;
    ollama)      [[ $OLLAMA_ENABLED -eq 1 ]] && { SELECTED_PROVIDER="ollama"; break; } ;;
  esac
done

# ---------- 付随パス ----------
TTS_MODEL_PATH=""
[[ -f "${ROOT}/models/piper/ja-kokoro-high.onnx" ]] && TTS_MODEL_PATH="${ROOT}/models/piper/ja-kokoro-high.onnx"
MPV_IPC_DIR="${ROOT}/data/cache/mpv"

# ---------- YAML プレビュー（上書きしない） ----------
{
  echo "# AUTO-GENERATED PREVIEW by gen_config_preview.sh (${CREATED_AT})"
  echo "llm:"
  echo "  provider_order:"
  echo "    - gemini"
  echo "    - huggingface"
  echo "    - ollama"
  echo "  selected_provider: ${SELECTED_PROVIDER}"
  echo
  echo "  gemini:"
  echo "    enabled: ${G_ENABLED}"
  echo "    api_url: \"${G_API_URL}\""
  echo "    model: \"${G_MODEL}\""
  echo "    temperature:"
  echo "    max_output_tokens:"
  echo "    timeout_sec:"
  echo
  echo "  huggingface:"
  echo "    enabled: ${HF_ENABLED}"
  echo "    api_base: \"${HF_API_BASE}\""
  echo "    chat_completions_url_template: \"${HF_CHAT_TMPL}\""
  echo "    inference_api_url_template: \"${HF_INFER_TMPL}\""
  echo "    selected_model: \"${HF_SELECTED}\""
  echo "    models:"
  for m in "${HF_MODELS[@]}"; do echo "      - ${m}"; done
  echo
  echo "  ollama:"
  echo "    enabled: ${OLLAMA_ENABLED}"
  echo "    host: \"${OLLAMA_HOST}\""
  echo "    models:"
  if (( ${#OLLAMA_ALL[@]} > 0 )); then
    for m in "${OLLAMA_ALL[@]}"; do echo "      - ${m}"; done
  else
    echo "      # (no local models)"
  fi
  echo "    selected_model: \"${OLLAMA_SELECTED}\""
  echo "    temperature:"
  echo "    num_ctx:"
  echo "    num_thread:"
  echo
  echo "asr:"
  echo "  engine:"
  echo "  model:"
  echo "  timeout_sec:"
  echo
  echo "tts:"
  echo "  engine:"
  if [[ -n "${TTS_MODEL_PATH}" ]]; then
    echo "  model: \"${TTS_MODEL_PATH}\""
  else
    echo "  model:"
  fi
  echo "  out_wav: \"${ROOT}/data/cache/tts/out.wav\""
  echo "  speed:"
  echo
  echo "mpv:"
  echo "  audio_device:"
  echo "  default_volume:"
  echo "  ipc_dir: \"${MPV_IPC_DIR}\""
  echo "  common_opts:"
  echo
  echo "logging:"
  echo "  level: INFO"
  echo "  dir: \"${ROOT}/logs\""
  echo
  echo "system:"
  echo "  created_at: \"${CREATED_AT}\""
  echo "  machine_id: \"${MACHINE_ID}\""
  echo "  hostname: \"${HOSTNAME}\""
  echo "  user: \"${USER_NAME}\""
  echo "  os: \"${OS_NAME}\""
  echo "  kernel: \"${KERNEL}\""
  echo "  arch: \"${ARCH}\""
  echo "  cpu_model: \"${CPU_MODEL}\""
  echo "  cpu_cores: ${CPU_CORES}"
  echo "  memory_mb: ${MEM_MB}"
  echo "  ipv4: [${IPV4_LIST}]"
  echo "  project_root: \"${ROOT}\""
  echo "  locale:"
  echo "    LANG: \"${LANG_VAL}\""
  echo "    LC_ALL: \"${LC_ALL_VAL}\""
  echo "    LANGUAGE: \"${LANGUAGE_VAL}\""
  echo "    system_locale_line: \"${SYSTEM_LOCALE_LINE}\""
  echo "  keyboard:"
  echo "    vc_keymap: \"${VC_KEYMAP:-}\""
  echo "    x11_layout: \"${X11_LAYOUT:-}\""
  echo "    x11_model: \"${X11_MODEL:-pc105}\""
  echo "    x11_variant: \"${X11_VARIANT:-}\""
  echo "    x11_options: \"${X11_OPTIONS:-}\""
  echo "  desktop:"
  echo "    current_desktop: \"${CUR_DESKTOP}\""
  echo "    session: \"${CUR_SESSION}\""
}  # end YAML print

# ---------- 注意（stderr） ----------
if (( ${#OLLAMA_CHAT_CAND[@]} == 0 )); then
  {
    echo
    if (( ${#OLLAMA_ALL[@]} == 0 )); then
      echo "[notice] Ollama のローカルモデルが見つかりません。次を例に追加してください:"
      echo "  ollama pull qwen2.5:0.5b-instruct"
    else
      echo "[notice] チャット用モデルが見つかりません（embed系のみの可能性）。次のどれかを追加してください:"
      echo "  ollama pull qwen2.5:0.5b-instruct"
      echo "  # 代替: llama3.2:1b-instruct / qwen2.5:1.5b-instruct / tinyllama:1.1b / moondream:latest など"
    fi
    if [[ $ver_ok -eq 0 && $started_by_me -eq 0 ]]; then
      echo "（補足）Ollama サーバ未起動の場合は、別端末で:"
      echo "  systemctl --user start ollama   # systemd 管理の場合"
      echo "  # または"
      echo "  ollama serve                     # 前面で起動"
    fi
  } >&2
fi
