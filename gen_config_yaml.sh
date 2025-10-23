#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
CONF_DIR="$ROOT/config"
YAML="$CONF_DIR/config.yaml"
ENVF="$CONF_DIR/.env"

mkdir -p "$CONF_DIR"

# ① Ollamaサーバ起動チェック → なければバックグラウンドで起動
if ! pgrep -x ollama >/dev/null 2>&1; then
  echo "⚙️ Ollama server not running. Starting it in background..."
  nohup ollama serve >/dev/null 2>&1 &
  sleep 3
fi

# ② モデル一覧取得（先頭を選択）
mapfile -t MODELS < <(ollama list 2>/dev/null | awk 'NR>1 {print $1}')
SELECTED="${MODELS[0]:-}"

# ③ YAML生成（コメントなし・相対パス）
{
  echo "app:"
  echo "  name: NeuroHub"
  echo "  timezone: Asia/Tokyo"
  echo "  env: dev"
  echo
  echo "paths:"
  echo "  base: ./"
  echo "  cache_asr: ./data/cache/asr"
  echo "  cache_tts: ./data/cache/tts"
  echo "  cache_mpv: ./data/cache/mpv"
  echo "  database: ./data/neurohub.db"
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
  echo "    host: http://127.0.0.1:11434"
  echo -n "    models:"
  if ((${#MODELS[@]}==0)); then
    echo " []"
  else
    echo
    for m in "${MODELS[@]}"; do
      echo "      - ${m}"
    done
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
  echo "  model: ./models/piper/ja-kokoro-high.onnx"
  echo "  out_wav: ./data/cache/tts/out.wav"
  echo "  speed:"
  echo
  echo "mpv:"
  echo "  audio_device:"
  echo "  default_volume:"
  echo "  ipc_dir: ./data/cache/mpv"
  echo "  common_opts:"
  echo
  echo "logging:"
  echo "  level:"
  echo "  dir: ./logs"
} > "$YAML"

# ④ .env 生成（なければ）
if [[ ! -f "$ENVF" ]]; then
  {
    echo "GEMINI_API_KEY="
    echo "DISCORD_BOT_TOKEN="
    echo "REMO_TOKEN="
  } > "$ENVF"
fi

echo "ok: wrote $YAML"
[[ -n "$SELECTED" ]] && echo "ollama.selected_model=$SELECTED" || echo "no local ollama models detected"
echo "ok: ensured $ENVF"
