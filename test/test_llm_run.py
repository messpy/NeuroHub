#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test/run_llm_tests.py
- 主要プロバイダ設定を事前チェック & 表示
- 絶対パス出力 / 環境変数・設定ファイル読み込み結果を可視化
- 実行時間計測 / 個別 .log 保存（日時フォルダ）
"""
from __future__ import annotations
import os
import sys
import json
import time
import datetime as dt
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from urllib.request import urlopen

# ====== パス設定 ======
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LLM_DIR = PROJECT_ROOT / "services" / "llm"
CONFIG_DIR = PROJECT_ROOT / "config"
ENV_FILE = CONFIG_DIR / ".env"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
LOG_ROOT = PROJECT_ROOT / "logs" / "tests"

PROMPT_DEFAULT = "日本語で1文だけ自己紹介"
PROMPT = None

# ====== デフォルトモデル ======
HF_MODEL_DEFAULT = os.getenv("HF_TEST_MODEL", "openai/gpt-oss-20b:groq")
OLLAMA_MODEL_DEFAULT = os.getenv("OLLAMA_TEST_MODEL", "qwen2.5:0.5b-instruct")
GEMINI_MODEL_DEFAULT = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            import yaml
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}


def reachable_ollama(host: str) -> bool:
    try:
        with urlopen(f"{host}/api/version", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def disp_prelude(cfg: Dict[str, Any], prompt: str) -> None:
    print("===== Test Prelude =====")
    print(f"Project Root  : {PROJECT_ROOT}")
    print(f"LLM Dir       : {LLM_DIR}")
    print(f"Config Dir    : {CONFIG_DIR}")
    print(f"  .env exists : {ENV_FILE.exists()} -> {ENV_FILE}")
    print(f"  config.yaml : {CONFIG_FILE.exists()} -> {CONFIG_FILE}")
    print()

    print("Environment Variables:")
    print(f"  HF_TOKEN          : {'<set>' if os.getenv('HF_TOKEN') else '<missing>'}")
    print(f"  GEMINI_API_KEY    : {'<set>' if os.getenv('GEMINI_API_KEY') else '<missing>'}")
    print(f"  OLLAMA_HOST       : {OLLAMA_HOST}")
    print()

    print("Model Config:")
    print(f"  HF model(default)      : {HF_MODEL_DEFAULT}")
    print(f"  Gemini model(default)  : {GEMINI_MODEL_DEFAULT}")
    print(f"  Ollama model(default)  : {OLLAMA_MODEL_DEFAULT}")
    print()

    if cfg:
        print("config.yaml (llm section):")
        print(json.dumps(cfg.get("llm", {}), ensure_ascii=False, indent=2))
        print()

    print(f"Test Prompt: {prompt}")
    print("========================================")
    print()


def run_and_log(name: str, cmd: List[str], log_dir: Path) -> Dict[str, Any]:
    log_path = log_dir / f"{name}_{dt.datetime.now().strftime('%H%M%S')}.log"
    start = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = round(time.perf_counter() - start, 3)

    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"[{name}] CMD: {' '.join(cmd)}\n")
        f.write(f"TIME: {elapsed}s\n\n[STDOUT]\n{proc.stdout}\n\n[STDERR]\n{proc.stderr}\n")

    status = (
        "OK"
        if proc.returncode == 0 and (proc.stdout or "").strip()
        else "NG"
    )

    return {"status": status, "elapsed": elapsed, "log": str(log_path)}


def main(argv: List[str]) -> int:
    global PROMPT
    PROMPT = " ".join(argv[1:]).strip() if len(argv) > 1 else PROMPT_DEFAULT

    today = dt.datetime.now().strftime("%Y-%m-%d")
    today_dir = LOG_ROOT / today
    today_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_config()
    disp_prelude(cfg, PROMPT)

    results: Dict[str, Dict[str, Any]] = {}

    # Hugging Face
    if os.getenv("HF_TOKEN"):
        cmd = [sys.executable, str(LLM_DIR / "provider_huggingface.py"),
               "--model", HF_MODEL_DEFAULT, PROMPT]
        results["huggingface"] = run_and_log("huggingface", cmd, today_dir)
    else:
        results["huggingface"] = {"status": "SKIP", "reason": "HF_TOKEN missing"}

    # Gemini
    if os.getenv("GEMINI_API_KEY"):
        cmd = [sys.executable, str(LLM_DIR / "provider_gemini.py"), PROMPT]
        results["gemini"] = run_and_log("gemini", cmd, today_dir)
    else:
        results["gemini"] = {"status": "SKIP", "reason": "GEMINI_API_KEY missing"}

    # Ollama
    if reachable_ollama(OLLAMA_HOST):
        cmd = [sys.executable, str(LLM_DIR / "provider_ollama.py"),
               "--model", OLLAMA_MODEL_DEFAULT, PROMPT]
        results["ollama"] = run_and_log("ollama", cmd, today_dir)
    else:
        results["ollama"] = {"status": "SKIP", "reason": "ollama down"}

    # CLI
    cli = LLM_DIR / "llm_cli.py"
    if cli.exists():
        cmd = [sys.executable, str(cli), PROMPT]
        results["cli"] = run_and_log("cli", cmd, today_dir)
    else:
        results["cli"] = {"status": "SKIP", "reason": "llm_cli.py missing"}

    # summary
    summary_path = today_dir / f"_summary_{dt.datetime.now().strftime('%H%M%S')}.log"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write(f"=== Summary @ {dt.datetime.now()} ===\n")
        f.write(f"Prompt: {PROMPT}\n\n")

        for name in ("huggingface", "gemini", "ollama", "cli"):
            r = results[name]
            if "elapsed" in r:
                f.write(f"{name:10s}: {r['status']} ({r['elapsed']}s) log={r['log']}\n")
            else:
                f.write(f"{name:10s}: {r['status']} {r.get('reason','')}\n")

        f.write("\nLogsDir: " + str(today_dir) + "\n")

    print(summary_path.read_text())
    return 1 if any(r["status"] == "NG" for r in results.values() if "status" in r) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
