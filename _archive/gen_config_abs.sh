#!/usr/bin/env bash
# NeuroHub: 絶対パス＆システム情報つき config.yaml 生成（_archive直下用の簡潔版）
# 実行例: bash gen_config_abs.sh  /  bash gen_config_abs.sh --debug
set -euo pipefail

DEBUG=${1:-}
[[ "$DEBUG" == "--debug" ]] && set -x

# ルートはこのスクリプトの1つ上（/home/.../NeuroHub）
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
CONF_DIR="$ROOT/config"
YAML="$CONF_DIR/config.yaml"
ENVF="$CONF_DIR/.env"

# 必要ディレクトリ
mkdir -p "$CONF_DIR" \
         "$ROOT/data/cache/asr" "$ROOT/data/cache/tts" "$ROOT/data/cache/mpv" \
         "$ROOT/logs" "$ROOT/models/piper"

# システム情報（失敗しても続行）
safe() { "$@" 2>/dev/null || true; }
HOSTNAME_FQDN="$(safe hostname -f || hostname)"
USER_NAME="$(safe id -un || whoami)"
OS_NAME="$(safe awk -F= '/^PRETTY_NAME/ {gsub(/"/,"",$2); print $2}' /etc/os-release)"
[[ -z "${OS_NAME:-}" ]] && OS_NAME="$(uname -s)"
KERNEL="$(uname -r)"
ARCH="$(uname -m)"
CPU_MODEL="$(safe awk -F: '/model name/ {sub(/^ /,"",$2); print $2; exit}' /proc/cpuinfo)"
CPU_CORES="$(safe nproc || echo 1)"
MEM_MB="$(safe awk '/Mem:/ {print $2}' < <(free -m))"
MACHINE_ID="$(safe cat /etc/machine-id)"
IPV4S="$(safe ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1 | paste -sd',' -)"
CREATED_AT="$(date -Is)"

# Ollama（短タイムアウト、無ければ空配列）
OLLAMA_HOST_VAL="${OLLAMA_HOST:-http://127.0.0.1:11434}"
MODELS=(); SELECTED=""
if command -v curl >/dev/null 2>&1 && command -v ollama >/dev/null 2>&1; then
  if curl -sS --max-time 2 "${OLLAMA_HOST_VAL%/}/api/tags" >/dev/null; then
    mapfile -t MODELS < <(ollama list 2>/dev/null | awk 'NR>1 {print $1}') || true
    SELECTED="${MODELS[0]:-}"
  fi
fi

# YAML 生成
{
  echo "app:"
  echo "  name: NeuroHub"
  echo "  timezone: Asia/Tokyo"
  echo "  env: dev"
  echo
  echo "paths:"
  echo "  base: $ROOT"
  echo "  cache_asr: $ROOT/data/cache/asr"
  echo "  cache_tts: $ROOT/data/cache/tts"
  echo "  cache_mpv: $ROOT/data/cache/mpv"
  echo "  database: $ROOT/data/neurohub.db"
  echo
  echo "llm:"
  echo "  default: ollama"
  echo "  gemini:"
  echo "    api_url: https://generativelanguage.googleapis.com/v1beta/models"
  echo "    model: gemini-1.5-pro-latest"
  echo "    temperature:"
  echo "    max_output_tokens:"
  echo "    timeout_sec:"
  echo "  ollama:"
  echo "    host: $OLLAMA_HOST_VAL"
  if ((${#MODELS[@]})); then
    echo "    models:"
    for m in "${MODELS[@]}"; do echo "      - $m"; done
  else
    echo "    models: []"
  fi
  echo "    selected_model: ${SELECTED}"
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
  echo "  model: $ROOT/models/piper/ja-kokoro-high.onnx"
  echo "  out_wav: $ROOT/data/cache/tts/out.wav"
  echo "  speed:"
  echo
  echo "mpv:"
  echo "  audio_device:"
  echo "  default_volume:"
  echo "  ipc_dir: $ROOT/data/cache/mpv"
  echo "  common_opts:"
  echo
  echo "logging:"
  echo "  level: INFO"
  echo "  dir: $ROOT/logs"
  echo
  echo "system:"
  echo "  created_at: \"$CREATED_AT\""
  echo "  machine_id: \"${MACHINE_ID}\""
  echo "  hostname: \"${HOSTNAME_FQDN}\""
  echo "  user: \"${USER_NAME}\""
  echo "  os: \"${OS_NAME}\""
  echo "  kernel: \"${KERNEL}\""
  echo "  arch: \"${ARCH}\""
  echo "  cpu_model: \"${CPU_MODEL}\""
  echo "  cpu_cores: ${CPU_CORES}"
  echo "  memory_mb: ${MEM_MB}"
  echo "  ipv4: [${IPV4S}]"
  echo "  project_root: \"$ROOT\""
} > "$YAML"

# .env（既存尊重）
touch "$ENVF"
grep -q '^GEMINI_API_KEY=' "$ENVF" || echo 'GEMINI_API_KEY=' >> "$ENVF"
grep -q '^DISCORD_BOT_TOKEN=' "$ENVF" || echo 'DISCORD_BOT_TOKEN=' >> "$ENVF"
grep -q '^REMO_TOKEN=' "$ENVF" || echo 'REMO_TOKEN=' >> "$ENVF"
grep -q '^OLLAMA_HOST=' "$ENVF" || echo "OLLAMA_HOST=$OLLAMA_HOST_VAL" >> "$ENVF"

echo "ok: wrote $YAML"
echo "ok: ensured $ENVF"
[[ -n "$SELECTED" ]] && echo "ollama.selected_model=$SELECTED" || echo "no local ollama models"