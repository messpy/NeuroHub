#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_agent.py
- URLからHTML取得 → BeautifulSoupで要約 → LLMに投げて回答
- 今は最小構成。後でMCP／追加ステップを差し込みやすい構造。

Usage:
  python services/agent/web_agent.py https://example.com "このページを3行で要約して"
  python services/agent/web_agent.py https://example.com "このページからダウンロード手順を箇条書きで"

オプション:
  --model MODEL     : LLMモデルのヒント（provider側に渡す）
  --provider {gemini,ollama,hf} : 利用プロバイダ
  --timeout SEC     : ネットワークタイムアウト（fetch）
  --pretty          : 出力を整形
"""
from __future__ import annotations
import argparse, json, sys, textwrap
from typing import Any, Dict, Optional

# 1) Web取得・解析
from tools.bs_core import fetch_html, soupify, extract_standard

# 2) LLM呼び出し：あなたの既存LLM層を薄く叩く
#   - 既存の llm_cli.py をサブプロセスで叩いてもOKだが、まずは関数化前提の薄い適配を作る。
#   - ここでは provider_* を直接使わず、llm_common などに "run_text(model, prompt)" 的な関数がある想定で一例実装。
try:
    from services.llm.llm_common import run_text  # あなたの実装に合わせて調整
except Exception:
    # フォールバック: llm_cli.py をCLIで呼ぶ場合の簡易関数
    import subprocess, shlex
    def run_text(prompt: str, model: Optional[str] = None, provider: Optional[str] = None) -> str:
        # 例: --smart で最良経路、もしくは --provider/--model を受け付けるあなたのCLIに合わせて修正
        cmd = ["python", "services/llm/llm_cli.py", "--smart", prompt]
        if model:    cmd.extend(["--model", model])
        if provider: cmd.extend(["--provider", provider])
        try:
            out = subprocess.check_output(cmd, text=True)
            return out.strip()
        except subprocess.CalledProcessError as e:
            return f"[LLM error] {e.output.strip() if e.output else e}"

PROMPT_TEMPLATE = """あなたはWebページの要約と質問回答を行うアシスタントです。
次のページのメタ情報と本文サマリを読み、ユーザーの質問に答えてください。
必要なら根拠となる抜粋も示してください。箇条書きは簡潔に。

[ページ情報]
title: {title}
description: {description}
canonical: {canonical}
sample_text: {sample_text}

[質問]
{question}
"""

def main() -> int:
    ap = argparse.ArgumentParser(description="Web→AI 統合エージェント")
    ap.add_argument("url", help="解析するURL")
    ap.add_argument("question", help="AIへの質問（日本語OK）")
    ap.add_argument("--model", help="モデル名（任意）")
    ap.add_argument("--provider", choices=["gemini","ollama","hf"], help="LLMプロバイダ（任意）")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    try:
        html = fetch_html(args.url, timeout=args.timeout)
        soup = soupify(html)
        std = extract_standard(soup)

        prompt = PROMPT_TEMPLATE.format(
            title=std.get("title") or "",
            description=std.get("description") or "",
            canonical=std.get("canonical") or args.url,
            sample_text=std.get("sample_text") or "",
            question=args.question.strip(),
        )

        answer = run_text(prompt, model=args.model, provider=args.provider)

        result: Dict[str, Any] = {
            "url": args.url,
            "title": std.get("title"),
            "canonical": std.get("canonical"),
            "qa": {
                "question": args.question,
                "answer": answer,
            },
        }
        if args.pretty:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False))
        return 0

    except Exception as e:
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
