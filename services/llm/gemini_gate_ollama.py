#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gemini_gate_ollama.py
- 役割: Gemini API で疎通チェック → 成功（≠404）なら Ollama にプロンプトを実行
- 参照設定:
    - ~/NeuroHub/config/config.yaml （存在すれば）
    - ~/NeuroHub/config/.env       （存在すれば）
    - ~/.gemini/.env               （存在すれば）
    - 環境変数 GEMINI_API_KEY / OLLAMA_HOST
- 依存: requests（標準外）。PyYAML はあれば使う、無ければフォールバック。
"""

import os, sys, json, argparse, time
from pathlib import Path

# --------- 依存の軽量ロード ---------
try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # PyYAML 無しでも動くように

try:
    import requests
except Exception as e:
    print("[ERROR] requests が必要です: pip install requests", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[2]  # NeuroHub/
CONF_DIR = ROOT / "config"
CONF_YAML = CONF_DIR / "config.yaml"
CONF_ENV  = CONF_DIR / ".env"
GEMINI_HOME_ENV = Path.home() / ".gemini/.env"

DEFAULTS = {
    "gemini_api_url": "https://generativelanguage.googleapis.com/v1",  # v1固定
    "gemini_model": "gemini-2.5-flash",
    "ollama_host": "http://127.0.0.1:11434",
    "ollama_model": None,  # 設定から拾う。無ければ API から推測 or エラー
}

# --------- .env / yaml ロード ---------
def read_env_file(path: Path) -> dict:
    env = {}
    if not path.exists(): return env
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s: continue
        k, v = s.split("=", 1)
        env[k.strip()] = v.strip()
    return env

def load_config():
    cfg = {
        "gemini_api_url": DEFAULTS["gemini_api_url"],
        "gemini_model": DEFAULTS["gemini_model"],
        "ollama_host": DEFAULTS["ollama_host"],
        "ollama_model": DEFAULTS["ollama_model"],
    }

    # YAML（あれば）
    if CONF_YAML.exists() and yaml:
        try:
            y = yaml.safe_load(CONF_YAML.read_text(encoding="utf-8"))
            if isinstance(y, dict):
                llm = (y.get("llm") or {})
                gem = (llm.get("gemini") or {})
                ola = (llm.get("ollama") or {})

                cfg["gemini_api_url"] = (gem.get("api_url") or cfg["gemini_api_url"]).strip()
                cfg["gemini_model"]   = (gem.get("model")   or cfg["gemini_model"]).strip()

                cfg["ollama_host"]  = (ola.get("host") or cfg["ollama_host"]).strip()
                sel = (ola.get("selected_model") or "").strip()
                if sel: cfg["ollama_model"] = sel
                else:
                    # models の先頭を採用（あれば）
                    models = ola.get("models") or []
                    if isinstance(models, list) and models:
                        cfg["ollama_model"] = str(models[0]).strip()
        except Exception as e:
            print(f"[WARN] config.yaml の読み込みに失敗: {e}", file=sys.stderr)

    # .env（NeuroHub）
    env_local = read_env_file(CONF_ENV)
    # ~/.gemini/.env
    env_global = read_env_file(GEMINI_HOME_ENV)

    # 環境変数で上書き
    gemini_key = os.environ.get("GEMINI_API_KEY") or env_local.get("GEMINI_API_KEY") or env_global.get("GEMINI_API_KEY")
    ollama_host = os.environ.get("OLLAMA_HOST") or env_local.get("OLLAMA_HOST")

    if gemini_key:
        cfg["gemini_api_key"] = gemini_key
    else:
        cfg["gemini_api_key"] = None

    if ollama_host:
        cfg["ollama_host"] = ollama_host

    return cfg

# --------- Gemini 疎通（generateContent で "こんにちは"）---------
def gemini_ping(api_base: str, model: str, api_key: str, debug: bool=False) -> tuple[bool, int, str]:
    """
    成功なら (True, status_code, response_text)
    404 以外（例: 200, 400, 401, 403, 500）の場合でも 'ゲート通過' とみなすかは呼び出し側で判断
    """
    url = f"{api_base.rstrip('/')}/models/{model}:generateContent?key={api_key}"
    payload = {"contents":[{"parts":[{"text":"こんにちは"}]}]}
    headers = {"Content-Type":"application/json"}
    if debug:
        print(f"[debug] GEMINI POST {url}", file=sys.stderr)
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return (r.status_code == 200 and "candidates" in r.text), r.status_code, r.text
    except Exception as e:
        return False, 0, str(e)

# --------- Ollama 実行（HTTP /api/chat）---------
def ollama_chat(host: str, model: str, prompt: str, stream: bool=False, debug: bool=False):
    """
    stream=False: 1レスポンスまとめて表示
    stream=True : チャンク逐次表示
    """
    url = host.rstrip("/") + "/api/chat"
    headers = {"Content-Type":"application/json"}
    payload = {
        "model": model,
        "messages": [{"role":"user","content":prompt}],
        "stream": stream
    }
    if debug:
        print(f"[debug] OLLAMA POST {url} model={model} stream={stream}", file=sys.stderr)

    with requests.post(url, headers=headers, data=json.dumps(payload), stream=stream, timeout=300) as r:
        r.raise_for_status()
        if not stream:
            data = r.json()
            # 形式: {"message":{"content":"..."}}
            msg = (data.get("message") or {}).get("content") or ""
            print(msg)
            return

        # stream=True の場合: NDJSON 的に1行ずつ
        for line in r.iter_lines(decode_unicode=True):
            if not line: continue
            try:
                obj = json.loads(line)
                delta = ((obj.get("message") or {}).get("content")) or obj.get("response") or ""
                if delta:
                    print(delta, end="", flush=True)
            except Exception:
                # 予期しない行はそのまま
                print(line, end="", flush=True)
        print()

# --------- CLI ---------
def main():
    ap = argparse.ArgumentParser(description="Gemini疎通OKならOllamaを実行するゲート")
    ap.add_argument("-p","--prompt", required=True, help="Ollama に投げるプロンプト")
    ap.add_argument("--stream", action="store_true", help="Ollama 出力を逐次表示")
    ap.add_argument("--gemini-api", help="Gemini API base (既定は v1)")
    ap.add_argument("--gemini-model", help="Gemini モデル（既定: gemini-2.5-flash）")
    ap.add_argument("--ollama-host", help="Ollama ホスト（http://127.0.0.1:11434 等）")
    ap.add_argument("--ollama-model", help="Ollama モデル名（config の selected_model が無い場合は必須）")
    ap.add_argument("--dry-run", action="store_true", help="実行せず判定と設定だけ表示")
    ap.add_argument("--debug", action="store_true", help="デバッグログ")
    args = ap.parse_args()

    cfg = load_config()

    gem_api = args.gemini_api or cfg.get("gemini_api_url") or DEFAULTS["gemini_api_url"]
    gem_mod = args.gemini_model or cfg.get("gemini_model") or DEFAULTS["gemini_model"]
    gem_key = cfg.get("gemini_api_key")

    ola_host = args.ollama_host or cfg.get("ollama_host") or DEFAULTS["ollama_host"]
    ola_model = args.ollama_model or cfg.get("ollama_model") or DEFAULTS["ollama_model"]

    if args.debug:
        print("[debug] config:", json.dumps({
            "gemini_api_url": gem_api,
            "gemini_model": gem_mod,
            "ollama_host": ola_host,
            "ollama_model": ola_model,
            "has_gemini_key": bool(gem_key),
        }, ensure_ascii=False, indent=2), file=sys.stderr)

    if not gem_key:
        print("[WARN] GEMINI_API_KEY が見つかりません。Gemini疎通チェックをスキップし、Ollamaを実行します。", file=sys.stderr)
        gate_pass = True
        status = -1
    else:
        ok, status, body = gemini_ping(gem_api, gem_mod, gem_key, debug=args.debug)
        if status == 404:
            print("[INFO] Gemini から 404（モデル/権限なし）。Ollama 実行はスキップします。", file=sys.stderr)
            if args.debug:
                print(body[:600], file=sys.stderr)
            return 4
        # “404以外は通す”ポリシー（要件どおり）
        gate_pass = True
        if ok:
            print(f"[OK] Gemini 応答確認 ({status})", file=sys.stderr)
        else:
            print(f"[WARN] Gemini 応答コード={status}（404以外）ですが、要件に従い Ollama 実行を継続します。", file=sys.stderr)
            if args.debug:
                print(body[:600], file=sys.stderr)

    if args.dry_run:
        print("[DRY-RUN] 判定のみで終了（Ollama未実行）")
        return 0

    if not ola_model:
        print("[ERROR] Ollama のモデル名が未設定です。--ollama-model か config.llm.ollama.selected_model を設定してください。", file=sys.stderr)
        return 5

    # Ollama 実行
    try:
        ollama_chat(ola_host, ola_model, args.prompt, stream=args.stream, debug=args.debug)
        return 0
    except requests.HTTPError as e:
        print(f"[ERROR] Ollama HTTPError: {e}", file=sys.stderr); return 6
    except Exception as e:
        print(f"[ERROR] Ollama error: {e}", file=sys.stderr); return 7

if __name__ == "__main__":
    sys.exit(main())
