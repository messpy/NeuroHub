#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
provider_gemini.py - Google Generative Language API (Gemini) クライアント最小版
- 依存: requests, (任意) python-dotenv, PyYAML
- 環境変数: GEMINI_API_KEY（必須）, GEMINI_API_URL(任意, 既定 https://generativelanguage.googleapis.com/v1)
- モデル: config.yaml の llm.gemini.model があれば優先、無ければ gemini-2.5-flash
- 使い方:
    python provider_gemini.py "こんにちは"
    python provider_gemini.py --system "あなたは有能なアシスタント" "要約して"
    python provider_gemini.py --opt temperature=0.7 --opt top_p=0.9 "俳句を作って"
"""

from __future__ import annotations
import os
import sys
import json
import argparse
from typing import Any, Dict, List, Optional
import requests

from llm_common import load_env_from_config, DebugLogger, load_config, get_llm_model_from_config

def parse_opt_kv(opts: Optional[List[str]]) -> Dict[str, Any]:
    if not opts:
        return {}
    out: Dict[str, Any] = {}
    for kv in opts:
        if "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        k, v = k.strip(), v.strip()
        # JSON優先
        try:
            if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")) or v in ("true","false","null"):
                out[k] = json.loads(v.replace("'", '"'))
                continue
        except Exception:
            pass
        if v.lower() in ("true","false"):
            out[k] = (v.lower() == "true"); continue
        try:
            out[k] = int(v); continue
        except ValueError:
            pass
        try:
            out[k] = float(v); continue
        except ValueError:
            pass
        out[k] = v
    return out

def main() -> int:
    ap = argparse.ArgumentParser(description="Gemini provider (minimal)")
    ap.add_argument("prompt", nargs="+", help="ユーザープロンプト（スペース可）")
    ap.add_argument("--system", help="system プロンプト")
    ap.add_argument("--opt", action="append", help="key=val（temperature, top_p など）")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    # 環境読み込み
    load_env_from_config()
    logger = DebugLogger(enabled=args.debug)

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("[error] 環境変数 GEMINI_API_KEY が未設定です", file=sys.stderr)
        return 2

    base = (os.getenv("GEMINI_API_URL") or "https://generativelanguage.googleapis.com/v1").rstrip("/")

    # config.yaml からモデル既定を取得（無い場合は flash）
    cfg = load_config()
    model = get_llm_model_from_config(cfg, "gemini", "gemini-2.5-flash")

    user_text = " ".join(args.prompt)
    text = (args.system + "\n" if args.system else "") + user_text

    opts = parse_opt_kv(args.opt)
    gen = {}
    if "temperature" in opts: gen["temperature"] = float(opts["temperature"])
    if "top_p" in opts: gen["topP"] = float(opts["top_p"])
    payload: Dict[str, Any] = {"contents": [{"parts": [{"text": text}]}]}
    if gen:
        payload["generationConfig"] = gen

    url = f"{base}/models/{model}:generateContent?key={api_key}"
    if args.debug:
        logger.dbg("POST", url)
        logger.dbg("payload", json.dumps(payload, ensure_ascii=False))

    try:
        r = requests.post(url, json=payload, timeout=args.timeout)
        if r.status_code != 200:
            print(f"[error] HTTP {r.status_code}: {r.text}", file=sys.stderr)
            return 1
        data = r.json()
        out = data["candidates"][0]["content"]["parts"][0]["text"]
        print(out)
        return 0
    except Exception as e:
        print(f"[error] request failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
