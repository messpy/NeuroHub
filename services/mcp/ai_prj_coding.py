#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_prj_coding.py
- LLMに仕様/コード生成を依頼し、プロジェクトを作成→実行→自動修正（最大5回）
- cmd_exec を優先実行に利用（なければ直接実行）
- 仕様プリントは日本語。READMEは日本語。

今回の修正点（ユーザー要望）
- プロジェクト名/フォルダは LLM から英語 snake_case を生成（fallbackあり）。固定名は廃止
- 作成ファイルは作成時に逐次ファイル名をプリント
- [RUN] コマンドの結果は 10 行以内に要約。超えたら末尾に「...」
- セットアップは実行と同じブロックに統合（README, 終了時のコマンド表示）
- 実行例セクションは削除
- 生成ファイル一覧はファイル名のみ（サイズ非表示）
- 成功時は README より先に「最終結果コマンド（コピペ可）」を表示
- 一発実行（絶対パスの venv python）は廃止
"""
from __future__ import annotations
import argparse
import os
import re
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, List

ROOT = Path(__file__).resolve().parents[2]  # ~/work/NeuroHub
PROJECTS_DIR = ROOT / "projects"
LOG_DIR = ROOT / "logs" / "ai_prj"
CMD_EXEC = ROOT / "services" / "mcp" / "cmd_exec.py"
LLM_CLI = ROOT / "services" / "llm" / "llm_cli.py"

MAX_RETRIES = 5

def print_flush(*a, **kw):
    print(*a, **kw); sys.stdout.flush()

def run_cmd(args: List[str], cwd: Optional[Path] = None, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    proc = subprocess.Popen(args, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return 124, out, err
    return proc.returncode, out, err

def run_via_cmd_exec(command: str, cwd: Path) -> Tuple[int, str, str]:
    if CMD_EXEC.exists():
        return run_cmd([sys.executable, str(CMD_EXEC), command], cwd=ROOT)
    return run_cmd(['/bin/bash','-lc', f'cd "{cwd}" && {command}'], cwd=ROOT)

def trim_lines(s: str, limit: int = 10) -> str:
    if not s: return ""
    lines = s.strip().splitlines()
    return "\n".join(lines[:limit]) + ("\n..." if len(lines) > limit else "")

def ensure_dirs():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True); LOG_DIR.mkdir(parents=True, exist_ok=True)

def detect_python() -> str:
    return shutil.which("python3") or sys.executable

def to_snake_ascii(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", " ", s, flags=re.U)
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    s = "_".join(filter(None, s.split(" ")))
    s = re.sub(r"[^a-z0-9_]+", "_", s).strip("_")
    return s[:60] or "project"

def prompt_project_name(prompt: str) -> str:
    if LLM_CLI.exists():
        ask = ("Generate a short English project name in snake_case (letters, numbers, underscores only). "
               "No spaces, no hyphens, no punctuation. 3-6 words max. Only output the name.\n"
               f"Spec: {prompt}")
        rc, out, err = run_cmd([sys.executable, str(LLM_CLI), ask], cwd=ROOT, timeout=40)
        if rc == 0:
            name = to_snake_ascii(out.strip().splitlines()[-1].strip())
            if name: return name
    return to_snake_ascii(prompt)

def build_readme_ja(name: str, proj_dir: Path, req_summary: str) -> str:
    return f"""# {name}

## 概要
{req_summary}

## 使い方（セットアップ込み）
```bash
$ cd {proj_dir}
$ python3 -m venv .venv
$ . .venv/bin/activate
$ python -m pip install --upgrade pip
$ python3 main.py
```
"""

def save_report(name: str, report: dict) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = LOG_DIR / f"{ts}_{name}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print_flush(f"[create] {path}")

def ensure_venv(proj_dir: Path) -> Path:
    py = detect_python()
    venv = proj_dir / ".venv"
    if not (venv / "bin" / "python").exists():
        rc, out, err = run_cmd([py, "-m", "venv", ".venv"], cwd=proj_dir)
        print_flush(f"[RUN] python3 -m venv .venv")
        print_flush(trim_lines(out or err, 10))
    return venv / "bin" / "python"

def gen_initial_code(prompt: str) -> str:
    if LLM_CLI.exists():
        ask = (
            "Write a single-file Python script named main.py to satisfy the following spec.\n"
            "Rules:\n- Must be Python 3.12 compatible\n- Include argparse --help\n- No sudo/apt\n"
            "- If external packages are needed, import and handle missing gracefully with a message\n"
            f"Spec (Japanese): {prompt}\nOutput only the code for main.py."
        )
        rc, out, err = run_cmd([sys.executable, str(LLM_CLI), ask], cwd=ROOT, timeout=60)
        if rc == 0 and out.strip(): return out.strip()
    return """#!/usr/bin/env python3
import argparse, sqlite3, socket, datetime
def main():
    ap = argparse.ArgumentParser(description="generated script")
    ap.add_argument("--db", default="results.db")
    args = ap.parse_args()
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ip = socket.gethostbyname(socket.gethostname())
    con=sqlite3.connect(args.db); cur=con.cursor()
    cur.execute("create table if not exists results(ts text, ip text)")
    cur.execute("insert into results values(?,?)",(ts,ip))
    con.commit(); con.close()
    print("Timestamp:", ts); print("IP Address(es):", ip)
