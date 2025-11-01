#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP共通ユーティリティ
- YAML操作、ファイル管理、コマンド実行などの共通機能
"""
from __future__ import annotations
import os
import re
import sys
import time
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# プロジェクトルート
ROOT = Path(__file__).resolve().parents[2]  # .../NeuroHub
PROJECTS_DIR = ROOT / "projects"
LOG_DIR = ROOT / "logs" / "ai_prj"
LLM_CLI = ROOT / "services" / "llm" / "llm_cli.py"
CONFIG_YAML = ROOT / "config" / "config.yaml"


def p(*a):
    """print with flush"""
    print(*a, flush=True)


def ensure_dirs():
    """必要なディレクトリを作成"""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def to_snake(s: str) -> str:
    """文字列をスネークケースに変換"""
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"[-\s]+", "_", s).strip("_")
    return s or "project"


def ts_now() -> str:
    """現在のタイムスタンプを返す"""
    return time.strftime("%Y%m%d-%H%M%S")


def yaml_dump(data, indent=0):
    """簡易YAML出力"""
    sp = "  " * indent
    if data is None:
        return "null"
    if isinstance(data, bool):
        return "true" if data else "false"
    if isinstance(data, (int, float)):
        return str(data)
    if isinstance(data, str):
        if re.search(r'[:{}\[\]\n"#]', data):
            return '"' + data.replace('"', '\\"') + '"'
        return data
    if isinstance(data, list):
        if not data:
            return "[]"
        out = []
        for it in data:
            y = yaml_dump(it, indent + 1)
            if "\n" in y:
                out.append(f"{sp}- |\n{sp}  " + y.replace("\n", f"\n{sp}  "))
            else:
                out.append(f"{sp}- {y}")
        return "\n".join(out)
    if isinstance(data, dict):
        if not data:
            return "{}"
        out = []
        for k, v in data.items():
            y = yaml_dump(v, indent + 1)
            if "\n" in y:
                out.append(f"{sp}{k}: |\n{sp}  " + y.replace("\n", f"\n{sp}  "))
            else:
                out.append(f"{sp}{k}: {y}")
        return "\n".join(out)
    return str(data)


def yaml_load(text: str):
    """簡易YAMLパーサー"""
    lines = text.splitlines()
    stack = [{}]
    indent_stack = [-1]
    current_key = None
    multiline_val = []
    multiline_indent = None

    def commit():
        nonlocal multiline_val, multiline_indent, current_key
        if multiline_val and current_key:
            val = "\n".join(multiline_val)
            stack[-1][current_key] = val
            current_key = None
            multiline_val = []
            multiline_indent = None

    for line in lines:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            if multiline_val and multiline_indent is not None:
                space = len(line) - len(stripped)
                if space > multiline_indent:
                    multiline_val.append(line[multiline_indent:])
            continue

        lead = len(line) - len(stripped)
        if multiline_indent is not None:
            if lead > multiline_indent:
                multiline_val.append(line[multiline_indent:])
                continue
            else:
                commit()

        while indent_stack and lead < indent_stack[-1]:
            indent_stack.pop()
            stack.pop()
            if not stack:
                stack = [{}]
                indent_stack = [-1]
                break

        if stripped.startswith("- "):
            commit()
            parent = stack[-1]
            if not isinstance(parent, list):
                parent = []
                if indent_stack:
                    k = list(stack[-2].keys())[-1] if isinstance(stack[-2], dict) else None
                    if k:
                        stack[-2][k] = parent
                stack[-1] = parent
            rest = stripped[2:]
            if ":" in rest:
                idx = rest.index(":")
                k = rest[:idx].strip()
                v = rest[idx + 1:].strip()
                obj = {k: _parse_scalar(v)}
                parent.append(obj)
            else:
                parent.append(_parse_scalar(rest))
        elif ":" in stripped:
            commit()
            idx = stripped.index(":")
            k = stripped[:idx].strip()
            v = stripped[idx + 1:].strip()
            if v == "|":
                current_key = k
                multiline_indent = lead + len(stripped) - len(v)
                continue
            stack[-1][k] = _parse_scalar(v)
        else:
            if multiline_val:
                multiline_val.append(stripped)

    commit()
    return stack[0] if len(stack) == 1 else stack


def _parse_scalar(v: str):
    """スカラー値をパース"""
    if not v:
        return None
    if v in ("null", "~"):
        return None
    if v in ("true", "yes"):
        return True
    if v in ("false", "no"):
        return False
    if re.match(r"^-?\d+$", v):
        return int(v)
    if re.match(r"^-?\d+\.\d+$", v):
        return float(v)
    return v


def run(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 180) -> Tuple[int, str, str]:
    """コマンドを実行"""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def strip_code_fences(s: str) -> str:
    """コードフェンスを削除"""
    s = re.sub(r"^```[\w]*\n", "", s, flags=re.MULTILINE)
    s = re.sub(r"\n```$", "", s, flags=re.MULTILINE)
    return s.strip()


def probe_models() -> Dict[str, str]:
    """利用可能なLLMモデルを検出"""
    models = {}

    # Gemini
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            models["gemini"] = "gemini-pro"
    except:
        pass

    # HuggingFace
    hf_token = os.getenv("HUGGINGFACE_API_KEY")
    if hf_token:
        models["huggingface"] = "mistralai/Mistral-7B-Instruct-v0.2"

    # Ollama
    try:
        code, out, err = run(["ollama", "list"], timeout=5)
        if code == 0 and "llama" in out.lower():
            models["ollama"] = "llama3"
    except:
        pass

    return models


def require_llm_or_die():
    """LLMが利用可能かチェック"""
    models = probe_models()
    if not models:
        p("[ERROR] No LLM provider found. Please set GEMINI_API_KEY, HUGGINGFACE_API_KEY, or install Ollama.")
        sys.exit(1)
    return models
