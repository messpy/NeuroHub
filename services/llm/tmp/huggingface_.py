#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hf_chat.py - Hugging Face Router(OpenAI互換) 用のチャットCLI
Ollama互換の引数を踏襲:
  prompt (nargs="+")
  --host, --model, --system, --opt key=val (複数), --keep-alive, --timeout, --debug, --systemd
設定ファイル（任意）:
  config/.env : HF_TOKEN, HF_HOST
  config/config.yaml : model: <default_model>
"""

import os
import sys
import json
import argparse
from typing import Any, Dict, List, Optional

# 依存: openai, pyyaml, python-dotenv
try:
    from openai import OpenAI
except Exception as e:
    print("[error] openai パッケージがありません: pip install openai", file=sys.stderr)
    sys.exit(2)

# 設定読み込み（任意）
def load_env() -> None:
    # ./config/.env を優先して読む。無ければスルー
    env_path = os.path.join("config", ".env")
    if os.path.exists(env_path):
        try:
            from dotenv import load_dotenv
        except Exception:
            print("[warn] python-dotenv 未インストール: pip install python-dotenv", file=sys.stderr)
            return
        load_dotenv(env_path)

def load_yaml_config() -> Dict[str, Any]:
    cfg = {}
    yml = os.path.join("config", "config.yaml")
    if os.path.exists(yml):
        try:
            import yaml
            with open(yml, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    cfg.update(data)
        except Exception as e:
            print(f"[warn] config.yaml 読み込み失敗: {e}", file=sys.stderr)
    return cfg

# key=val → 型推論（bool/int/float/json/str）
def parse_opt_kv(opts: List[str]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for kv in opts:
        if "=" not in kv:
            print(f"[warn] --opt は key=val 形式です: {kv}", file=sys.stderr)
            continue
        k, v = kv.split("=", 1)
        k = k.strip()
        v = v.strip()
        # JSON（配列/オブジェクト/true/false/null）を優先
        try:
            if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")) or v in ("true","false","null"):
                parsed[k] = json.loads(v.replace("'", '"'))
                continue
        except Exception:
            pass
        # bool
        if v.lower() in ("true","false"):
            parsed[k] = v.lower() == "true"
            continue
        # int
        try:
            parsed[k] = int(v)
            continue
        except ValueError:
            pass
        # float
        try:
            parsed[k] = float(v)
            continue
        except ValueError:
            pass
        # それ以外は文字列
        parsed[k] = v
    return parsed

def build_messages(system_text: Optional[str], user_text: str) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = []
    if system_text:
        msgs.append({"role": "system", "content": system_text})
    msgs.append({"role": "user", "content": user_text})
    return msgs

def main() -> int:
    load_env()
    cfg = load_yaml_config()

    ap = argparse.ArgumentParser(description="HF Router Chat CLI (Ollama互換風)")
    ap.add_argument("prompt", nargs="+", help="ユーザープロンプト（スペース可）")
    ap.add_argument("--host", help="HF Router ベースURL（未指定なら config/.env の HF_HOST か既定）")
    ap.add_argument("--model", help="モデル名（未指定なら config.yaml の model）")
    ap.add_argument("--system", help="system プロンプト")
    ap.add_argument("--opt", action="append", help="オプション key=val（複数可）")
    ap.add_argument("--keep-alive", default="5m", help="(互換用) 未使用")
    ap.add_argument("--timeout", type=int, default=120, help="タイムアウト秒")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--systemd", action="store_true", help="(互換用) 未使用")
    args = ap.parse_args()

    # 既定の host / model
    base_url = args.host or os.environ.get("HF_HOST") or "https://router.huggingface.co/v1"
    model = args.model or cfg.get("model") or "google/gemma-2-2b-it"

    if args.systemd:
        print("[warn] --systemd はHF Routerでは起動対象が無いため無視します", file=sys.stderr)

    # HF_TOKEN 必須
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("[error] 環境変数 HF_TOKEN が未設定です", file=sys.stderr)
        return 2

    # オプション解釈
    opt = parse_opt_kv(args.opt or [])

    # OpenAIクライアント生成（OpenAI互換 / Router）
    client = OpenAI(base_url=base_url, api_key=token)
    client_req = client.with_options(timeout=args.timeout)

    # stream 指定があればストリーミング、それ以外は通常
    stream = bool(opt.pop("stream", False))

    # OpenAI chat.completions パラメータへマッピング
    # 利用可能代表: temperature, top_p, max_tokens, frequency_penalty, presence_penalty, stop, seed, response_format など
    # （未知キーはそのまま渡さない）
    allow_keys = {
        "temperature","top_p","max_tokens","frequency_penalty","presence_penalty",
        "stop","seed","response_format"
    }
    mapped = {k:v for k,v in opt.items() if k in allow_keys}

    # プロンプト
    user_text = " ".join(args.prompt)
    messages = build_messages(args.system, user_text)

    if args.debug:
        dbg = {
            "base_url": base_url,
            "model": model,
            "messages": messages,
            "mapped_opts": mapped,
            "stream": stream,
            "timeout": args.timeout,
        }
        print("[debug] request:", json.dumps(dbg, ensure_ascii=False, indent=2), file=sys.stderr)

    try:
        if stream:
            # ストリーミング（標準出力へ逐次）
            with client_req.chat.completions.stream(
                model=model,
                messages=messages,
                **mapped
            ) as s:
                for ev in s:
                    if ev.type == "chunk" and ev.data.choices:
                        delta = ev.data.choices[0].delta
                        if delta and delta.content:
                            sys.stdout.write(delta.content)
                            sys.stdout.flush()
                # 行末整形
                print()
            return 0
        else:
            # 通常（1レスポンスで出力）
            resp = client_req.chat.completions.create(
                model=model,
                messages=messages,
                **mapped
            )
            out = resp.choices[0].message.content
            print(out)
            if args.debug:
                # レスポンスの一部だけ（全文は大きいことがある）
                meta = {
                    "id": resp.id,
                    "model": getattr(resp, "model", model),
                    "finish_reason": resp.choices[0].finish_reason,
                    "usage": getattr(resp, "usage", None)
                }
                print("[debug] response_meta:", json.dumps(meta, ensure_ascii=False), file=sys.stderr)
            return 0
    except Exception as e:
        print(f"[error] request failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
