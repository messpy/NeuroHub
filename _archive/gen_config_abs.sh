#!/usr/bin/env bash
# NeuroHub: 絶対パス＆システム情報つき config.yaml 生成（_archive直下用）
# 実行例: bash gen_config_abs.sh  /  bash gen_config_abs.sh --debug
set -euo pipefail

DEBUG=${1:-}
[[ "${DEBUG}" == "--debug" ]] && set -x

# ルート（このスクリプトの1つ上: /home/.../NeuroHub）
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
CONF_DIR="$ROOT/config"
YAML="$CONF_DIR/config.yaml"
ENVF="$CONF_DIR/.env"

# 必要ディレクトリ
mkdir -p "$CONF_DIR" \
         "$ROOT/data/cache/asr" "$ROOT/data/cache/tts" "$ROOT/data/cache/mpv" \
         "$ROOT/logs" "$ROOT/models/piper"

# ---- 収集: システム情報（失敗しても続行） ----
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
IPV4S_CSV="$(safe ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1 | paste -sd',' -)"
CREATED_AT="$(date -Is)"

# ---- Ollama（短タイムアウト、無ければ空） ----
OLLAMA_HOST_VAL="${OLLAMA_HOST:-http://127.0.0.1:11434}"
MODELS_BLOCK="    models: []"
SELECTED=""
if command -v curl >/dev/null 2>&1 && command -v ollama >/dev/null 2>&1; then
  if curl -sS --max-time 2 "${OLLAMA_HOST_VAL%/}/api/tags" >/dev/null; then
    mapfile -t MODELS < <(ollama list 2>/dev/null | awk 'NR>1 {print $1}') || true
    if ((${#MODELS[@]})); then
      SELECTED="${MODELS[0]}"
      MODELS_BLOCK="    models:"
      for m in "${MODELS[@]}"; do
        MODELS_BLOCK+=$'\n'"      - ${m}"
      done
    fi
  fi
fi

# IPv4 配列表現（空なら空配列）
if [[ -n "${IPV4S_CSV}" ]]; then
  IPV4_YAML="[${IPV4S_CSV}]"
else
  IPV4_YAML="[]"
fi

# ---- YAML 本文（ヒアドキュメントは“展開なし”でテンプレ → 後から置換） ----
read -r -d '' YAML_TMPL <<'EOF'
app:
  name: NeuroHub
  timezone: Asia/Tokyo
  env: dev

paths:
  base: __ROOT__
  cache_asr: __ROOT__/data/cache/asr
  cache_tts: __ROOT__/data/cache/tts
  cache_mpv: __ROOT__/data/cache/mpv
  database: __ROOT__/data/neurohub.db

llm:
  default: gemini
  gemini:
    api_url: https://generativelanguage.googleapis.com/v1
    model: gemini-2.5-flash
    temperature:
    max_output_tokens:
    timeout_sec:
  ollama:
    host: __OLLAMA_HOST_VAL__
__MODELS_BLOCK__
    selected_model: __SELECTED__
    temperature:
    num_ctx:
    num_thread:

asr:
  engine:
  model:
  timeout_sec:

tts:
  engine:
  model: __ROOT__/models/piper/ja-kokoro-high.onnx
  out_wav: __ROOT__/data/cache/tts/out.wav
  speed:

mpv:
  audio_device:
  default_volume:
  ipc_dir: __ROOT__/data/cache/mpv
  common_opts:

logging:
  level: INFO
  dir: __ROOT__/logs

system:
  created_at: "__CREATED_AT__"
  machine_id: "__MACHINE_ID__"
  hostname: "__HOSTNAME_FQDN__"
  user: "__USER_NAME__"
  os: "__OS_NAME__"
  kernel: "__KERNEL__"
  arch: "__ARCH__"
  cpu_model: "__CPU_MODEL__"
  cpu_cores: __CPU_CORES__
  memory_mb: __MEM_MB__
  ipv4: __IPV4_YAML__
  project_root: "__ROOT__
EOF

# 置換（安全に1回ずつ）
OUT="$YAML_TMPL"
OUT="${OUT//__ROOT__/$ROOT}"
OUT="${OUT//__OLLAMA_HOST_VAL__/$OLLAMA_HOST_VAL}"
OUT="${OUT//__MODELS_BLOCK__/$MODELS_BLOCK}"
OUT="${OUT//__SELECTED__/$SELECTED}"
OUT="${OUT//__CREATED_AT__/$CREATED_AT}"
OUT="${OUT//__MACHINE_ID__/$MACHINE_ID}"
OUT="${OUT//__HOSTNAME_FQDN__/$HOSTNAME_FQDN}"
OUT="${OUT//__USER_NAME__/$USER_NAME}"
OUT="${OUT//__OS_NAME__/$OS_NAME}"
OUT="${OUT//__KERNEL__/$KERNEL}"
OUT="${OUT//__ARCH__/$ARCH}"
OUT="${OUT//__CPU_MODEL__/$CPU_MODEL}"
OUT="${OUT//__CPU_CORES__/$CPU_CORES}"
OUT="${OUT//__MEM_MB__/$MEM_MB}"
OUT="${OUT//__IPV4_YAML__/$IPV4_YAML}"

# YAML 書き込み
printf '%s\n' "$OUT" > "$YAML"
echo "ok: wrote $YAML"

# .env は「初回のみ作成」。存在する場合は一切変更しない
if [[ ! -f "$ENVF" ]]; then
  umask 077
  cat > "$ENVF" <<EOF
# NeuroHub environment
# ※このファイルは初回生成のみ。以後スクリプトは上書きしません。
GEMINI_API_KEY=
DISCORD_BOT_TOKEN=
REMO_TOKEN=
OLLAMA_HOST=$OLLAMA_HOST_VAL
EOF
  echo "ok: created $ENVF"
else
  echo "ok: kept existing $ENVF (no changes)"
fi

# 参考出力
[[ -n "$SELECTED" ]] && echo "ollama.selected_model=$SELECTED" || echo "no local ollama models"