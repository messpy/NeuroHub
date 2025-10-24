#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini APIキー検証スクリプト
- ~/.gemini/.env または NeuroHub/config/.env を使用
- v1 API / gemini-2.5-flash 対応
"""

import os, sys, json, requests
from pathlib import Path

AI_STUDIO_URL = "https://aistudio.google.com/app/apikey"
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"

HOME = Path.home()
CONF_DIR = HOME / ".gemini"
CONF_FILE = CONF_DIR / ".env"

# NeuroHub 側の .env（存在すれば同期対象にする）
NEUROHUB_ENV = HOME / "NeuroHub/config/.env"

def load_key():
    """環境変数→.env→NeuroHubの順でキーを探す"""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()
    for path in [CONF_FILE, NEUROHUB_ENV]:
        if path.exists():
            for line in path.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return None

def test_key(key: str):
    """APIキーで実際にテキスト生成を試す"""
    try:
        payload = {
            "contents": [
                {"parts": [{"text": "こんにちは"}]}
            ]
        }
        r = requests.post(
            f"{API_URL}?key={key}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        ok = r.status_code == 200 and "candidates" in r.text
        return ok, r.status_code, r.text
    except Exception as e:
        return False, 0, str(e)

def save_key(key: str):
    """キーを保存＆NeuroHubにも反映"""
    CONF_DIR.mkdir(mode=0o700, exist_ok=True)
    for path in [CONF_FILE, NEUROHUB_ENV]:
        try:
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            lines = [f"GEMINI_API_KEY={key}\n"]
            path.write_text("".join(lines))
            os.chmod(path, 0o600)
            print(f"[SAVED] {path}")
        except Exception as e:
            print(f"[WARN] failed to save to {path}: {e}")

def show_info(key: str):
    masked = f"{key[:6]}...{key[-4:]}" if key else "[未設定]"
    print(f"GEMINI_API_KEY = {masked}")
    if key:
        print(f"export GEMINI_API_KEY={key}")
    print("===============================\n")

def check_api():
    """キーをロード→検証→必要なら更新"""
    print(AI_STUDIO_URL)
    key = load_key()

    if not key:
        print("[WARN] APIキーが設定されていません。")
    else:
        ok, code, body = test_key(key)
        if ok:
            print(f"[OK] 現在のAPIキーで {code} 応答確認")
            show_info(key)
            print("[DONE]")
            return True
        else:
            print(f"[WARN] 現在のAPIキーでは code={code}")
            print(body[:200])

    print("GEMINI_API_KEY（ここに貼り付け）:")
    new_key = sys.stdin.readline().strip()
    if not new_key:
        print("[ERROR] 空のキーです。")
        return False

    ok, code, body = test_key(new_key)
    if ok:
        save_key(new_key)
        show_info(new_key)
        print("[DONE]")
        return True
    else:
        print(f"[ERROR] 入力キー検証失敗 code={code}")
        print(body[:300])
        return False

if __name__ == "__main__":
    sys.exit(0 if check_api() else 1)
