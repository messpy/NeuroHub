#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Manager（Gemini→Ollama ゲート）
- パスはハードコードしない。config探索で yaml/.env を取得
- ルール: Gemini の応答が 404 以外なら Ollama 実行（キー無しも実行）
"""

import os, sys, json, argparse
from pathlib import Path
from typing import Optional

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from gemini_api_check import test_key as gem_test_key, load_key as gem_load_key, load_cfg as gem_load_cfg
from ollama_utils import ollama_chat

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

DEFAULTS = {
    "gemini_api_url": "https://generativelanguage.googleapis.com/v1",
    "gemini_model":   "gemini-2.5-flash",
    "ollama_host":    "http://127.0.0.1:11434",
    "ollama_model":   None,
}

# --------- config探索 ----------
def _find_config_dir() -> Optional[Path]:
    env_conf = os.environ.get("NEUROHUB_CONFIG")
    if env_conf:
        p = Path(env_conf).expanduser().resolve()
        if p.is_dir():
            return p

    env_root = os.environ.get("NEUROHUB_ROOT")
    if env_root:
        p = Path(env_root).expanduser().resolve() / "config"
        if p.is_dir():
            return p

    here = Path(__file__).resolve()
    for base in [here.parent, *here.parents]:
        cand = base / "config"
        if (cand / "config.yaml").exists():
            return cand

    cwd = Path.cwd()
    for base in [cwd, *cwd.parents]:
        cand = base / "config"
        if (cand / "config.yaml").exists():
            return cand

    return None

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

def load_all_config():
    """
    最終設定を返す。優先順：
    1) YAML（見つかれば） 2) .env の OLLAMA_HOST 3) 環境変数 4) デフォルト
    Gemini の api_url/model は gemini_api_check.load_cfg にも委譲
    """
    conf_dir = _find_config_dir()
    cfg = dict(DEFAULTS)

    # --- Gemini 側（api_url/model）は check 側の実装も尊重 ---
    gcfg = gem_load_cfg(conf_dir)
    cfg["gemini_api_url"] = gcfg["api_url"]
    cfg["gemini_model"]   = gcfg["model"]

    # --- Ollama 側：YAML 優先 ---
    if conf_dir and (conf_dir / "config.yaml").exists() and yaml:
        try:
            y = yaml.safe_load((conf_dir / "config.yaml").read_text(encoding="utf-8"))
            if isinstance(y, dict):
                llm = (y.get("llm") or {})
                ola = (llm.get("ollama") or {})
                if ola.get("host"):
                    cfg["ollama_host"] = str(ola["host"]).strip()
                sel = str(ola.get("selected_model") or "").strip()
                if sel:
                    cfg["ollama_model"] = sel
                else:
                    models = ola.get("models") or []
                    if isinstance(models, list) and models:
                        cfg["ollama_model"] = str(models[0]).strip()
        except Exception as e:
            print(f"[WARN] config.yaml 読み込み失敗: {e}", file=sys.stderr)

    # --- .env の OLLAMA_HOST（上書き可） ---
    if conf_dir:
        env_local = _read_env_file(conf_dir / ".env")
        if env_local.get("OLLAMA_HOST"):
            cfg["ollama_host"] = env_local["OLLAMA_HOST"].strip()

    # --- 環境変数最優先（必要なら） ---
    if os.environ.get("OLLAMA_HOST"):
        cfg["ollama_host"] = os.environ["OLLAMA_HOST"].strip()

    # --- Gemini Key ---
    cfg["gemini_api_key"] = gem_load_key(conf_dir)

    return cfg

def main():
    ap = argparse.ArgumentParser(description="NeuroHub LLM Manager（Gemini→Ollama）")
    ap.add_argument("-p","--prompt", required=True, help="Ollama へ送るプロンプト")
    ap.add_argument("--stream", action="store_true", help="Ollama 出力を逐次表示")
    ap.add_argument("--ollama-model", help="Ollama モデル（未指定時は YAML/.env から）")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_all_config()

    if args.debug:
        print("[debug] config:", json.dumps({
            "conf_dir":        str(_find_config_dir()),
            "gemini_api_url":  cfg["gemini_api_url"],
            "gemini_model":    cfg["gemini_model"],
            "has_gemini_key":  bool(cfg["gemini_api_key"]),
            "ollama_host":     cfg["ollama_host"],
            "ollama_model":    args.ollama_model or cfg["ollama_model"],
        }, ensure_ascii=False, indent=2), file=sys.stderr)

    # --- Gate: Gemini の応答が 404 以外なら Ollama 実行（キー無しも実行） ---
    if cfg["gemini_api_key"]:
        ok, status, body, reply = gem_test_key(cfg["gemini_api_url"], cfg["gemini_model"], cfg["gemini_api_key"], text="hello")
        if status == 404:
            print("[INFO] Gemini 応答 404（モデル/権限なし）→ Ollama 実行をスキップします。", file=sys.stderr)
            if args.debug:
                print((reply or body)[:600], file=sys.stderr)
            return 4
        elif ok:
            print("[OK] Gemini 疎通 200 → Ollama 実行へ", file=sys.stderr)
        else:
            print(f"[WARN] Gemini 応答 code={status}（404以外）→ ポリシーにより Ollama 実行へ", file=sys.stderr)
            if args.debug:
                print((reply or body)[:600], file=sys.stderr)
    else:
        print("[WARN] GEMINI_API_KEY 不在 → ポリシーにより Ollama 実行へ", file=sys.stderr)

    if args.dry_run:
        print("[DRY-RUN] 判定のみで終了（Ollama未実行）")
        return 0

    # --- Ollama 実行 ---
    ola_model = args.ollama_model or cfg["ollama_model"]
    if not ola_model:
        print("[ERROR] Ollama モデル名が未設定です（config.llm.ollama.selected_model か --ollama-model を指定）。", file=sys.stderr)
        return 5

    try:
        ollama_chat(cfg["ollama_host"], ola_model, args.prompt, stream=args.stream, debug=args.debug)
        return 0
    except Exception as e:
        print(f"[ERROR] Ollama error: {e}", file=sys.stderr)
        return 7

if __name__ == "__main__":
    sys.exit(main())
