#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/mcp/mcp_cmd.py
AIが自然文からコマンドを生成→安全に実行→解説/改善案を出すCLI

更新点:
- 特定ツール（git等）を禁止/強制しない（LLMに委ねる）。ただし危険操作はガード。
- プロンプトに「削除したい場合は .bak へリネーム提案」を明記。
- sudo制御オプション: --sudo {allow,deny,ask}（デフォルト: ask）
  - ask: sudo提案時に確認 (yで実行 / nで非sudo代替をAIに再提案して実行)
  - allow: sudo許可
  - deny: sudo禁止
- 出力は「プロンプト / 実行コマンド / コマンド結果 / AI解説 / エラー時の改善案」
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
import os, re, argparse, subprocess, time
from typing import Optional
from services.llm.llm_common import load_env_from_config, DebugLogger

# ==== ユーティリティ ====

def _strip_code_fences_text(s: str) -> str:
    """```bash ...``` などのコードフェンスを剥がす"""
    if not s:
        return s
    s = s.strip()
    s = re.sub(r"^```(?:\w+)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()

def _remove_leading_sudo(cmd: str) -> str:
    """先頭の sudo を除去（非破壊で試す用）"""
    return re.sub(r"^\s*sudo\s+(?=\S)", "", cmd.strip())

def extract_command(text: str) -> Optional[str]:
    """
    LLM出力から1行コマンドを抽出。
    優先: 先頭に'$ 'が付いた行 → それ以外なら最初の非空行。
    """
    if not text:
        return None
    t = _strip_code_fences_text(text)
    m = re.search(r"^\s*\$\s*(.+)$", t, re.M)
    cmd = (m.group(1).strip() if m else "")
    if not cmd:
        # 最初の非空行
        for line in t.splitlines():
            if line.strip():
                cmd = line.strip()
                break
    # 末尾の余計なフェンス混入を除去
    cmd = cmd.split("```", 1)[0].strip()
    # 1行だけに制限
    cmd = cmd.splitlines()[0].strip()
    return cmd or None

def is_dangerous(cmd: str) -> bool:
    """危険コマンド検出（最低限のガード）"""
    bad_substrings = [
        "rm -rf", " mkfs", "mkfs.", " :(){", "shutdown", "reboot", "halt",
        " dd if=", " :(){ :|:& };:", "chmod 000", "chown -R /"
    ]
    return any(b in cmd for b in bad_substrings)

def ask_llm(prompt: str, dbg: DebugLogger) -> str:
    """llm_cli経由でLLM応答を取得"""
    cmd = [sys.executable, "services/llm/llm_cli.py", "--smart", prompt]
    dbg.dbg("ask_llm:", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"llm_cli failed: {p.stderr.strip()}")
    return p.stdout.strip()

# ==== プロンプト ====

def build_command_prompt(goal: str, cwd: str) -> str:
    """
    コマンド生成の指示（特定ツールは縛らないが、安全要件のみ明記）
    - 削除したい場合は .bak にリネームする提案にすることも明示
    """
    return (
        f"あなたはLinuxの熟練シェルオペレータです。作業ディレクトリは {cwd}。\n"
        f"目的:\n{goal}\n\n"
        "厳守事項:\n"
        "- 実行すべき『単一のシェルコマンド』のみを1行で出力\n"
        "- 先頭に「$ 」を付ける（例: $ ls -la）\n"
        "- コードブロックや説明文は出力しない\n"
        "- 対話的操作・エディタ起動は禁止\n"
        "- sudo を使わずに実現できる方法を優先して選択\n"
        "- 破壊的な削除を避ける。削除が必要なら 'mv <path> <path>.bak' で退避する提案にする\n"
    )

def build_analysis_prompt(goal: str, cmd: str, rc: int, took: float, stdout: str, stderr: str) -> str:
    """成功・失敗に関わらず、コマンドと結果の解説（両方）を求める"""
    return (
        "以下の情報を基に、コマンドの目的と意味、そして実行結果に対する解説を書いてください。\n"
        "事実ベースで簡潔に。出力に無いことは憶測で書かない。\n\n"
        f"[プロンプト]\n{goal}\n\n"
        f"[実行コマンド]\n$ {cmd}\n\n"
        f"[終了コード]\n{rc}\n"
        f"[実行時間]\n{took:.2f}s\n\n"
        "[STDOUT 抜粋]\n" + (stdout[:2000]) + "\n\n"
        "[STDERR 抜粋]\n" + (stderr[:1000]) + "\n\n"
        "出力形式:\n"
        "- コマンドの説明: 1〜3行\n"
        "- 結果の解説: 箇条書きで最大3点\n"
    )

def build_fix_suggestion_prompt(goal: str, cmd: str, rc: int, stdout: str, stderr: str) -> str:
    """エラー時の改善案をLLMに聞くプロンプト"""
    return (
        "以下のコマンドがエラーになりました。改善案（具体的な代替コマンド or 手順）を1〜3件、"
        "短く提案してください。sudoや破壊的操作は避けてください。削除が必要なら .bak 退避を提案してください。\n\n"
        f"[プロンプト]\n{goal}\n\n"
        f"[実行コマンド]\n$ {cmd}\n\n"
        f"[終了コード]\n{rc}\n\n"
        "[STDOUT 抜粋]\n" + (stdout[:1200]) + "\n\n"
        "[STDERR 抜粋]\n" + (stderr[:800]) + "\n\n"
        "出力形式:\n- 改善案: 箇条書き 1〜3件（各1行）\n"
    )

def build_non_sudo_alternative_prompt(goal: str, cwd: str, sudo_cmd: str) -> str:
    """sudoを使わない代替1行コマンドを要求"""
    return (
        f"次の目的を達成したいが、sudoは禁止です。作業ディレクトリは {cwd}。\n"
        f"目的:\n{goal}\n\n"
        f"先ほどの提案は sudo を含むため不許可でした:\n$ {sudo_cmd}\n\n"
        "sudoを使わずに実現できる『単一のシェルコマンド』のみを1行で、先頭に「$ 」を付けて出力してください。\n"
        "破壊的削除は禁止。削除が必要なら 'mv <path> <path>.bak' で退避する提案にしてください。\n"
        "コードブロックや説明文は禁止です。"
    )

# ==== メイン ====

def main() -> int:
    load_env_from_config()
    ap = argparse.ArgumentParser(description="AI Command Executor (MCP)")
    ap.add_argument("goal", help="目的・自然文（例: 現在のpc端末の温度状態を色々確認して）")
    ap.add_argument("--cwd", default=os.getcwd(), help="作業ディレクトリ")
    ap.add_argument("--dry-run", action="store_true", help="生成のみ実行しない")
    ap.add_argument("--debug", action="store_true", help="デバッグ出力")
    ap.add_argument("--sudo", choices=["allow", "deny", "ask"], default="ask",
                    help="sudo の扱い: allow=許可, deny=禁止, ask=確認（デフォルト）")
    args = ap.parse_args()
    dbg = DebugLogger(args.debug)

    goal, cwd = args.goal, args.cwd
    dbg.dbg(f"Goal={goal}, cwd={cwd}, sudo_mode={args.sudo}")

    # --- コマンド生成 ---
    try:
        prompt = build_command_prompt(goal, cwd)
        raw = ask_llm(prompt, dbg)
        cmdline = extract_command(raw)
        if not cmdline:
            print(f"[error] コマンド抽出失敗:\n{raw}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"[error] LLM初回生成に失敗: {e}", file=sys.stderr)
        return 1

    # --- sudo方針に従ったハンドリング ---
    has_sudo = bool(re.search(r"(^|\s)sudo(\s|$)", cmdline))
    if args.sudo == "deny" and has_sudo:
        print(f"[block] sudoは禁止です: {cmdline}", file=sys.stderr)
        return 1
    if args.sudo == "ask" and has_sudo:
        # 提案確認
        print("# プロンプト")
        print(goal)
        print("\n# 実行コマンド（提案: sudo を含む）")
        print(f"$ {cmdline}")
        if args.dry_run:
            return 0
        try:
            ans = input("\n[sudo確認] このコマンドを実行しますか？ (y/N): ").strip().lower()
        except EOFError:
            ans = "n"
        if ans != "y":
            # 非sudo代替をAIに作らせる
            try:
                alt_raw = ask_llm(build_non_sudo_alternative_prompt(goal, cwd, cmdline), dbg)
                alt_cmd = extract_command(alt_raw)
                if not alt_cmd:
                    print(f"[error] 非sudo代替の抽出に失敗:\n{alt_raw}", file=sys.stderr)
                    return 1
                cmdline = alt_cmd
                has_sudo = False  # 以降はsudo扱いしない
                print("\n# 置換された実行コマンド（非sudo代替）")
                print(f"$ {cmdline}")
            except Exception as e:
                print(f"[error] 非sudo代替の生成に失敗: {e}", file=sys.stderr)
                return 1

    # --- 危険チェック（sudo以外） ---
    if is_dangerous(cmdline):
        print(f"[block] 危険コマンド検知: {cmdline}", file=sys.stderr)
        return 1

    # === 出力フォーマットここから ===
    if not (args.sudo == "ask" and has_sudo):
        # askでsudo→y確認のケースは既に見出しを出しているので重複回避
        print("# プロンプト")
        print(goal)
        print("\n# 実行コマンド")
        print(f"$ {cmdline}")

    if args.dry_run:
        return 0

    # --- 実行 ---
    t0 = time.time()
    p = subprocess.run(cmdline, shell=True, capture_output=True, text=True, cwd=cwd)
    took = time.time() - t0
    rc = p.returncode
    out, err = (p.stdout or "").strip(), (p.stderr or "").strip()

    print("\n# コマンド結果")
    print("## STDOUT (先頭2000文字)")
    print((out[:2000]) if out else "")
    print("\n## STDERR (先頭1000文字)")
    print((err[:1000]) if err else "")
    print(f"\n(終了コード: {rc}, 実行時間: {took:.2f}s)")

    # --- 解説 ---
    try:
        analysis_prompt = build_analysis_prompt(goal, cmdline, rc, took, out, err)
        analysis = ask_llm(analysis_prompt, dbg)
    except Exception as e:
        analysis = f"[error] 解析失敗: {e}"

    print("\n# AIの解説（コマンドと結果）")
    print(_strip_code_fences_text(analysis).strip())

    # --- 失敗時のみ 改善案 ---
    if rc != 0:
        try:
            fix_prompt = build_fix_suggestion_prompt(goal, cmdline, rc, out, err)
            fixes = ask_llm(fix_prompt, dbg)
        except Exception as e:
            fixes = f"[error] 改善案生成に失敗: {e}"
        print("\n# エラー時の改善案")
        print(_strip_code_fences_text(fixes).strip())

    return rc

if __name__ == "__main__":
    sys.exit(main())
