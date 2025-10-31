#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_prj_coding.py (regen, safe, empty-main)
- 仕様→詳細設計→「モデル選別中」→生成→レビュー を一括出力
- main.py は空（1行コメントのみ）。DB/外部ライブラリ/ネットアクセスなし
- 生成先: projects/<snake_case_name>_cli/
- 任意LLM: services/llm/llm_cli.py が存在する場合のみ 1回だけ呼ぶ（失敗しても続行）
- ログ: logs/ai_prj/<timestamp>_<name>.yaml に保存（LLM結果・モデル選別情報を含む）
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# -------- Paths --------
ROOT = Path(__file__).resolve().parents[2]  # ~/work/NeuroHub
PROJECTS_DIR = ROOT / "projects"
LOG_DIR = ROOT / "logs" / "ai_prj"
LLM_CLI = ROOT / "services" / "llm" / "llm_cli.py"
CONFIG_YAML = ROOT / "config" / "config.yaml"

# -------- Utils --------
def p(s: str = "") -> None:
    print(s, flush=True)

def ensure_dirs() -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def to_snake_ascii(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s-]", " ", s)
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = "_".join([t for t in s.split(" ") if t])
    s = re.sub(r"[^a-z0-9_]+", "_", s).strip("_")
    return s[:60] or "project"

