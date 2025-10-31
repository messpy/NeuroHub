#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_test.py
- 設計YAMLの tests を順番に実行（実行もテスターの責務）
- 出力/エラー収集 + keywords/regex 照合
"""
from __future__ import annotations
import argparse, re, sys, time, shlex

# ---- tiny helpers (no external deps) ----
import os, re, sys, time, subprocess, shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

ROOT = Path(__file__).resolve().parents[2]  # .../NeuroHub
PROJECTS_DIR = ROOT / "projects"
LOG_DIR = ROOT / "logs" / "ai_prj"
LLM_CLI = ROOT / "services" / "llm" / "llm_cli.py"
CONFIG_YAML = ROOT / "config" / "config.yaml"

def p(*a): print(*a, flush=True)

def ensure_dirs():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def to_snake(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"[-\s]+", "_", s).strip("_")
    return s or "project"

def ts_now() -> str:
    return time.strftime("%Y%m%d-%H%M%S")

def yaml_dump(data, indent=0):
    sp = "  " * indent
    if data is None: return "null"
    if isinstance(data, bool): return "true" if data else "false"
    if isinstance(data, (int, float)): return str(data)
    if isinstance(data, str):
        if re.search(r'[:{}\[\]\n"#]', data):
            return '"' + data.replace('"','\\"') + '"'
        return data
    if isinstance(data, list):
        if not data: return "[]"
        out = []
        for it in data:
            y = yaml_dump(it, indent+1)
            if "\n" in y:
                a,*rs = y.splitlines()
                out.append(f"{sp}- {a}")
                out.extend(f"{sp}  {r}" for r in rs)
            else:
                out.append(f"{sp}- {y}")
        return "\n".join(out)
    if isinstance(data, dict):
        if not data: return "{}"
        out = []
        for k,v in data.items():
            y = yaml_dump(v, indent+1)
            if "\n" in y:
                out.append(f"{sp}{k}:")
                out.extend(f"{sp}  {r}" for r in y.splitlines())
            else:
                out.append(f"{sp}{k}: {y}")
        return "\n".join(out)
    return yaml_dump(str(data), indent)

def yaml_load(text: str):
    try:
        import yaml as _pyyaml  # type: ignore
        return _pyyaml.safe_load(text)
    except Exception:
        pass
    # minimal loader
    data_stack = [{}]
    indent_stack = [0]
    current = data_stack[0]
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise ValueError("Invalid indent")
        while indent_stack and indent < indent_stack[-1]:
            data_stack.pop(); indent_stack.pop(); current = data_stack[-1]
        if line.lstrip().startswith("- "):
            if "__list__" not in current:
                current["__list__"] = []
            item = line.strip()[2:]
            if item.endswith(":"):
                newd = {}
                current["__list__"].append(newd)
                data_stack.append(newd); indent_stack.append(indent+2); current = newd
            else:
                current["__list__"].append(_parse_scalar(item))
        else:
            if ":" in line:
                k, v = line.strip().split(":", 1)
                v = v.strip()
                if v == "":
                    newd = {}
                    current[k] = newd
                    data_stack.append(newd); indent_stack.append(indent+2); current = newd
                else:
                    current[k] = _parse_scalar(v)
    def fix(obj):
        if isinstance(obj, dict):
            if list(obj.keys()) == ["__list__"]:
                return [fix(x) for x in obj["__list__"]]
            return {k: fix(v) for k,v in obj.items()}
        if isinstance(obj, list):
            return [fix(x) for x in obj]
        return obj
    return fix(data_stack[0])

def _parse_scalar(v: str):
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1].replace('\\"','"')
    if v in ("true","false"): return v=="true"
    try:
        if "." in v: return float(v)
        return int(v)
    except Exception:
        return v

def run(cmd: List[str], cwd: Optional[Path]=None, timeout: int=180) -> Tuple[int,str,str]:
    proc = subprocess.Popen(cmd, cwd=str(cwd) if cwd else None,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return 124, out, err

def strip_code_fences(s: str) -> str:
    m = re.search(r"```[a-zA-Z0-9]*\s*(.*?)```", s, flags=re.S)
    if m: return m.group(1).strip()
    return s.strip()

def probe_models() -> Dict[str, str]:
    """Return dict with keys: selected, ordered, detail (multiline). Requires llm_cli.py"""
    detail = []
    if not LLM_CLI.exists():
        return {"selected":"", "ordered":"", "detail":"llm_cli.py not found"}
    providers = ["gemini","huggingface","ollama"]
    # read enabled flags from config.yaml (best-effort)
    enabled = {p:"?" for p in providers}
    if CONFIG_YAML.exists():
        try:
            text = CONFIG_YAML.read_text(encoding="utf-8", errors="ignore")
            for name in providers:
                m = re.search(rf"(?m)^{name}:\s*\n(?:[ \t].*\n)*?[ \t]*enabled:\s*(\d+)", text)
                if m: enabled[name] = "1" if m.group(1)=="1" else "0"
        except Exception: pass
    # env
    envmap = {"gemini":["GEMINI_API_KEY"], "huggingface":["HF_TOKEN","HUGGINGFACEHUB_API_TOKEN"], "ollama":["OLLAMA_HOST"]}
    scores = {}
    for pvd in providers:
        envs = [k for k in envmap[pvd] if os.environ.get(k)]
        detail.append(f"- {pvd}: enabled={enabled[pvd]} env={','.join(envs) if envs else ''}")
        base = {"gemini":3,"huggingface":2,"ollama":1}[pvd]
        scores[pvd] = base*10 + (2 if enabled[pvd]=="1" else 0) + (1 if envs else 0)
    ordered = [k for k,_ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)]
    # quick ping using llm_cli
    ping_text = "Return exactly: PONG"
    selected = ""
    for name in ordered:
        rc, out, err = run([sys.executable, str(LLM_CLI), f"[{name}] " + ping_text], cwd=ROOT, timeout=25)
        ok = (rc==0 and ("PONG" in (out or "")))
        detail.append(f"  probe {name}: rc={rc} ok={ok}")
        if ok and not selected:
            selected = name
    return {
        "selected": selected,
        "ordered": ",".join(ordered),
        "detail": "\n".join(detail) if detail else "(no detail)",
    }

def require_llm_or_die():
    if not LLM_CLI.exists():
        raise SystemExit("[fatal] LLM CLI が見つかりません: services/llm/llm_cli.py")
    pr = probe_models()
    print("=== モデル選別中 ===")
    print(f"- ordered: {pr['ordered']}")
    print(pr["detail"])
    if not pr["selected"]:
        raise SystemExit("[fatal] いずれのモデルでも ping に失敗しました。config/config.yaml と環境変数を確認してください。")
    print(f"- selected: {pr['selected']}")
    return pr["selected"]

def main():
    ap = argparse.ArgumentParser(description="MCP: テスター")
    ap.add_argument("--design", required=True)
    args = ap.parse_args()

    ensure_dirs()
    require_llm_or_die()

    design = yaml_load(Path(args.design).read_text(encoding="utf-8"))
    project = design.get("project")
    if not project:
        print("[fatal] design.project がありません", file=sys.stderr); return 2
    proj_dir = PROJECTS_DIR / project
    if not proj_dir.exists():
        print("[fatal] project dir がありません", file=sys.stderr); return 2

    tests = design.get("tests") or []
    results = []
    status = "success"
    for t in tests:
        cmd = t.get("cmd")
        expect_rc = str(t.get("expect_rc","0"))
        if not cmd: continue
        rc, out, err = run(["/bin/bash","-lc", cmd], cwd=proj_dir, timeout=180)
        ok = (str(rc) == expect_rc)
        results.append({
            "name": t.get("name",""),
            "cmd": cmd,
            "rc": rc,
            "ok": ok,
            "stdout": (out or "")[-4000:],
            "stderr": (err or "")[-4000:],
        })
        if not ok:
            status = "failed"
            break

    text_all = "\n".join((r.get("stdout","") + "\n" + r.get("stderr","")) for r in results)
    kw = design.get("expected_behavior",{}).get("keywords",[])
    rx = design.get("expected_behavior",{}).get("regex",[])
    keywords_ok = all(k in text_all for k in kw)
    regex_ok = all(re.search(r, text_all) for r in rx)
    analysis = {"keywords_ok": keywords_ok, "regex_ok": regex_ok}

    ts = ts_now()
    report = {
        "phase": "test",
        "project": project,
        "timestamp": ts,
        "status": status if (status!="success" or (keywords_ok and regex_ok)) else "retry_needed",
        "results": results,
        "analysis": analysis,
    }
    out = LOG_DIR / f"{project}_{ts}_test.yaml"
    out.write_text(yaml_dump(report), encoding="utf-8")

    print("=== 実行結果 ===")
    for r in results:
        print(f"[RC={r['rc']}] {r['name']} :: {r['cmd']} (ok={r['ok']})")
        if r["stdout"].strip(): print(r["stdout"])
        if r["stderr"].strip(): print(r["stderr"])
    print(f"STATUS: {report['status']}")
    print(f"\n[Saved] {out}")
    return 0 if report["status"] in ("success","retry_needed") else 1

if __name__ == "__main__":
    sys.exit(main())
