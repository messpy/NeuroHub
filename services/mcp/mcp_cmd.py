#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/mcp/mcp_cmd.py
AIが自然文からコマンドを生成→安全に実行→出力解析するCLI
"""
from __future__ import annotations

# --- import パス設定（ルート追加） ---
from pathlib import Path
import sys

_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# --- 通常 import ---
import os, re, json, argparse, subprocess, time
from typing import Optional
from services.llm.llm_common import load_env_from_config, DebugLogger


# ==== 汎用ユーティリティ ====

def _strip_code_fences_text(s: str) -> str:
    """```bash ...``` などを除去"""
    if not s: return s
    s = s.strip()
    s = re.sub(r"^```(?:\w+)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()

def _sanitize_sudo_for_git(cmd: str) -> str:
    """sudo git ... の sudo を除去"""
    return re.sub(r"^\s*sudo\s+(?=git\b)", "", cmd.strip())

def extract_command(text: str) -> Optional[str]:
    """LLM出力から1行コマンドを抽出"""
    if not text:
        return None
    t = _strip_code_fences_text(text)
    m = re.search(r"^\s*\$\s*(.+)$", t, re.M)
    cmd = (m.group(1).strip() if m else t.splitlines()[0].strip())
    cmd = cmd.split("```", 1)[0].strip()
    cmd = _sanitize_sudo_for_git(cmd)
    cmd = cmd.splitlines()[0].strip()
    return cmd or None

def is_dangerous(cmd: str) -> bool:
    """危険コマンド検出"""
    bad = ["sudo", "rm -rf", "mkfs", ":(){", "shutdown", "reboot", "dd if="]
    return any(b in cmd for b in bad)

def ask_llm(prompt: str, dbg: DebugLogger) -> str:
    """llm_cli経由でLLM応答を取得"""
    cmd = [sys.executable, "services/llm/llm_cli.py", "--smart", prompt]
    dbg.dbg("ask_llm:", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"llm_cli failed: {p.stderr.strip()}")
    return p.stdout.strip()


# ==== 環境検出・意図判定 ====

def detect_env(cwd: str) -> dict:
    """VCSを検出: git / hg / svn / fossil / None"""
    p = Path(cwd)
    if (p / ".git").exists():
        return {"vcs": "git"}
    if (p / ".hg").exists():
        return {"vcs": "hg"}
    if (p / ".svn").exists():
        return {"vcs": "svn"}
    if (p / ".fossil").exists() or (p / "_FOSSIL_").exists():
        return {"vcs": "fossil"}
    return {"vcs": None}

def detect_intent(goal: str) -> str | None:
    """自然文から大まかな意図を判定"""
    g = goal.lower()
    if any(k in g for k in ["ログ", "log", "履歴", "recent"]) and any(k in g for k in ["直近", "3", "３", "few", "latest"]):
        return "recent_logs"
    if any(k in g for k in ["差分", "diff", "ステージ", "stage", "ステージング", "状態", "status", "確認", "一覧"]):
        return "status_summary"
    return None

def plan_command(intent: str, env: dict) -> str | None:
    """意図×環境に応じた安全な1行コマンドを返す"""
    vcs = env.get("vcs")

    if intent == "recent_logs":
        if vcs == "git":
            return "git --no-pager log --oneline -n 3"
        if vcs == "hg":
            return r'hg --color=never log -l 3 --template "{node|short} {desc|firstline}\n"'
        if vcs == "svn":
            return "svn log -l 3"
        if vcs == "fossil":
            return "fossil timeline -n 3"
        return 'find . -maxdepth 1 -type f -printf "%TY-%Tm-%Td %TH:%TM %s %f\n" | sort -r | head -n 3'

    if intent == "status_summary":
        if vcs == "git":
            return (
                "git status --short && "
                "echo '--- DIFF(WD→INDEX) ---' && git diff --stat && "
                "echo '--- DIFF(INDEX→HEAD) ---' && git diff --cached --stat && "
                "echo '--- RECENT LOG ---' && git --no-pager log --oneline -n 5"
            )
        if vcs == "hg":
            return (
                "hg status && echo '--- DIFF ---' && hg diff --stat && "
                "echo '--- RECENT LOG ---' && hg --color=never log -l 5 --template '{node|short} {desc|firstline}\\n'"
            )
        if vcs == "svn":
            return (
                "svn status && echo '--- DIFF ---' && svn diff --summarize && "
                "echo '--- RECENT LOG ---' && svn log -l 5"
            )
        if vcs == "fossil":
            return (
                "fossil changes && echo '--- DIFF ---' && fossil diff --brief && "
                "echo '--- RECENT ---' && fossil timeline -n 5"
            )
        return (
            'echo "--- RECENT FILES ---" && '
            'find . -maxdepth 1 -type f -printf "%TY-%Tm-%Td %TH:%TM %s %f\n" | sort -r | head -n 10'
        )
    return None


# ==== プロンプト構築 ====

def build_command_prompt(goal: str, cwd: str) -> str:
    """目的→実行コマンド生成用プロンプト"""
    return (
        f"あなたはLinuxの熟練シェルオペレータです。作業ディレクトリは {cwd}。\n"
        f"目的:\n{goal}\n\n"
        "出力要件:\n"
        "- 実行すべき『単一のシェルコマンド』のみを1行で出力\n"
        "- 先頭に「$ 」を付ける（例: $ ls -la）\n"
        "- 説明・装飾・コードブロックは禁止\n"
        "- 対話的操作・エディタ起動は禁止\n"
        "- sudo は禁止\n"
    )

def build_retry_prompt(goal: str, cwd: str, last_cmd: str, rc: int, stderr: str) -> str:
    """再試行プロンプト"""
    return (
        "前回のコマンドは目的に適合しなかった、または失敗しました。新しい1行コマンドを提案してください。\n\n"
        f"作業ディレクトリ: {cwd}\n"
        f"目的: {goal}\n\n"
        f"直前の提案: $ {last_cmd}\n"
        f"終了コード: {rc}\n"
        "エラーメッセージ（要約可）:\n"
        f"{(stderr or '').strip()[:1000]}\n\n"
        "出力要件:\n"
        "- 単一のコマンドを1行で\n"
        "- sudoは禁止\n"
        "- コードブロックや説明文を含めない\n"
    )

def build_analysis_prompt(goal: str, cmd: str, rc: int, took: float, stdout: str, stderr: str) -> str:
    """結果解析用プロンプト"""
    return (
        "以下のコマンド実行結果を、事実に基づいて簡潔に要約してください。\n"
        "出力に存在しない情報は書かないでください。\n\n"
        f"目的: {goal}\n"
        f"実行: $ {cmd}\n"
        f"終了コード: {rc}\n"
        f"実行時間: {took:.2f}s\n\n"
        "[STDOUT 抜粋]\n" + (stdout[:1800]) + "\n\n"
        "[STDERR 抜粋]\n" + (stderr[:800]) + "\n\n"
        "出力形式:\n"
        "- 要約: 箇条書きで最大3点（事実のみ）\n"
        "- 提案: あれば1行（次の具体コマンド例）\n"
    )


# ==== メイン ====

def main() -> int:
    load_env_from_config()
    ap = argparse.ArgumentParser(description="AI Command Executor (MCP)")
    ap.add_argument("goal", help="目的・自然文")
    ap.add_argument("--cwd", default=os.getcwd(), help="作業ディレクトリ")
    ap.add_argument("--dry-run", action="store_true", help="生成のみ実行しない")
    ap.add_argument("--debug", action="store_true", help="デバッグ出力")
    ap.add_argument("--allow-dangerous", action="store_true", help="危険コマンド実行を許可")
    args = ap.parse_args()
    dbg = DebugLogger(args.debug)

    goal, cwd = args.goal, args.cwd
    dbg.dbg(f"Goal={goal}, cwd={cwd}")

    # --- コマンド生成 ---
    try:
        prompt = build_command_prompt(goal, cwd)
        raw = ask_llm(prompt, dbg)
        cmdline = extract_command(raw)
        if not cmdline:
            print(f"[error] コマンド抽出失敗:\n{raw}", file=sys.stderr)
            return 1

        # 意図・環境を判定して上書き
        env = detect_env(cwd)
        intent = detect_intent(goal)
        planned = plan_command(intent, env) if intent else None
        if planned:
            dbg.dbg(f"intent={intent}, vcs={env.get('vcs')}, override-> {planned}")
            cmdline = planned

    except Exception as e:
        print(f"[error] LLM初回生成に失敗: {e}", file=sys.stderr)
        return 1

    # --- 危険コマンドチェック ---
    if is_dangerous(cmdline) and not args.allow_dangerous:
        print(f"[block] 危険コマンド検知: {cmdline}", file=sys.stderr)
        return 1

    print(f"[run#1] $ {cmdline}")

    if args.dry_run:
        return 0

    # --- 実行 ---
    attempt = 1
    while True:
        t0 = time.time()
        p = subprocess.run(cmdline, shell=True, capture_output=True, text=True, cwd=cwd)
        took = time.time() - t0
        rc = p.returncode
        out, err = p.stdout.strip(), p.stderr.strip()

        print(f"[rc={rc}] took={took:.2f}s\n")

        if rc == 0:
            break
        if attempt >= 3:
            print("[error] 3回失敗したため終了", file=sys.stderr)
            break

        retry_prompt = build_retry_prompt(goal, cwd, cmdline, rc, err)
        try:
            retry_raw = ask_llm(retry_prompt, dbg)
            next_cmd = extract_command(retry_raw)

            # 再試行時も意図×環境で上書き
            env = detect_env(cwd)
            intent = detect_intent(goal)
            planned = plan_command(intent, env) if intent else None
            if planned:
                cmdline = planned
            elif next_cmd and next_cmd != cmdline:
                cmdline = next_cmd
            else:
                print("[warn] 新しいコマンドが得られなかったため終了", file=sys.stderr)
                break

            if is_dangerous(cmdline) and not args.allow_dangerous:
                print(f"[block] 危険コマンド検知: {cmdline}", file=sys.stderr)
                return 1

            print(f"[retry#{attempt}] $ {cmdline}")
        except Exception as e:
            print(f"[error] 再試行生成に失敗: {e}", file=sys.stderr)
            break
        attempt += 1

    # --- 結果解析 ---
    try:
        analysis_prompt = build_analysis_prompt(goal, cmdline, rc, took, out, err)
        analysis = ask_llm(analysis_prompt, dbg)
    except Exception as e:
        analysis = f"[error] 解析失敗: {e}"

    print("===== RESULT =====")
    print(f"Command : $ {cmdline}")
    print(f"RC      : {rc}")
    print(f"Elapsed : {took:.2f}s")
    print("----- STDOUT (first 4000 chars) -----")
    print(out[:4000])
    print("\n----- STDERR (first 2000 chars) -----")
    print(err[:2000])
    print("\n----- AI Analysis -----")
    print(analysis.strip())

    return rc


if __name__ == "__main__":
    sys.exit(main())