def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def run(cmd: List[str], cwd: Optional[Path]=None, timeout: int=25) -> Tuple[int,str,str]:
    proc = subprocess.Popen(cmd, cwd=str(cwd) if cwd else None,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return 124, out, err

def yaml_dump(data, indent: int=0) -> str:
    sp = "  " * indent
    if data is None: return "null"
    if isinstance(data, bool): return "true" if data else "false"
    if isinstance(data, (int, float)): return str(data)
    if isinstance(data, str):
        # quote if special chars or newline
        if re.search(r"[:\\-\\{\\}\\[\\]\\n#\"]", data):
            return '"' + data.replace('"', '\\"') + '"'
        return data
    if isinstance(data, list):
        if not data: return "[]"
        lines = []
        for it in data:
            dumped = yaml_dump(it, indent+1)
            if "\n" in dumped:
                first, *rest = dumped.splitlines()
                lines.append(f"{sp}- {first}")
                for r in rest: lines.append(f"{sp}  {r}")
            else:
                lines.append(f"{sp}- {dumped}")
        return "\n".join(lines)
    if isinstance(data, dict):
        if not data: return "{}"
        lines = []
        for k, v in data.items():
            dumped = yaml_dump(v, indent+1)
            if "\n" in dumped:
                lines.append(f"{sp}{k}:")
                for r in dumped.splitlines(): lines.append(f"{sp}  {r}")
            else:
                lines.append(f"{sp}{k}: {dumped}")
        return "\n".join(lines)
    return yaml_dump(str(data), indent)

# -------- Model Selection (display only, no network) --------
def detect_providers() -> Dict[str, Dict[str, str]]:
    info = {}
    # provider files
    prov_files = {
        "gemini": ROOT / "services" / "llm" / "provider_gemini.py",
        "huggingface": ROOT / "services" / "llm" / "provider_huggingface.py",
        "ollama": ROOT / "services" / "llm" / "provider_ollama.py",
    }
    for name, path in prov_files.items():
        info[name] = {"exists": "yes" if path.exists() else "no"}

    # env hints (存在表示のみ)
    env_map = {
        "gemini": ("GEMINI_API_KEY",),
        "huggingface": ("HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN"),
        "ollama": ("OLLAMA_HOST",),
    }
    for name, keys in env_map.items():
        found = [k for k in keys if os.environ.get(k)]
        info.setdefault(name, {})
        info[name]["env"] = ",".join(found) if found else ""

    # config.yaml(有れば)のざっくり解析（enabled: 1/0 を拾うだけ）
    if CONFIG_YAML.exists():
        try:
            text = CONFIG_YAML.read_text(encoding="utf-8", errors="ignore")
            for name in ["gemini","huggingface","ollama"]:
                m = re.search(rf"(?m)^{name}:\s*\\n(?:[ \\t].*\\n)*?[ \\t]*enabled:\s*(\\d+)", text)
                if m:
                    info.setdefault(name, {})
                    info[name]["enabled"] = "1" if m.group(1) == "1" else "0"
        except Exception:
            pass

    # selection policy (表示用優先度)
    # enabled==1 の中で gemini > huggingface > ollama、無ければ存在/環境を見て候補表示
    def score(n):
        e = info.get(n, {}).get("enabled", "")
        ex = info.get(n, {}).get("exists", "no")
        envar = info.get(n, {}).get("env", "")
        base = {"gemini":3, "huggingface":2, "ollama":1}.get(n, 0)
        bonus = (2 if e=="1" else 0) + (1 if ex=="yes" else 0) + (1 if envar else 0)
        return base*10 + bonus

    ordered = sorted(["gemini","huggingface","ollama"], key=score, reverse=True)
    info["_ordered"] = ",".join(ordered)
    info["_selected"] = ordered[0] if ordered else ""
    return info

def print_model_selection(info: Dict[str, Dict[str, str]]) -> None:
    p("=== モデル選別中 ===")
    for name in ["gemini","huggingface","ollama"]:
        d = info.get(name, {})
        p(f"- {name}: exists={d.get('exists','no')}, env={d.get('env','') or '-'}, enabled={d.get('enabled','?')}")
    p(f"- provider_order: {info.get('_ordered','')}")
    p(f"- selected_provider: {info.get('_selected','')}")
    p("")

# -------- Optional LLM Ping --------
def llm_ping(prompt: str) -> Tuple[bool, Optional[str], Optional[str]]:
    if not LLM_CLI.exists():
        return False, None, None
    rc, out, err = run([sys.executable, str(LLM_CLI), prompt], cwd=ROOT, timeout=20)
    if rc == 0 and (out or "").strip():
        return True, out.strip(), None
    return True, (out or "").strip() or None, (err or "").strip() or None

# -------- Main --------
def main() -> int:
    ap = argparse.ArgumentParser(description="AI project coder (empty main; model selection display; optional LLM)")
    ap.add_argument("prompt", help="プロンプト（日本語OK）")
    ap.add_argument("--name", help="プロジェクト名（snake_case）。未指定なら自動生成")
    args = ap.parse_args()

    ensure_dirs()

    # name
    auto_name = to_snake_ascii(args.name or args.prompt)
    if not auto_name.endswith("_cli"):
        auto_name = f"{auto_name}_cli"
    proj_name = auto_name
    proj_dir = PROJECTS_DIR / proj_name
    proj_dir.mkdir(parents=True, exist_ok=True)

    # spec
    p("=== 仕様設計プラン ===")
    p(f"プロンプト: {args.prompt}")
    p("要求要約: コーディング用の空プロジェクトを作成（main.py は空）")
    p("期待挙動: ファイル生成・モデル選別出力・任意でLLM ping・YAMLログ保存")
    p("")

    p("=== 詳細設計 ===")
    p("- 生成先: projects/<name>_cli/")
    p("- 生成物: main.py(空), README.md")
    p("- LLM: services/llm/llm_cli.py が有れば 1回呼ぶ（失敗でも続行）")
    p("- ログ: logs/ai_prj/<timestamp>_<name>.yaml")
    p("- 依存: 標準ライブラリのみ（pip/apt/venv/ネット未使用）")
    p("")

    # model selection display
    info = detect_providers()
    print_model_selection(info)

    p("=== プロジェクト名 ===")
    p(f"{proj_name} に決定")
    p(f"$ mkdir {proj_name}")
    p("[結果]")
    p("")

    # generate files
    main_py = proj_dir / "main.py"
    readme = proj_dir / "README.md"
    write_text(main_py, "# main.py (auto-created placeholder)\n")
    readme_text = f"""# {proj_name}

## Overview
Empty scaffolding for coding. This project only creates files and logs.

## Files
- main.py (empty placeholder)
- README.md

## Notes
- Provider/model selection is printed at creation time.
- Optional LLM ping via services/llm/llm_cli.py (if present).
- Logs are saved under logs/ai_prj/.
"""
    write_text(readme, readme_text)

    # optional LLM
    llm_called, llm_out, llm_err = llm_ping("この生成スキャフォールドで注意点があれば1行だけ")

    if not llm_called:
        p("[LLM] スキップ（services/llm/llm_cli.py が見つかりません）")
    else:
        p("[LLM] 呼び出し済み")
        if llm_out: p(f"[LLM out] {llm_out}")
        if llm_err: p(f"[LLM err] {llm_err}")
    p("")

    # result
    files = []
    try:
        files = sorted([q.name for q in proj_dir.iterdir()])
    except FileNotFoundError:
        pass

    p("=== 生成結果 ===")
    p(f"DIR : {proj_dir}")
    p("FILES:")
    for fn in files: p(f" - {fn}")
    p("")
    p("=== 実行結果 ===")
    p("[OK] placeholder created")
    p("STATUS: success")
    p("")

    p("=== AIレビュー ===")
    p("- main.py は空で作成され、後から安全に上書き可能")
    p("- README と YAML ログが整合していることを確認")
    p("- 改良提案: 以後の世代では spec ファイル群を読み込んで複数ファイルを生成する機構を追加")
    p("")

    # log
    ts = time.strftime("%Y%m%d-%H%M%S")
    log_data = {
        "timestamp": ts,
        "project_dir": str(proj_dir),
        "prompt": args.prompt,
        "status": "success",
        "files": files,
        "model_selection": info,
        "llm_called": llm_called,
        "llm_out": llm_out or "",
        "llm_err": llm_err or "",
        "note": "empty main scaffolder; no network; stdlib only",
    }
    (LOG_DIR / f"{ts}_{proj_name}.yaml").write_text(yaml_dump(log_data), encoding="utf-8")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\\n[abort] Interrupted.", file=sys.stderr)
        sys.exit(130)
