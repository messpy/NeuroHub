#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
import os
import sys
import subprocess
import shlex
from pathlib import Path
import urllib.request
import urllib.error

# ===== llm_common から .env / config 読み込み =====
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from llm_common import (
    load_env_from_config,
    load_config,
    get_llm_model_from_config,
    DebugLogger,
)

load_env_from_config()   # ~/work/NeuroHub/config/.env を反映
CFG = load_config()      # ~/work/NeuroHub/config/config.yaml
DBG = DebugLogger(False)

# ===== 設定解決 =====
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

# モデル優先順位: OLLAMA_MODEL > OLLAMA_TEST_MODEL > config.yaml > 既定
PREFERRED_MODEL = (
    os.getenv("OLLAMA_MODEL")
    or os.getenv("OLLAMA_TEST_MODEL")
    or get_llm_model_from_config(CFG, "ollama", "qwen2.5:0.5b-instruct")
)

# 小さめ中心のフォールバック候補（無ければ順に pull）
FALLBACK_MODELS = [
    "qwen2.5:0.5b-instruct",
    "llama3.2:1b",
    "qwen2.5:1.5b-instruct",
    "phi4:latest",
]

# ===== HTTPユーティリティ（headers=Noneバグ修正済） =====
def _http_json(method: str, path: str, payload: dict | None = None, timeout: int = 120) -> dict:
    url = f"{OLLAMA_HOST}{path}"
    if payload is None:
        data = None
        headers = {}  # ← ここを必ず dict にする（以前の None.items() 例外対策）
    else:
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        if not body:
            return {}
        return json.loads(body.decode("utf-8"))

# ===== モデル確認・pull =====
def _tags() -> list[str]:
    """ローカルにあるモデル名一覧（/api/tags）。"""
    try:
        obj = _http_json("GET", "/api/tags", None, timeout=10)
        models = obj.get("models", []) if isinstance(obj, dict) else []
        names = []
        for m in models:
            n = (m or {}).get("name")
            if n:
                names.append(str(n))
        return names
    except Exception:
        return []

def _has_model_locally(name: str) -> bool:
    name = name.strip()
    existing = _tags()
    if name in existing:
        return True
    # ":latest" 指定に対する簡易一致（ベース名一致）
    if name.endswith(":latest"):
        base = name.split(":")[0]
        return any(x.split(":")[0] == base for x in existing)
    return False

def _pull(model: str) -> bool:
    """`ollama pull <model>` を実行。成功で True。"""
    cmd = ["ollama", "pull", model]
    DBG.dbg("pull:", " ".join(shlex.quote(x) for x in cmd))
    try:
        p = subprocess.run(cmd, check=False, text=True, capture_output=True)
        DBG.dbg("pull.rc=", p.returncode, "out.len=", len(p.stdout), "err.len=", len(p.stderr))
        return p.returncode == 0
    except Exception as e:
        DBG.dbg("pull.error:", e)
        return False

def ensure_model(preferred: str | None) -> str:
    """
    1) preferred を優先（ローカル無ければ pull）
    2) ダメなら FALLBACK_MODELS を順に pull
    戻り値: 利用可能なモデル名（全滅なら例外）
    """
    candidates: list[str] = []
    if preferred:
        candidates.append(preferred)
    for m in FALLBACK_MODELS:
        if m not in candidates:
            candidates.append(m)

    for name in candidates:
        if _has_model_locally(name):
            DBG.dbg("model exists:", name)
            return name
        DBG.dbg("model missing:", name, " -> try pull")
        if _pull(name) and _has_model_locally(name):
            return name

    raise RuntimeError("no available model (pull failed). Tried: " + ", ".join(candidates))

# ===== 推論 =====
def _infer_generate(model: str, prompt: str) -> dict:
    return _http_json("POST", "/api/generate", {"model": model, "prompt": prompt, "stream": False})

def _infer_chat(model: str, prompt: str) -> dict:
    return _http_json("POST", "/api/chat", {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    })

def infer(model: str, prompt: str) -> str:
    """
    /api/generate → 404/405 のとき /api/chat へフォールバック。
    戻り値はテキスト（未知形式は JSON のまま）。
    """
    try:
        obj = _infer_generate(model, prompt)
    except urllib.error.HTTPError as e:
        if e.code not in (404, 405):
            raise
        obj = _infer_chat(model, prompt)

    if isinstance(obj, dict):
        if isinstance(obj.get("response"), str):
            return obj["response"].strip()
        msg = obj.get("message", {})
        if isinstance(msg, dict) and isinstance(msg.get("content"), str):
            return msg["content"].strip()
    return json.dumps(obj, ensure_ascii=False)

# ===== CLI =====
def main() -> int:
    ap = argparse.ArgumentParser(description="Ollama provider (.env/config + auto-pull + fallback)")
    ap.add_argument("--model", help="使いたいモデル名。未指定なら .env/config → FALLBACK で自動確保")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("prompt", nargs="+", help="プロンプト")
    args = ap.parse_args()

    DBG.enabled = args.debug
    prompt = " ".join(args.prompt)

    # サーバ生存確認
    try:
        ver = _http_json("GET", "/api/version", None, timeout=5)
        DBG.dbg("version:", ver)
    except Exception as e:
        print(f"[error] ollama not healthy or unreachable at {OLLAMA_HOST}: {e}", file=sys.stderr)
        return 1

    # モデル確保（ローカルに無ければ自動 pull / フォールバック）
    try:
        model = ensure_model(args.model or PREFERRED_MODEL)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 2

    DBG.dbg("using model:", model)

    # 推論
    try:
        text = infer(model, prompt)
    except Exception as e:
        print(f"[error] ollama request failed: {e}", file=sys.stderr)
        return 3

    print(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
