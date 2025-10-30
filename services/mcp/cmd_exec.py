#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/mcp/cmd_exec.py  (improved)

自然文 → コマンド生成/レシピ優先 → 実行 → LLMリトライ → 解説
改良点:
- 既知ゴールはレシピを優先（例: グローバルIP）
- 成功判定を強化 (--require-output/--success-pattern/--min-bytes)
- 目標から自動成功パターン (IPv4 etc.)
"""

from __future__ import annotations
import os, sys, re, json, time, argparse, subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.llm.llm_common import DebugLogger
from services.mcp.core import (
    ask_llm, extract_command, is_dangerous, non_destructive_only, log_event
)

# ---------- レシピ（高信頼初手） ----------
RECIPES: Dict[str, str] = {
    "global_ip": (
        "(command -v curl >/dev/null 2>&1 && curl -fsS https://ifconfig.me)"
        " || (command -v dig >/dev/null 2>&1 && dig +short myip.opendns.com @resolver1.opendns.com)"
        " || (command -v wget >/dev/null 2>&1 && wget -qO- https://ifconfig.me)"
        " || (command -v drill >/dev/null 2>&1 && drill -Q myip.opendns.com @resolver1.opendns.com)"
        " || (printf 'no external IP source found\\n' >&2; exit 1)"
    ),
}

def pick_recipe(goal: str) -> Optional[str]:
    g = (goal or "").lower()
    if any(k in g for k in ["グローバルip", "グローバル ip", "global ip", "外向きip", "外部ip"]):
        return RECIPES["global_ip"]
    return None

# ---------- 目標から成功パターン自動決定 ----------
def auto_success_pattern(goal: str) -> Optional[str]:
    g = (goal or "").lower()
    # IPv4っぽいもの
    if any(k in g for k in ["グローバルip", "グローバル ip", "global ip", "外向きip", "外部ip"]):
        return r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    return None

# ---------- LLMプロンプト ----------
def prompt_first_cmd(goal: str, cwd: str) -> str:
    return (
        "あなたはLinuxシェルの専門家です。以下の目的を達成する安全な単一のコマンドを1行で提案してください。\n"
        f"- 作業ディレクトリ: {cwd}\n"
        "- 出力は **コードブロック無し**。必要なら先頭に `$ ` を付けてもよい\n"
        "- sudo禁止（どうしても必要なら提案は可だが、その場合は 'sudo ' を含める）\n"
        "- 破壊的操作は禁止。削除は mv <path> <path>.bak に置換すること\n"
        "- リダイレクト(>, >>, tee)や権限変更(chmod/chown)は禁止\n"
        f"\n目的: {goal}\n"
    )

def prompt_retry_json(goal: str, cwd: str, attempts: int, last_cmd: str, rc: int, out: str, err: str, history_snip: str) -> str:
    return (
        "あなたはLinuxシェルの専門家であり、逐次改善のコーチです。\n"
        "次の実行履歴を踏まえて、**JSONのみ**でリトライ方針を返してください（前後に説明文を付けない）。\n"
        "スキーマ:\n"
        '{ "retry": true|false, "reason": "短い説明", "wait_sec": <number>, "next_cmd": "$ ... (任意)" }\n'
        "- retry=false なら終了。retry=true の場合、可能なら next_cmd を提案。省略時は直前コマンドを再実行。\n"
        "- sudo禁止。破壊・権限変更・リダイレクト禁止。.bak退避は可。\n"
        "- 出力は必ず **1行のJSON文字列のみ**。\n\n"
        f"[目的]\n{goal}\n"
        f"[作業ディレクトリ]\n{cwd}\n"
        f"[試行回数]\n{attempts}\n"
        f"[直前コマンド]\n$ {last_cmd}\n"
        f"[終了コード]\n{rc}\n"
        f"[STDOUT 抜粋(先頭500)]\n{out[:500]}\n"
        f"[STDERR 抜粋(先頭500)]\n{err[:500]}\n"
        f"[履歴要約]\n{history_snip}\n"
        "JSONのみで応答:"
    )

# ---------- JSON抽出 ----------
def extract_json_line(text: str) -> Optional[dict]:
    if not text:
        return None
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

# ---------- 安全フィルタ ----------
def sanitize_command(cmd: str) -> Optional[str]:
    if not cmd:
        return None
    s = cmd.strip()
    if s.startswith("$"):
        s = s[1:].strip()
    s = s.splitlines()[0].strip()
    if is_dangerous(s) or not non_destructive_only(s):
        return None
    return s

def maybe_confirm(prompt: str) -> bool:
    try:
        return input(prompt + " (y/N): ").strip().lower() in {"y", "yes"}
    except EOFError:
        return False

# ---------- 実行 ----------
def run_once(cmd: str, cwd: str, timeout: float = 60.0) -> Tuple[int, str, str, float]:
    t0 = time.time()
    p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    dt = round(time.time() - t0, 2)
    return p.returncode, (p.stdout or ""), (p.stderr or ""), dt

# ---------- 成功判定 ----------
def is_effective_success(rc: int, out: str, require_output: bool, success_pattern: Optional[re.Pattern], min_bytes: int) -> bool:
    if rc != 0:
        return False
    out_s = (out or "")
    if require_output and len(out_s.strip()) < max(0, min_bytes):
        return False
    if success_pattern and not success_pattern.search(out_s):
        return False
    return True

# ---------- main ----------
def main() -> int:
    ap = argparse.ArgumentParser(description="自然文→生成/レシピ→実行→LLMリトライ→解説（強化版）")
    ap.add_argument("input", nargs="+", help="自然文の目的、または '$ コマンド'")
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--sudo", choices=["allow","deny","ask"], default="ask", help="sudo使用方針")
    ap.add_argument("--max-attempts", type=int, default=5, help="最大試行回数")
    ap.add_argument("--timeout", type=float, default=60.0, help="1回のコマンド実行タイムアウト秒")
    ap.add_argument("--no-explain", action="store_true", help="最後のAI解説を行わない")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--cmd", help="明示コマンドを実行（$不要）")

    # 成功判定関連
    ap.add_argument("--require-output", action="store_true", default=True, help="STDOUTが空なら失敗扱い（デフォルトON）")
    ap.add_argument("--no-require-output", dest="require_output", action="store_false")
    ap.add_argument("--success-pattern", help="STDOUTにマッチ必須の正規表現")
    ap.add_argument("--min-bytes", type=int, default=1, help="STDOUTの最小バイト数（既定1。0にすれば無効同然）")

    args = ap.parse_args()

    dbg = DebugLogger(args.debug)
    cwd = os.path.abspath(args.cwd)
    goal_or_cmd = " ".join(args.input)

    print(f"# CWD\n{cwd}\n")

    # 成功パターン（自動推定→明示指定があれば上書き）
    auto_pat = auto_success_pattern(goal_or_cmd if not args.cmd and not goal_or_cmd.strip().startswith("$") else "")
    success_pat: Optional[re.Pattern] = None
    try:
        if args.success_pattern:
            success_pat = re.compile(args.success_pattern, re.M)
        elif auto_pat:
            success_pat = re.compile(auto_pat, re.M)
    except Exception as e:
        print(f"[warn] success-pattern invalid: {e}", file=sys.stderr)

    # 初手コマンド決定（既知ゴールはまずレシピ、それ以外はLLM）
    if args.cmd:
        initial_cmd = args.cmd
        goal = f"(direct) {goal_or_cmd}"
    elif goal_or_cmd.strip().startswith("$"):
        initial_cmd = goal_or_cmd.strip()[1:].strip()
        goal = f"(direct) {goal_or_cmd}"
    else:
        goal = goal_or_cmd
        recipe = pick_recipe(goal)
        if recipe:
            initial_cmd = recipe
        else:
            try:
                body, meta = ask_llm(prompt_first_cmd(goal, cwd), dbg)
                c = extract_command(body)
            except Exception:
                c = None
            if not c:
                print("[error] 初手コマンド生成に失敗", file=sys.stderr)
                return 1
            initial_cmd = c

    # sudoポリシー
    if " sudo " in f" {initial_cmd} ":
        if args.sudo == "deny":
            print("[block] sudoは禁止です。", file=sys.stderr); return 1
        if args.sudo == "ask" and not maybe_confirm("[sudo確認] 初手コマンドにsudoが含まれます。実行しますか？"):
            print("[info] sudoを含む初手案の実行をキャンセル。", file=sys.stderr)
            return 1

    cmdline = sanitize_command(initial_cmd)
    if not cmdline:
        print("[block] 初手コマンドが危険/破壊的と判定: ", initial_cmd, file=sys.stderr)
        return 1

    attempts = 0
    history_snip = ""
    last_rc = 1
    last_out = ""
    last_err = ""

    print(f"# プロンプト / 目的\n{goal}\n")

    while attempts < args.max_attempts:
        attempts += 1
        print(f"# 実行コマンド (try {attempts})\n$ {cmdline}\n")
        rc, out, err, took = run_once(cmdline, cwd, timeout=args.timeout)
        print("# コマンド結果")
        print("## STDOUT (先頭2000)\n" + out[:2000] + "\n")
        if err:
            print("## STDERR (先頭1000)\n" + err[:1000] + "\n")
        print(f"(rc={rc}, took={took:.2f}s)\n")

        log_event({
            "kind": "exec",
            "goal": goal,
            "cmd": cmdline,
            "rc": rc,
            "stdout": out[:500],
            "stderr": err[:300],
            "cwd": cwd,
            "attempt": attempts,
        })

        # --- 強化された成功判定 ---
        if is_effective_success(rc, out, args.require_output, success_pat, args.min_bytes):
            print("# 完了: 成功条件を満たしたので終了します。")
            last_rc, last_out, last_err = rc, out, err
            break

        # 失敗 → LLM にリトライ方針を問い合わせ
        last_rc, last_out, last_err = rc, out, err
        history_snip = (history_snip + f"[{attempts}] $ {cmdline} -> rc={rc}\n").strip()[-800:]
        try:
            advice_body, _ = ask_llm(
                prompt_retry_json(goal, cwd, attempts, cmdline, rc, out, err, history_snip),
                dbg
            )
        except Exception as e:
            print(f"[error] リトライ方針の取得に失敗: {e}")
            break

        plan = extract_json_line(advice_body)
        if not plan:
            print("[error] LLMから有効なJSONが得られませんでした。中止。")
            break

        retry = bool(plan.get("retry", False))
        reason = str(plan.get("reason", "") or "")
        wait_sec = float(plan.get("wait_sec", 0) or 0)
        next_cmd_raw = str(plan.get("next_cmd", "") or "")

        print("# LLMリトライ方針")
        print(json.dumps({"retry": retry, "reason": reason, "wait_sec": wait_sec, "next_cmd": next_cmd_raw}, ensure_ascii=False))
        print()

        if not retry:
            print("# LLM指示: ここで終了（retry=false）")
            break

        next_cmd = next_cmd_raw.strip() or cmdline
        if " sudo " in f" {next_cmd} ":
            if args.sudo == "deny":
                print("[block] sudoは禁止です（リトライ案）。中止。", file=sys.stderr)
                break
            if args.sudo == "ask" and not maybe_confirm("[sudo確認] リトライ案にsudoが含まれます。実行しますか？"):
                print("[info] sudoを含むリトライ案の実行をキャンセル。中止。", file=sys.stderr)
                break

        safe_cmd = sanitize_command(next_cmd)
        if not safe_cmd:
            print("[block] 提案コマンドが危険/破壊的と判定。中止。", file=sys.stderr)
            break

        if wait_sec > 0:
            time.sleep(min(wait_sec, 10.0))

        cmdline = safe_cmd

    # 簡易解説
    if not args.no_explain:
        try:
            summary_prompt = (
                "次のコマンドと結果を短く解説し、改善案があれば1〜2点提案してください。\n"
                f"[目的]\n{goal}\n"
                f"[最終コマンド]\n$ {cmdline}\n"
                f"[終了コード]\n{last_rc}\n"
                f"[STDOUT抜粋]\n{(last_out or '')[:1000]}\n"
                f"[STDERR抜粋]\n{(last_err or '')[:600]}\n"
                "出力形式:\n- 解説: 1〜3行\n- 改善案: 箇条書き"
            )
            body, _ = ask_llm(summary_prompt, DebugLogger(False))
            print("# AI解説\n" + body.strip())
        except Exception as e:
            print(f"[warn] 解説生成に失敗: {e}", file=sys.stderr)

    return 0 if is_effective_success(last_rc, last_out, args.require_output, success_pat, args.min_bytes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
