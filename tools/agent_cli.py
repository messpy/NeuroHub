#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # ~/NeuroHub
WEATHER = ROOT / "agents" / "specialized" / "weather_agent.py"
WEB = ROOT / "agents" / "specialized" / "web_agent.py"
LLM = ROOT / "agents" / "llm_agent.py"

def run(cmd: list[str]) -> int:
    p = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
    return p.returncode

def cmd_weather(args) -> int:
    if not WEATHER.exists():
        print(f"[error] not found: {WEATHER}", file=sys.stderr)
        return 2
    base = [sys.executable, str(WEATHER)]
    # 透過（知らない引数はそのまま weather_agent.py に渡す）
    return run(base + args.pass_through)

def cmd_llm_chunk(args) -> int:
    """LLMのチャンク処理コマンド"""
    if not LLM.exists():
        print(f"[error] not found: {LLM}", file=sys.stderr)
        return 2

    # チャンクサイズのデフォルト値
    chunk_size = getattr(args, 'chunk_size', 500)

    if hasattr(args, 'file') and args.file:
        # ファイルからテキストを読み込み
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"[error] ファイル読み込み失敗: {e}", file=sys.stderr)
            return 3
    elif hasattr(args, 'text') and args.text:
        text = args.text
    else:
        print("[error] --file または --text を指定してください", file=sys.stderr)
        return 4

    # LLMエージェントを呼び出し
    cmd = [
        sys.executable, str(LLM),
        '--chunk', str(chunk_size),
        '--instruction', getattr(args, 'instruction', '要約してください')
    ]

    if hasattr(args, 'file') and args.file:
        cmd.extend(['--file', args.file])
    else:
        cmd.extend(['--text', text])

    return run(cmd)

def cmd_web(args) -> int:
    if not WEB.exists():
        print(f"[error] not found: {WEB}", file=sys.stderr)
        return 2
    # 例: web_agent.py <url> <question> [--pretty]
    base = [sys.executable, str(WEB)]
    return run(base + [args.url, args.question] + (["--pretty"] if args.pretty else []))

def main() -> int:
    ap = argparse.ArgumentParser(prog="agent")
    sub = ap.add_subparsers(dest="sub")

    # weather サブコマンド（引数は全部パススルー）
    ap_w = sub.add_parser("weather", help="weather_agent.py wrapper")
    ap_w.add_argument("pass_through", nargs=argparse.REMAINDER,
                      help="(pass-through) ex) --lat 35.68 --lon 139.76 --json")
    ap_w.set_defaults(func=cmd_weather)

    # web サブコマンド（既存web_agent直結）
    ap_web = sub.add_parser("web", help="web_agent.py wrapper")
    ap_web.add_argument("url", help="URL")
    ap_web.add_argument("question", help="質問/プロンプト")
    ap_web.add_argument("--pretty", action="store_true")
    ap_web.set_defaults(func=cmd_web)

    # chunk サブコマンド（LLMチャンク処理）
    ap_chunk = sub.add_parser("chunk", help="LLM chunk processing")
    ap_chunk_input = ap_chunk.add_mutually_exclusive_group(required=True)
    ap_chunk_input.add_argument("--file", help="入力ファイルパス")
    ap_chunk_input.add_argument("--text", help="入力テキスト")
    ap_chunk.add_argument("--chunk-size", type=int, default=500, help="チャンクサイズ（デフォルト: 500文字）")
    ap_chunk.add_argument("--instruction", default="要約してください", help="各チャンクへの指示")
    ap_chunk.set_defaults(func=cmd_llm_chunk)

    args = ap.parse_args()
    if not args.sub:
        ap.print_help()
        return 1
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
