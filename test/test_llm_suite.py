#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_llm_suite.py
- まとめて / 単体指定で LLM プロバイダの実行テストを行う最小ハーネス
  使い方:
    PYTHONPATH=. ./venv/bin/python test/test_llm_suite.py           # 全部
    PYTHONPATH=. ./venv/bin/python test/test_llm_suite.py gemini
    PYTHONPATH=. ./venv/bin/python test/test_llm_suite.py ollama
    PYTHONPATH=. ./venv/bin/python test/test_llm_suite.py hugging
    PYTHONPATH=. ./venv/bin/python test/test_llm_suite.py gemini ollama
"""
import os, sys, time, subprocess, pathlib, argparse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY   = sys.executable

def load_env():
    sys.path.insert(0, str(ROOT))
    try:
        from services.llm.llm_common import load_env_from_config
        load_env_from_config(debug=False)
    except Exception as e:
        print(f"[warn] .env load skipped: {e}", file=sys.stderr)

def run(cmd, timeout=120):
    t0 = time.time()
    r = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    dt = time.time() - t0
    return r.returncode, dt, (r.stdout or ""), (r.stderr or "")

def test_gemini(prompt="1+1"):
    if not os.getenv("GEMINI_API_KEY"):
        return ("gemini", "SKIP", 0.0, "", "GEMINI_API_KEY missing")
    cmd = [PY, str(ROOT/"services/llm/provider_gemini.py"), "--debug", prompt]
    rc, dt, out, err = run(cmd)
    return ("gemini", "OK" if rc == 0 else "NG", dt, out, err)

def ollama_alive(host):
    try:
        with urllib.request.urlopen(host.rstrip("/")+"/api/version", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False

def test_ollama(prompt="カタカナで1+1の答え", model="qwen2.5:0.5b-instruct"):
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    if not ollama_alive(host):
        return ("ollama", "SKIP", 0.0, "", f"Ollama server not responding: {host}")
    cmd = [PY, str(ROOT/"services/llm/provider_ollama.py"), "--model", model, prompt]
    rc, dt, out, err = run(cmd)
    return ("ollama", "OK" if rc == 0 else "NG", dt, out, err)

def test_hugging(prompt="日本語で自己紹介を一文で"):
    if not os.getenv("HF_TOKEN"):
        return ("hugging", "SKIP", 0.0, "", "HF_TOKEN missing")
    cmd = [PY, str(ROOT/"services/llm/provider_huggingface.py"), "--debug", prompt]
    rc, dt, out, err = run(cmd)
    return ("hugging", "OK" if rc == 0 else "NG", dt, out, err)

def main():
    ap = argparse.ArgumentParser(description="LLM provider test suite")
    ap.add_argument("providers", nargs="*", help="gemini / ollama / hugging（省略で全て）")
    ap.add_argument("--ollama-model", dest="ollama_model", default="qwen2.5:0.5b-instruct")
    ap.add_argument("--quiet", action="store_true", help="結果サマリのみ出力")
    args = ap.parse_args()

    want = [p.lower() for p in (args.providers or ["gemini", "ollama", "hugging"])]
    valid = {"gemini","ollama","hugging"}
    want = [p for p in want if p in valid] or ["gemini","ollama","hugging"]

    load_env()

    results = []
    if "gemini" in want:   results.append(test_gemini())
    if "ollama" in want:   results.append(test_ollama(model=args.ollama_model))
    if "hugging" in want:  results.append(test_hugging())

    print("\n=== LLM TEST SUITE RESULT ===")
    fail = False
    for name, status, dt, out, err in results:
        print(f"[{name:7}] {status:4}  ({dt:.3f}s)")
        if not args.quiet:
            if out.strip():
                print("  [STDOUT]")
                print("\n".join("    "+line for line in out.strip().splitlines()[:20]))
            if err.strip():
                print("  [STDERR]")
                print("\n".join("    "+line for line in err.strip().splitlines()[:20]))
        if status == "NG":
            fail = True
    return 1 if fail else 0

if __name__ == "__main__":
    sys.exit(main())
