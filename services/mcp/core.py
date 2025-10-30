#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/mcp/core.py

共通ユーティリティ:
- ask_llm: llm_cliを叩いて本文/METAを取得
- extract_command: LLM出力から1行コマンド抽出
- is_dangerous / non_destructive_only: 危険/破壊的コマンドの簡易判定
- log_event: 実行ログを logs/mcp_exec.log に1行JSONで追記
"""

from __future__ import annotations
import os, sys, re, json, subprocess, getpass
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Optional

# プロジェクトルートをPYTHONPATHに
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.llm.llm_common import load_env_from_config, DebugLogger

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "mcp_exec.log"

# ========== ログ ==========
def log_event(entry: Dict) -> None:
    try:
        e = dict(entry)
        e.setdefault("user", getpass.getuser())
        e.setdefault("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    except Exception as ex:
        print(f"[warn] log write failed: {ex}", file=sys.stderr)

# ========== LLM呼び出し ==========
def _parse_llm_meta_and_body(text: str) -> Tuple[str, Dict]:
    """
    llm_cliの出力の先頭が '###META### {...}' ならMETAをJSONとして取り出し、本文を返す。
    """
    meta: Dict = {}
    if not text:
        return "", meta
    lines = text.splitlines()
    if lines and lines[0].startswith("###META### "):
        try:
            meta = json.loads(lines[0].split("###META### ", 1)[1])
        except Exception:
            meta = {}
        body = "\n".join(lines[1:]).strip()
        return body, meta
    return text.strip(), meta

def ask_llm(prompt: str, dbg: Optional[DebugLogger] = None) -> Tuple[str, Dict]:
    """
    llm_cli.py を --smart で起動して応答を取得。
    戻り値: (本文, meta_dict)
    """
    load_env_from_config()
    cmd = [sys.executable, "services/llm/llm_cli.py", "--smart", prompt]
    if dbg: dbg.dbg("ask_llm:", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"llm_cli failed: {p.stderr.strip()}")
    body, meta = _parse_llm_meta_and_body(p.stdout.strip())
    return body, meta

# ========== コマンド抽出 ==========
_CODE_FENCE_START = re.compile(r"^```(?:\w+)?\s*$")
_CODE_FENCE_END   = re.compile(r"^```\s*$")

def _strip_code_fences_text(text: str) -> str:
    """
    ```bash ...``` / ```...``` で囲まれていたら中身だけを返す。
    混在も考慮して単純に最初と最後のフェンスを取り除く。
    """
    if not text:
        return text
    lines = text.splitlines()
    if lines and _CODE_FENCE_START.match(lines[0]):
        # 末尾の ``` を探す
        for i in range(len(lines) - 1, -1, -1):
            if _CODE_FENCE_END.match(lines[i]):
                return "\n".join(lines[1:i]).strip()
    return text.strip()

def extract_command(text: str) -> Optional[str]:
    """
    LLMの出力から最初の実行行を1本抽出。
    - 先頭が '$' の場合は取り除く
    - コメント/空行/META行はスキップ
    - 複数行あっても最初の1行だけ
    """
    if not text:
        return None
    t = _strip_code_fences_text(text)
    for line in t.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("###META###"):
            continue
        if s.startswith("$"):
            s = s[1:].strip()
        return s
    return None

# ========== 安全判定 ==========
# 「危険」の代表（sudoは方針により拒否されるのでここでは参考程度）
DANGER_TOKENS = [
    " rm -rf", " mkfs", " dd if=", " :(){ :|:& };:", " shutdown", " reboot",
    " poweroff", " init 0", " chown -R /", " :(){:|:&};:"  # いわゆるfork爆弾
]

def is_dangerous(cmd: str) -> bool:
    """
    ざっくり危険そうなものを弾く。
    """
    if not cmd:
        return True
    low = f" {cmd.lower()} "
    # sudo含みは基本的に危険寄りとして扱う（最終可否は実行側オプションで制御）
    if " sudo " in low:
        return True
    return any(tok in low for tok in DANGER_TOKENS)

def non_destructive_only(cmd: str) -> bool:
    """
    破壊/変更系（削除・権限変更・リダイレクト等）を禁止。
    .bak退避などは生成側で対応してもらう前提。
    """
    if not cmd:
        return False
    low = f" {cmd.lower()} "
    banned = [
        " sudo ", " rm ", " mkfs", " dd ", " chmod ", " chown ", " chgrp ",
        " > ", " >> ", " tee ", " :> ", " truncate "
    ]
    if any(b in low for b in banned):
        return False
    # 1行のみ許可
    return "\n" not in cmd
