#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_cmd_exec.py
- services/mcp/cmd_exec.py の単体スモークテスト
- LLM 提案→コマンド実行の一連の流れが「最低限動くか」を確認する
- 依存: 標準ライブラリのみ（requests 等は cmd_exec 側が使う）
- 成功/失敗に関わらず、stdout/stderr と mcp_exec.log の末尾を表示する
"""
import os, sys, subprocess, time, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY   = sys.executable
CMD  = ROOT / "services" / "mcp" / "cmd_exec.py"
LOGF = ROOT / "logs" / "mcp_exec.log"

CASES = [
    # “安全に成功が期待できる”指示（echoを狙う）
    '次のコマンドを1行で実行して。$ echo "HELLO_CMD_TEST"',
    # “自然文→コマンド化”の最低限（echo系を誘導）
    'カレントディレクトリの絶対パスを出力して（可能なら `pwd` を使う）。',
    # 失敗を誘発（存在しないコマンド）し、エラー処理パスを見る
    '次のコマンドを実行して。$ hogefugapiyo --version',
]

def run(case: str, timeout=60):
    t0 = time.time()
    r = subprocess.run([PY, str(CMD), case],
                       text=True, capture_output=True, timeout=timeout, cwd=str(ROOT))
    dt = time.time() - t0
    return r.returncode, dt, r.stdout, r.stderr

def tail_log(path: pathlib.Path, n=120) -> str:
    try:
        if not path.exists():
            return "(log not found)"
        txt = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(txt[-n:]) if txt else "(log empty)"
    except Exception as e:
        return f"(log read error: {e})"

def main():
    print("== test_cmd_exec: START ==")
    print("ROOT:", ROOT)
    print("PY  :", PY)
    print("CMD :", CMD)
    if not CMD.exists():
        print("SKIP: services/mcp/cmd_exec.py not found")
        return 0

    fails = 0
    for i, case in enumerate(CASES, 1):
        print("\n" + "="*10 + f" CASE {i} " + "="*10)
        print("PROMPT:", case)
        rc, dt, out, err = run(case)
        print(f"RC={rc}  TIME={dt:.3f}s")
        if out.strip():
            print("[STDOUT]\n" + out.strip()[:1200])
        if err.strip():
            print("[STDERR]\n" + err.strip()[:800])
        if rc != 0:
            fails += 1

    print("\n--- mcp_exec.log (tail) ---")
    print(tail_log(LOGF, n=160))

    print("\n== SUMMARY ==")
    print("FAILS:", fails)
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
