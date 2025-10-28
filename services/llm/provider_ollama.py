#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/llm/provider_ollama.py
- Ollama（/api/chat 優先、失敗時 /api/generate へフォールバック）
"""
from __future__ import annotations
import os, sys, json, argparse, requests
from llm_common import load_env_from_config, ensure_ollama_running

def main() -> int:
    load_env_from_config()  # .env
    ap = argparse.ArgumentParser(description="Ollama provider")
    ap.add_argument("prompt", nargs="+", help="ユーザープロンプト")
    ap.add_argument("--model", help="モデル名（未指定: $OLLAMA_TEST_MODEL or qwen2.5:0.5b-instruct）")
    ap.add_argument("--host", help="Ollama ホスト（未指定: $OLLAMA_HOST or http://127.0.0.1:11434）")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    host = (args.host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
    model = args.model or os.getenv("OLLAMA_TEST_MODEL", "qwen2.5:0.5b-instruct")
    prompt = " ".join(args.prompt)

    if not ensure_ollama_running(host):
        print(f"[error] ollama not reachable: {host}", file=sys.stderr)
        return 1

    def post(path: str, payload: dict) -> requests.Response:
        url = f"{host}{path}"
        if args.debug:
            sys.stderr.write(f"[debug] POST {url}\n{json.dumps(payload, ensure_ascii=False)}\n")
            sys.stderr.flush()
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        return r

    # 1) /api/chat を試す
    try:
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        r = post("/api/chat", payload)
        data = r.json()
        if isinstance(data, dict):
            msg = data.get("message") or {}
            content = (msg.get("content") or "").strip()
            if content:
                print(content); return 0
            # ストリーム合成の可能性
            if data.get("done") and "messages" in data:
                chunks = [m.get("content", "") for m in data.get("messages", [])]
                out = "".join(chunks).strip()
                if out:
                    print(out); return 0
    except Exception as e:
        if args.debug:
            print(f"[debug] /api/chat failed: {e}", file=sys.stderr)

    # 2) /api/generate にフォールバック
    try:
        payload = {"model": model, "prompt": prompt, "stream": False}
        r = post("/api/generate", payload)
        data = r.json()
        out = (data.get("response") or "").strip()
        if out:
            print(out); return 0
        print("[error] empty response from /api/generate", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[error] ollama request failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
