#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # ~/work/NeuroHub
WEATHER = ROOT / "services" / "agent" / "weather_agent.py"
WEB = ROOT / "services" / "agent" / "web_agent.py"

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

    args = ap.parse_args()
    if not args.sub:
        ap.print_help()
        return 1
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())

