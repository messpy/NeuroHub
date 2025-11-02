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
    PYTHONPATH=. ./venv/bin/python test/test_llm_suite.py --ollama-model qwen2.5:1.5b-instruct
"""
import os, sys, time, subprocess, pathlib, argparse, urllib.request
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY   = sys.executable

# 統一テストプロンプト
DEFAULT_PROMPT = "Hello Worldを日本語で？"

def load_env():
    sys.path.insert(0, str(ROOT))
    try:
        # 環境変数をロード
        from services.llm.llm_common import load_env_from_config
        load_env_from_config(debug=False)
    except Exception as e:
        print(f"[warn] .env load skipped: {e}", file=sys.stderr)

def load_llm_config():
    """LLM設定をYAMLから読み込み"""
    config_path = ROOT / "config" / "llm_config.yaml"
    if not config_path.exists():
        return {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[warn] config load failed: {e}", file=sys.stderr)
        return {}

def run(cmd, timeout=120):
    t0 = time.time()
    r = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    dt = time.time() - t0
    return r.returncode, dt, (r.stdout or ""), (r.stderr or "")

def parse_response(stdout, stderr):
    """応答から実際のLLM返答を抽出"""
    # provider_*.py の出力から応答部分を抽出
    for line in stdout.splitlines():
        if line.strip() and not line.startswith("[") and not line.startswith("Response:"):
            return line.strip()
    return stdout.strip() or stderr.strip()

def test_gemini(prompt=DEFAULT_PROMPT, model=None, config=None):
    if not os.getenv("GEMINI_API_KEY"):
        return ("gemini", "SKIP", 0.0, "", "", "GEMINI_API_KEY missing")
    
    # configからモデル取得（引数優先）
    if model is None and config:
        model = config.get("llm", {}).get("providers", {}).get("gemini", {}).get("model", "gemini-1.5-flash")
    
    cmd = [PY, str(ROOT/"services/llm/provider_gemini.py"), "--debug"]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    
    rc, dt, out, err = run(cmd)
    response = parse_response(out, err) if rc == 0 else ""
    return ("gemini", "OK" if rc == 0 else "NG", dt, response, out, err)

def ollama_alive(host):
    try:
        with urllib.request.urlopen(host.rstrip("/")+"/api/version", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False

def test_ollama(prompt=DEFAULT_PROMPT, model=None, config=None):
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    if not ollama_alive(host):
        return ("ollama", "SKIP", 0.0, "", "", f"Ollama server not responding: {host}")
    
    # configからモデル取得（引数優先）
    if model is None and config:
        model = config.get("llm", {}).get("providers", {}).get("ollama", {}).get("model", "qwen2.5:1.5b-instruct")
    if model is None:
        model = "qwen2.5:1.5b-instruct"
    
    cmd = [PY, str(ROOT/"services/llm/provider_ollama.py"), "--model", model, prompt]
    rc, dt, out, err = run(cmd)
    response = parse_response(out, err) if rc == 0 else ""
    return ("ollama", "OK" if rc == 0 else "NG", dt, response, out, err)

def test_hugging(prompt=DEFAULT_PROMPT, model=None, config=None):
    if not os.getenv("HF_TOKEN"):
        return ("hugging", "SKIP", 0.0, "", "", "HF_TOKEN missing")
    
    # configからモデル取得（引数優先）
    if model is None and config:
        model = config.get("llm", {}).get("providers", {}).get("huggingface", {}).get("model", "microsoft/phi-2")
    
    cmd = [PY, str(ROOT/"services/llm/provider_huggingface.py"), "--debug"]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    
    rc, dt, out, err = run(cmd)
    response = parse_response(out, err) if rc == 0 else ""
    return ("hugging", "OK" if rc == 0 else "NG", dt, response, out, err)

def main():
    ap = argparse.ArgumentParser(description="LLM provider test suite")
    ap.add_argument("providers", nargs="*", help="gemini / ollama / hugging（省略で全て）")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT, help=f"テストプロンプト（デフォルト: {DEFAULT_PROMPT}）")
    ap.add_argument("--ollama-model", dest="ollama_model", help="Ollamaモデル名（yamlより優先）")
    ap.add_argument("--gemini-model", dest="gemini_model", help="Geminiモデル名（yamlより優先）")
    ap.add_argument("--hugging-model", dest="hugging_model", help="HuggingFaceモデル名（yamlより優先）")
    ap.add_argument("--quiet", action="store_true", help="結果サマリのみ出力")
    ap.add_argument("--show-response", action="store_true", help="LLM応答を表示")
    args = ap.parse_args()

    want = [p.lower() for p in (args.providers or ["gemini", "ollama", "hugging"])]
    valid = {"gemini","ollama","hugging"}
    want = [p for p in want if p in valid] or ["gemini","ollama","hugging"]

    load_env()
    config = load_llm_config()

    results = []
    if "gemini" in want:
        results.append(test_gemini(prompt=args.prompt, model=args.gemini_model, config=config))
    if "ollama" in want:
        results.append(test_ollama(prompt=args.prompt, model=args.ollama_model, config=config))
    if "hugging" in want:
        results.append(test_hugging(prompt=args.prompt, model=args.hugging_model, config=config))

    print("\n=== LLM TEST SUITE RESULT ===")
    print(f"Prompt: {args.prompt}")
    print("")
    
    fail = False
    for name, status, dt, response, out, err in results:
        print(f"[{name:7}] {status:4}  ({dt:.3f}s)")
        
        # 応答情報を表示
        if args.show_response or not args.quiet:
            if response and status == "OK":
                print(f"  [Response] {response[:200]}{'...' if len(response) > 200 else ''}")
        
        if not args.quiet:
            if out.strip() and status != "OK":
                print("  [STDOUT]")
                print("\n".join("    "+line for line in out.strip().splitlines()[:20]))
            if err.strip():
                print("  [STDERR]")
                print("\n".join("    "+line for line in err.strip().splitlines()[:10]))
        
        if status == "NG":
            fail = True
    
    return 1 if fail else 0

if __name__ == "__main__":
    sys.exit(main())
