#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_prj_coding.py - Rebuilt clean version (llm_cli --system 未対応対応版)
- llm_cli.py に --system が無い環境でも動作するよう、system_text は user_text 先頭に埋め込みます。
"""

from __future__ import annotations
import argparse
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
LLM_CLI = ROOT / "services" / "llm" / "llm_cli.py"
PY = sys.executable

def abort(msg: str, code: int = 1) -> None:
    print(f"[error] {msg}", file=sys.stderr)
    sys.exit(code)

def run(cmd: list[str], *, cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)

def load_env_if_any() -> None:
    try:
        sys.path.insert(0, str(ROOT))
        from services.llm.llm_common import load_env_from_config
        load_env_from_config(debug=False)
    except Exception:
        pass

def read_many(paths: List[Path]) -> str:
    blocks: List[str] = []
    for p in paths:
        if p.exists():
            try:
                blocks.append(f"<<<BEGIN {p}>>>\n{p.read_text(encoding='utf-8', errors='replace')}\n<<<END {p}>>>")
            except Exception as e:
                blocks.append(f"<<<ERROR reading {p}: {e}>>>")
        else:
            blocks.append(f"<<<MISSING {p}>>>")
    return "\n\n".join(blocks)

def decide_project_name(spec: str) -> str:
    base = spec.strip().split()[0] if spec.strip() else "proj"
    base = base.lower().replace("/", "_").replace("\\", "_").replace(".", "-")
    if not base or base in {"--", "-"}:
        base = "proj"
    return base[:32]

# ---- LLM I/O (no --system; embed system text) ----
def call_llm(user_text: str, *, system_text: str = "", timeout: int = 240, print_raw: bool = False) -> str:
    if not LLM_CLI.exists():
        abort(f"missing LLM CLI: {LLM_CLI}")
    # Prepend system_text to user prompt to emulate system role
    if system_text:
        combined = f"[SYSTEM]\n{system_text}\n\n[USER]\n{user_text}"
    else:
        combined = user_text
    cmd = [PY, str(LLM_CLI), "--smart", combined]
    p = run(cmd, cwd=ROOT, timeout=timeout)
    if p.returncode != 0:
        abort(f"LLM failed rc={p.returncode}\n{p.stderr}")
    if print_raw:
        print("----- LLM RAW BEGIN -----")
        print(p.stdout.rstrip())
        print("----- LLM RAW END -----")
    return p.stdout

FENCE_RE = re.compile(r"```(?:python)?\s*(?P<body>[\s\S]*?)```", re.IGNORECASE)

def extract_python(text: str) -> str:
    m = FENCE_RE.search(text)
    if m:
        return m.group("body").strip()
    lines = text.splitlines()
    kept: List[str] = []
    seen_code = False
    for ln in lines:
        if not seen_code and (ln.strip().startswith("#!") or "def " in ln or "print(" in ln or "import " in ln):
            seen_code = True
        if seen_code:
            kept.append(ln.rstrip())
    return ("\n".join(kept) if kept else text).strip()

SYS_PROMPT = (
    "あなたは熟練のソフトウェアエンジニアです。"
    "出力は実行可能な最小のPythonスクリプトを返してください。"
)

PROMPT_DESIGN = """次の仕様に基づき、最小の仕様書(README抜粋)を日本語Markdownで作成してください。
要件/入出力/使い方/今後の拡張の節を含めてください。説明は簡潔でOK。
[仕様]
{spec}

[参照コンテキスト]
{ctx}
"""

PROMPT_CODE = """次の仕様書に基づき、単一ファイルのPythonスクリプト(main.py)を作成してください。
- 余計な説明は不要です。コードのみを ```python ～ ``` のフェンスで返してください。
- 実行例: `python main.py` で動くこと。
[仕様書]
{design}
"""

PROMPT_FIX = """この Python コードは実行時に失敗しました。原因を修正した完全なコードを返してください。
コードのみを ```python ～ ``` のフェンスで返してください。
[前回コード]
{code}

[実行ログ]
{log}
"""

def main() -> int:
    ap = argparse.ArgumentParser(description="NeuroHub: LLM-assisted mini project generator (no --system)")
    ap.add_argument("spec", nargs="?", help="仕様（第1引数）。未指定なら --spec/--spec-file を使用")
    ap.add_argument("--spec", dest="spec_opt", help="仕様文字列を追加指定")
    ap.add_argument("-S", "--spec-file", action="append", help="仕様ファイル(複数可)")
    ap.add_argument("-F", "--file", action="append", help="参照コンテキストファイル(複数可)")
    ap.add_argument("--project", help="プロジェクト名（既定は仕様から自動推定）")
    ap.add_argument("--max-iters", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--print-raw", action="store_true")
    args = ap.parse_args()

    load_env_if_any()

    spec_parts: List[str] = []
    if args.spec:
        spec_parts.append(args.spec.strip())
    if args.spec_opt:
        spec_parts.append(args.spec_opt.strip())
    if args.spec_file:
        for p in args.spec_file:
            pp = (ROOT / p).resolve()
            try:
                spec_parts.append(pp.read_text(encoding="utf-8", errors="replace"))
            except Exception as e:
                spec_parts.append(f"<<ERROR reading {pp}: {e}>>")
    spec_text = "\n\n".join([s for s in spec_parts if s]).strip()
    if not spec_text:
        abort("仕様が空です。第1引数、--spec、または --spec-file を使ってください。")

    ctx_text = ""
    if args.file:
        files = [(ROOT / p).resolve() for p in args.file]
        ctx_text = read_many(files)

    project_name = args.project or decide_project_name(spec_text)
    proj_dir = (ROOT / "projects" / project_name).resolve()
    proj_dir.mkdir(parents=True, exist_ok=True)

    # 1) 設計
    design = call_llm(PROMPT_DESIGN.format(spec=spec_text, ctx=ctx_text), system_text=SYS_PROMPT, timeout=args.timeout, print_raw=args.print_raw)
    (proj_dir / "README.md").write_text(design, encoding="utf-8")

    # 2) 実装→実行→修正
    for i in range(1, args.max_iters + 1):
        pass

        raw = call_llm(PROMPT_CODE.format(design=design), system_text=SYS_PROMPT, timeout=args.timeout, print_raw=args.print_raw)
        code = extract_python(raw)
        (proj_dir / "main.py").write_text(code, encoding="utf-8")

        p = run([PY, "main.py"], cwd=proj_dir, timeout=60)
        print(p.stdout, end="")
        if p.returncode == 0:
            print(f"[run] OK (iter {i})")
            break

        log = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        raw = call_llm(PROMPT_FIX.format(code=code, log=log), system_text=SYS_PROMPT, timeout=args.timeout, print_raw=args.print_raw)
        code = extract_python(raw)
        (proj_dir / "main.py").write_text(code, encoding="utf-8")
    else:
        abort("最大リトライ回数に達しました。修正に失敗しました。", code=2)

    print(f"[完成] projects/{project_name}\n\n使い方:\n  cd projects/{project_name}\n  {Path(PY).name} main.py")
    return 0

if __name__ == "__main__":
    sys.exit(main())
