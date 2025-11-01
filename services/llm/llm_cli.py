#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/llm/llm_cli.py

スマートフォールバックで LLM を呼び出す統一 CLI。
- フォールバック順は LLM_SMART_ORDER（既定: "huggingface,ollama,gemini"）
- 実際に使った provider / model / impl(provider_*.py) を先頭行 ###META### JSON で必ず出力
- model 名は config/config.yaml（llm.<provider>.model）→ .env → 既定 の順で解決し、
  provider_* へ --model で明示的に渡すため、META と実行内容が確実に一致する
"""

from __future__ import annotations
import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# ---- import path 調整（services/llm を import 対象に）----
LLM_DIR = Path(__file__).resolve().parent
if str(LLM_DIR) not in sys.path:
    sys.path.insert(0, str(LLM_DIR))

# プロジェクトルート: ~/work/NeuroHub
PROJECT_ROOT = LLM_DIR.parents[2]

from llm_common import (
    load_env_from_config,
    load_config,
    get_llm_model_from_config,
    print_environment_status,
    DebugLogger
)


# ========== ヘルパ ==========
def resolve_model(provider: str) -> str:
    """
    実際に使うモデル名を決定（YAML > .env > デフォルト）
    """
    cfg = load_config()  # config/config.yaml
    if provider == "ollama":
        yaml_model = get_llm_model_from_config(cfg, "ollama", "")
        env_model = os.getenv("OLLAMA_MODEL") or os.getenv("OLLAMA_TEST_MODEL", "")
        return yaml_model or env_model or "qwen2.5:1.5b-instruct"
    if provider == "huggingface":
        yaml_model = get_llm_model_from_config(cfg, "huggingface", "")
        env_model = os.getenv("HF_MODEL") or os.getenv("HF_TEST_MODEL", "")
        return yaml_model or env_model or "openai/gpt-oss-20b:groq"
    if provider == "gemini":
        yaml_model = get_llm_model_from_config(cfg, "gemini", "")
        env_model = os.getenv("GEMINI_MODEL") or os.getenv("GEMINI_TEST_MODEL", "")
        return yaml_model or env_model or "gemini-2.5-flash"
    return "unknown-model"


def strip_leading_meta(text: str) -> str:
    """
    provider_* 側が独自に ###META### 行を出していても、
    本 CLI で標準化した META を先頭に 1 行だけ出す方針のため、
    先頭の META 行は除去しておく。
    """
    if not text:
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("###META### "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def run_provider(provider: str, prompt: str) -> tuple[int, str, dict]:
    """
    対応 provider を呼び出し、(rc, stdout/stderr, meta) を返す。
    meta は {provider, model, impl} を必ず含む。
    """
    impl_map = {
        "huggingface": LLM_DIR / "provider_huggingface.py",
        "ollama":      LLM_DIR / "provider_ollama.py",
        "gemini":      LLM_DIR / "provider_gemini.py",
    }
    impl = impl_map.get(provider)
    if not impl or not impl.exists():
        return 1, f"[error] provider impl not found: {provider}", {}

    model = resolve_model(provider)

    # プロバイダをPythonモジュールとして実行（相対インポート対応）
    cwd = str(LLM_DIR.parent)  # services ディレクトリ
    module_name = f"llm.provider_{provider}"

    # プロバイダごとに引数形式を調整
    if provider == "ollama":
        cmd = [sys.executable, "-m", module_name, "--model", model, "--prompt", prompt]
    else:  # gemini, huggingface
        cmd = [sys.executable, "-m", module_name, "--model", model, prompt]

    # 環境変数を設定
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)
    meta = {"provider": provider, "model": model, "impl": impl.name}

    # 成功時は stdout、失敗時は stderr を返す（上位で判定する）
    out = p.stdout if p.returncode == 0 else p.stderr
    return p.returncode, out, meta


# ========== main ==========
def main() -> int:
    load_env_from_config()  # config/.env を反映

    ap = argparse.ArgumentParser(description="LLM CLI (smart fallback with accurate META)")
    ap.add_argument("prompt", nargs="+", help="ユーザープロンプト（スペース可）")
    ap.add_argument(
        "--smart",
        action="store_true",
        help="huggingface→ollama→gemini の順で自動フォールバック（LLM_SMART=1 でも有効）",
    )
    args = ap.parse_args()
    prompt = " ".join(args.prompt)

    # フォールバック順
    order = os.getenv("LLM_SMART_ORDER", "huggingface,ollama,gemini").split(",")
    order = [x.strip() for x in order if x.strip()]

    # スマート実行の有効性判定
    if not (args.smart or os.getenv("LLM_SMART", "1") == "1"):
        print("[error] no provider selected; try --smart", file=sys.stderr)
        return 1

    tried = []
    for name in order:
        # 軽い利用可否チェック（トークン類）
        if name == "huggingface" and not os.getenv("HF_TOKEN"):
            tried.append("huggingface:skip")
            continue
        if name == "gemini" and not os.getenv("GEMINI_API_KEY"):
            tried.append("gemini:skip")
            continue
        # ollama はプロセス死等も provider 側で失敗扱いに任せる

        rc, out, meta = run_provider(name, prompt)
        if rc == 0 and out and out.strip():
            # provider 側の先頭 META は除去して、本 CLI の META を 1 行だけ出す
            body = strip_leading_meta(out.strip())
            print("###META### " + json.dumps(meta, ensure_ascii=False))
            print(body)
            return 0
        tried.append(f"{name}:NG")

    print("[error] all providers failed: " + ", ".join(tried), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
