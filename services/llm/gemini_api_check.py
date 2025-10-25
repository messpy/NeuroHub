#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini APIキー検証スクリプト（ライブラリ兼CLI）
https://aistudio.google.com/api-keys

■ ポイント
- パスはハードコードしない：
  1) 環境変数 NEUROHUB_CONFIG（configディレクトリへの絶対パス）
  2) 環境変数 NEUROHUB_ROOT（その直下の config/ を使う）
  3) スクリプト位置から親に辿って config/config.yaml を探索
  4) 最後の手段として CWD からも探索
- YAML（config/config.yaml）が見つかれば gemini.api_url / gemini.model を取得
- .env は 見つかった config/.env を最優先、無ければ ~/.gemini/.env
- --prompt 未指定なら "hello"
- ライブラリ関数 test_key(...) は (ok, status, body, reply_text) を返します
"""

import os, sys, json
from pathlib import Path
from typing import Optional, Tuple

# 依存
try:
    import requests
except Exception:
    print("[ERROR] requests が必要です: pip install requests", file=sys.stderr)
    sys.exit(2)

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # PyYAML無しでも最低限動く

DEFAULTS = {
    "api_url": "https://generativelanguage.googleapis.com/v1",
    "model": "gemini-2.5-flash",
}

# ----------------- config ディレクトリ探索 -----------------
def _find_config_dir() -> Optional[Path]:
    # 明示渡し（最優先）
    env_conf = os.environ.get("NEUROHUB_CONFIG")
    if env_conf:
        p = Path(env_conf).expanduser().resolve()
        if p.is_dir():
            return p

    # ルート→config
    env_root = os.environ.get("NEUROHUB_ROOT")
    if env_root:
        p = Path(env_root).expanduser().resolve() / "config"
        if p.is_dir():
            return p

    # このファイルの親から上方探索
    here = Path(__file__).resolve()
    for base in [here.parent, *here.parents]:
        cand = base / "config"
        if (cand / "config.yaml").exists():
            return cand

    # CWD からも一応
    cwd = Path.cwd()
    for base in [cwd, *cwd.parents]:
        cand = base / "config"
        if (cand / "config.yaml").exists():
            return cand

    return None

# ----------------- 小ユーティリティ -----------------
def _read_env_file(path: Path) -> dict:
    env = {}
    if not path or not path.exists():
        return env
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        env[k.strip()] = v.strip()
    return env

def _extract_text_from_body(body: str) -> Optional[str]:
    try:
        data = json.loads(body)
    except Exception:
        return None
    try:
        cands = data.get("candidates") or []
        if not cands:
            return None
        parts = (cands[0].get("content") or {}).get("parts") or []
        texts = [p.get("text") for p in parts if isinstance(p, dict) and p.get("text")]
        return "".join(texts) if texts else None
    except Exception:
        return None

# ----------------- 公開関数 -----------------
def load_key(conf_dir: Optional[Path] = None) -> Optional[str]:
    """
    GEMINI_API_KEY を取得。
    優先順: 環境変数 → config/.env → ~/.gemini/.env
    """
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()

    if conf_dir:
        key = _read_env_file(conf_dir / ".env").get("GEMINI_API_KEY")
        if key:
            return key.strip()

    home_key = _read_env_file(Path.home() / ".gemini/.env").get("GEMINI_API_KEY")
    return home_key.strip() if home_key else None

def load_cfg(conf_dir: Optional[Path] = None) -> dict:
    """
    config.yaml（見つかった場合）→ 環境変数（GEMINI_API_URL / GEMINI_MODEL）→ デフォルト
    """
    api_url = DEFAULTS["api_url"]
    model   = DEFAULTS["model"]

    if conf_dir and (conf_dir / "config.yaml").exists() and yaml:
        try:
            y = yaml.safe_load((conf_dir / "config.yaml").read_text(encoding="utf-8"))
            if isinstance(y, dict):
                llm = (y.get("llm") or {})
                gem = (llm.get("gemini") or {})
                if gem.get("api_url"): api_url = str(gem["api_url"]).strip()
                if gem.get("model"):   model   = str(gem["model"]).strip()
        except Exception as e:
            print(f"[WARN] config.yaml 読み込み失敗: {e}", file=sys.stderr)

    if os.environ.get("GEMINI_API_URL"):
        api_url = os.environ["GEMINI_API_URL"].strip()
    if os.environ.get("GEMINI_MODEL"):
        model   = os.environ["GEMINI_MODEL"].strip()

    return {"api_url": api_url, "model": model}

def test_key(api_url: str, model: str, key: str, text: str = "hello", timeout: int = 10) -> Tuple[bool, int, str, Optional[str]]:
    """
    実リクエスト。
    戻り値: (ok, status, body, reply_text)
    - ok: status==200 かつ "candidates" を含む
    - reply_text: 抜き出した最初のテキスト（なければ None）
    """
    url = f"{api_url.rstrip('/')}/models/{model}:generateContent?key={key}"
    payload = {"contents":[{"parts":[{"text": text}]}]}
    try:
        r = requests.post(url, headers={"Content-Type": "application/json"},
                          data=json.dumps(payload), timeout=timeout)
        body = r.text
        ok = (r.status_code == 200) and ("candidates" in body)
        reply = _extract_text_from_body(body)
        return ok, r.status_code, body, reply
    except Exception as e:
        return False, 0, str(e), None

# ----------------- CLI -----------------
def _main():
    import argparse
    ap = argparse.ArgumentParser(description="Gemini API キー検証（config探索版）")
    ap.add_argument("--prompt", "-p", default="hello", help="テスト送信プロンプト（既定: hello）")
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    conf_dir = _find_config_dir()
    key = load_key(conf_dir)
    cfg = load_cfg(conf_dir)

    if args.debug:
        print(f"[debug] conf_dir={conf_dir}", file=sys.stderr)
        print(f"[debug] api_url={cfg['api_url']} model={cfg['model']} has_key={bool(key)}", file=sys.stderr)

    if not key:
        print("[WARN] GEMINI_API_KEY が見つかりません。")
        return 1

    ok, code, body, reply = test_key(cfg["api_url"], cfg["model"], key, text=args.prompt, timeout=args.timeout)
    print(f"[RESULT] status={code}")
    if reply:
        print(f"[REPLY] {reply}")
    else:
        print(body[:400])

    return 0 if ok else 2

if __name__ == "__main__":
    sys.exit(_main())
