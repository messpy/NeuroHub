#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
provider_huggingface.py - Hugging Face Router(OpenAI互換) 簡易クライアント
- Inference API ではなく Router(OpenAI互換) に統一
- 404 対策: モデルは <model-id>:<provider> 形式で指定
- 依存: requests
"""

import os
import sys
import json
import argparse
import requests
from typing import Any, Dict, List, Optional

def build_messages(system_text: Optional[str], user_text: str) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = []
    if system_text:
        msgs.append({"role": "system", "content": system_text})
    msgs.append({"role": "user", "content": user_text})
    return msgs

def parse_opt_kv(opts: Optional[List[str]]) -> Dict[str, Any]:
    if not opts:
        return {}
    out: Dict[str, Any] = {}
    for kv in opts:
        if "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        k, v = k.strip(), v.strip()
        # JSON 優先
        try:
            if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")) or v in ("true","false","null"):
                out[k] = json.loads(v.replace("'", '"'))
                continue
        except Exception:
            pass
        if v.lower() in ("true","false"):
            out[k] = (v.lower() == "true")
            continue
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
    ap = argparse.ArgumentParser(description="HF Router(OpenAI互換) client")
    ap.add_argument("prompt", nargs="+", help="ユーザープロンプト（スペース可）")
    ap.add_argument("--host", help="HF Router base URL（既定: env HF_HOST or https://router.huggingface.co/v1）")
    ap.add_argument("--model", help="モデル（既定: openai/gpt-oss-20b:groq）")
    ap.add_argument("--system", help="system プロンプト")
    ap.add_argument("--opt", action="append", help="key=val（temperature, top_p, max_tokens, stop など）")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    token = os.getenv("HF_TOKEN")
    if not token:
        print("[error] 環境変数 HF_TOKEN が未設定です", file=sys.stderr)
        return 2

    base_url = args.host or os.getenv("HF_HOST") or "https://router.huggingface.co/v1"
    url = f"{base_url.rstrip('/')}/chat/completions"

    # 重要: Router 用モデルは <model-id>:<provider>
    model = args.model or "openai/gpt-oss-20b:groq"

    user_text = " ".join(args.prompt)
    messages = build_messages(args.system, user_text)

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    # openai互換の代表パラメータを --opt 経由で上書き
    mapped = parse_opt_kv(args.opt)
    allow = {"temperature","top_p","max_tokens","frequency_penalty","presence_penalty","stop","seed","response_format"}
    for k, v in list(mapped.items()):
        if k in allow:
            payload[k] = v

    if args.debug:
        dbg = {"url": url, "model": model, "payload": payload}
        print("[debug] request:", json.dumps(dbg, ensure_ascii=False, indent=2), file=sys.stderr)

    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=args.timeout,
        )
        if resp.status_code != 200:
            print(f"[error] HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
            return 1
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print(content)
        if args.debug:
            meta = {
                "id": data.get("id"),
                "model": data.get("model", model),
                "finish_reason": data["choices"][0].get("finish_reason"),
                "usage": data.get("usage"),
            }
            print("[debug] response_meta:", json.dumps(meta, ensure_ascii=False), file=sys.stderr)
        return 0
    except Exception as e:
        print(f"[error] request failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
