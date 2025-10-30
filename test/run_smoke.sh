#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "[Smoke] import"
python - <<'PY'
import importlib
mods = [
    "services.agent.agent_cli",
    "services.llm.llm_common",
    "tools.bs_core",
]
for m in mods:
    importlib.import_module(m)
print("OK: imports")
PY
echo "[Smoke] config"
test -f config/config.yaml && echo "✅ config/config.yaml OK" || (echo "❌ missing config"; exit 1)
echo "[DONE]"
