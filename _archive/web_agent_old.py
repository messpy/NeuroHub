#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
web_agent.py
- URLからHTML取得 → BeautifulSoupで要約 → LLMに投げて回答
- 出力は YAML を標準出力（デフォルト）
- --output 指定時のみ、意味のある自動ファイル名で保存
  例: booth_7414326_hollow_20251029.yaml（重複時 _001, _002 ...）

Usage:
  # 任意質問（--prompt を推奨）
  python services/agent/web_agent.py https://example.com --prompt "このページを3行で要約"

  # 後方互換（位置引数 question も可）
  python services/agent/web_agent.py https://example.com "ダウンロード手順を箇条書きで"

  # ファイル保存（自動命名）
  python services/agent/web_agent.py https://booth.pm/ja/items/7414326 --prompt "これいくら？" --output
"""

import argparse, sys, pathlib, subprocess, re, glob
from typing import Any, Dict, Optional
from datetime import datetime
import unicodedata

# === プロジェクトルート導入 ===
ROOT = pathlib.Path(__file__).resolve().parents[2]  # .../NeuroHub
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# === Web取得・解析 ===
from tools.bs_core import fetch_html, soupify, extract_standard  # type: ignore

# === LLM呼び出し（共通関数 or CLI フォールバック） ===
try:
    from services.llm.llm_common import run_text  # プロジェクト実装に合わせる
except Exception:
    def run_text(prompt: str, model: Optional[str] = None, provider: Optional[str] = None) -> str:
        cmd = ["python", "services/llm/llm_cli.py", "--smart", prompt]
        if model:    cmd.extend(["--model", model])
        if provider: cmd.extend(["--provider", provider])
        try:
            out = subprocess.check_output(cmd, text=True)
            return out.strip()
        except subprocess.CalledProcessError as e:
            return f"[LLM error] {e.output.strip() if e.output else e}"

# === YAML 出力 ===
try:
    import yaml  # PyYAML
except Exception:
    print("[error] PyYAML が必要です: pip install pyyaml", file=sys.stderr)
    raise

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

def _slugify(text: str, limit: int = 20) -> str:
    # 日本語はローマ字化しない方針：記号除去・スペース/ハイフン→アンダースコア
    t = unicodedata.normalize("NFKD", text)
    t = re.sub(r"[^\w\s-]", "", t)          # 記号除去（全角英数はNFKDで分解後に\wに入る想定）
    t = re.sub(r"[-\s]+", "_", t).strip("_")
    t = t.lower()
    return (t[:limit] if t else "page")

def _host_key(url: str) -> str:
    # https?:// を剥がしてホスト先頭ラベルのみ（例: booth.pm -> booth）
    host = re.sub(r"^https?://", "", url).split("/")[0]
    return host.split(".")[0] if host else "site"

def _id_from_url(url: str) -> str:
    # 末尾セグメントから数字優先抽出（例: /items/7414326 -> 7414326）
    seg = url.rstrip("/").split("/")[-1]
    num = re.sub(r"\D", "", seg)
    return num if num else (seg or "x")

def _autoname(url: str, title: Optional[str]) -> str:
    host = _host_key(url)
    id_part = _id_from_url(url)
    title_slug = _slugify(title or "page", limit=20)
    date_str = datetime.now().strftime("%Y%m%d")
    base = f"{host}_{id_part}_{title_slug}_{date_str}"

    # 重複回避の連番付与
    if not pathlib.Path(f"{base}.yaml").exists():
        return f"{base}.yaml"
    suffix = 1
    while True:
        cand = f"{base}_{suffix:03d}.yaml"
        if not pathlib.Path(cand).exists():
            return cand
        suffix += 1

def main() -> int:
    ap = argparse.ArgumentParser(description="Web→AI 統合エージェント (YAML出力)")
    ap.add_argument("url", help="解析するURL")
    ap.add_argument("question", nargs="?", help="AIへの質問（未指定なら --prompt を使う）")
    ap.add_argument("--prompt", help="任意質問テキスト（指定時は question より優先）")
    ap.add_argument("--model", help="モデル名（任意）")
    ap.add_argument("--provider", choices=["gemini","ollama","hf"], help="LLMプロバイダ（任意）")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--output", action="store_true", help="結果を意味のある自動名で保存（デフォルトは保存しない）")
    args = ap.parse_args()

    # 質問テキストの決定
    qtext: Optional[str] = args.prompt.strip() if args.prompt else (args.question.strip() if args.question else None)
    if not qtext:
        print("[error] 質問がありません。--prompt か position引数で質問を指定してください。", file=sys.stderr)
        return 2

    try:
        html = fetch_html(args.url, timeout=args.timeout)
        soup = soupify(html)
        std = extract_standard(soup) or {}

        prompt = PROMPT_TEMPLATE.format(
            title=std.get("title") or "",
            description=std.get("description") or "",
            canonical=std.get("canonical") or args.url,
            sample_text=std.get("sample_text") or "",
            question=qtext,
        )

        answer = run_text(prompt, model=args.model, provider=args.provider)

        data: Dict[str, Any] = {
            "url": args.url,
            "title": std.get("title"),
            "canonical": std.get("canonical") or args.url,
            "qa": {
                "question": qtext,
                "answer": answer,
            },
        }

        # YAML を標準出力（デフォルト）
        sys.stdout.write(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))

        # --output 指定時のみファイル保存
        if args.output:
            fname = _autoname(args.url, std.get("title"))
            pathlib.Path(fname).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            print(f"# saved: {fname}", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