if __name__=="__main__": main()
"""

def auto_fix_with_llm(prompt: str, prev_stdout: str, prev_stderr: str, files_snapshot: List[str]) -> Optional[str]:
    if not LLM_CLI.exists(): return None
    ask = (
        "Previous run failed or had issues. Fix main.py and return ONLY the corrected full content.\n"
        f"Spec (Japanese): {prompt}\nstdout (tail):\n{prev_stdout[-2000:]}\n\nstderr (tail):\n{prev_stderr[-2000:]}\n"
        f"Existing files: {files_snapshot}\nConstraints:\n- Python 3.12\n- argparse --help\n- No sudo/apt\n"
    )
    rc, out, err = run_cmd([sys.executable, str(LLM_CLI), ask], cwd=ROOT, timeout=60)
    if rc == 0 and out.strip(): return out.strip()
    return None

def detect_help_output(proj_dir: Path) -> Optional[str]:
    vpy = proj_dir / ".venv" / "bin" / "python"
    if not vpy.exists(): return None
    rc, out, err = run_via_cmd_exec(f'./.venv/bin/python main.py --help', cwd=proj_dir)
    if rc == 0 and out.strip():
        return f"$ . .venv/bin/activate\n$ python3 main.py --help\n{trim_lines(out, 10)}"
    return None

def list_files(proj_dir: Path) -> List[str]:
    return [p.name + ("/" if p.is_dir() else "") for p in sorted(proj_dir.iterdir())]

def main() -> int:
    ap = argparse.ArgumentParser(description="AI project coder (NeuroHub)")
    ap.add_argument("prompt", help="作りたいもの（日本語OK）")
    ap.add_argument("-F", "--spec-file", action="append", default=[], help="仕様テキスト（複数可）")
    args = ap.parse_args()

    ensure_dirs()

    spec_texts = []
    for f in args.spec_file:
        try: spec_texts.append(Path(f).read_text(encoding="utf-8"))
        except Exception: pass
    req_summary = f"要求: {args.prompt}" + (("\n\n追加仕様:\n" + "\n---\n".join(spec_texts)) if spec_texts else "")

    print_flush("=== 要件定義（日本語） ==="); print_flush(req_summary)
    name = prompt_project_name(args.prompt)
    proj_dir = PROJECTS_DIR / name
    proj_dir.mkdir(parents=True, exist_ok=True)
    print_flush("\n=== プロジェクト名 ==="); print_flush(name)

    code = gen_initial_code(args.prompt)
    if not code.lstrip().startswith("#!"): code = "#!/usr/bin/env python3\n" + code
    write_file(proj_dir/"main.py", code)

    vpy = ensure_venv(proj_dir)

    last_out = ""; last_err = ""; rc = 1
    run_cmd_str = ". .venv/bin/activate; python3 main.py"
    for attempt in range(1, MAX_RETRIES+1):
        print_flush(f"\n[RUN] attempt {attempt}/{MAX_RETRIES}: {run_cmd_str}")
        rc, out, err = run_via_cmd_exec(run_cmd_str, cwd=proj_dir)
        last_out, last_err = out or "", err or ""
        print_flush(trim_lines(last_out if last_out.strip() else last_err, 10))
        if rc == 0: break
        print_flush("[auto-fix] LLM による再生成を行います。")
        fixed = auto_fix_with_llm(args.prompt, last_out, last_err, list_files(proj_dir))
        if fixed: write_file(proj_dir/"main.py", fixed)

    status = "ok" if rc == 0 else "failed"

    if status == "ok":
        print_flush("\n=== 最終結果コマンド（コピペ可） ===")
        print_flush(f"$ cd {proj_dir}")
        print_flush("$ . .venv/bin/activate")
        print_flush("$ python3 main.py")

    readme_text = build_readme_ja(name, proj_dir, req_summary)
    write_file(proj_dir/"README.md", readme_text)

    print_flush("\n=== 生成ファイル一覧 ===")
    print_flush(f"$ ls -la {proj_dir}")
    for n in list_files(proj_dir): print_flush(f" - {n}")

    print_flush("\n=== 最終テスト結果（要約） ===")
    print_flush(f"RC: {rc}")
    if last_out.strip(): print_flush("---- STDOUT (<=10 lines) ----"); print_flush(trim_lines(last_out, 10))
    if last_err.strip(): print_flush("---- STDERR (<=10 lines) ----"); print_flush(trim_lines(last_err, 10))

    print_flush("\n=== README.md ===")
    print_flush((proj_dir/"README.md").read_text(encoding="utf-8"))

    report = {
        "project_dir": str(proj_dir),
        "run_cmd": run_cmd_str,
        "rc": rc,
        "stdout": last_out,
        "stderr": last_err,
        "venv_python": str(vpy),
        "base_python": sys.executable,
        "status": status,
    }
    path = save_report(name, report)
    print_flush(f"\n[完成] {proj_dir}")
    print_flush("使い方:")
    print_flush(f"  $ cd {proj_dir}")
    print_flush("  $ . .venv/bin/activate")
    print_flush("  $ python3 main.py")
    print_flush(f"\nReport: {path}")
    return 0 if status == "ok" else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[abort] Interrupted.", file=sys.stderr); sys.exit(130)
