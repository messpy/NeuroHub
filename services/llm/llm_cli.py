#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/llm/llm_cli.py
- シンプルCLI（スマートフォールバック）
"""
from __future__ import annotations
import os, sys, argparse, subprocess
from pathlib import Path
from llm_common import load_env_from_config

def main() -> int:
    load_env_from_config()  # ★ debug引数は付けない（将来互換のため）

    ap = argparse.ArgumentParser(description="LLM CLI")
    ap.add_argument("prompt", nargs="+", help="ユーザープロンプト")
    ap.add_argument("--smart", action="store_true", help="HF→Ollama→Gemini 自動フォールバック")
    args = ap.parse_args()
    prompt = " ".join(args.prompt)

    # デフォルトでスマート実行をオン（env LLM_SMART=0 で無効化）
    if args.smart or os.getenv("LLM_SMART", "1") == "1":
        order = os.getenv("LLM_SMART_ORDER", "huggingface,ollama,gemini").split(",")
        tried = []
        for name in [x.strip() for x in order if x.strip()]:
            if name == "huggingface" and os.getenv("HF_TOKEN"):
                cmd = [sys.executable, str(Path(__file__).parent / "provider_huggingface.py"),
                       "--model", os.getenv("HF_TEST_MODEL", "openai/gpt-oss-20b:groq"),
                       prompt]
            elif name == "ollama":
                cmd = [sys.executable, str(Path(__file__).parent / "provider_ollama.py"),
                       "--model", os.getenv("OLLAMA_TEST_MODEL", "qwen2.5:0.5b-instruct"),
                       prompt]
            elif name == "gemini" and os.getenv("GEMINI_API_KEY"):
                cmd = [sys.executable, str(Path(__file__).parent / "provider_gemini.py"), prompt]
            else:
                tried.append(f"{name}:skip"); continue

            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode == 0 and p.stdout.strip():
                print(p.stdout.strip()); return 0
            tried.append(f"{name}:NG")

        print("[error] all providers failed: " + ", ".join(tried), file=sys.stderr)
        return 1

    print("[error] no provider selected; try --smart", file=sys.stderr)
    return 1

if __name__ == "__main__":
    sys.exit(main())
