#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Utils — config連携 & /chat + /generate 両対応
- config/config.yaml / .env / 環境変数 から host/model を自動取得
- /api/chat の message.content と /api/generate の response 両対応
- stream安全化（bytes対応）
"""

from __future__ import annotations
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import requests

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


# ================================
# Config 読み込み
# ================================
def _find_config_dir() -> Optional[Path]:
    """NeuroHub/config ディレクトリ探索（環境変数優先 → 祖先探索 → CWD探索）"""
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
    """KEY=VALUE 形式の .env 読み込み"""
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


def load_ollama_config() -> Dict[str, str]:
    """YAML / .env / 環境変数から host/model を抽出（優先度: YAML → .env → env → 既定）"""
    host = "http://127.0.0.1:11434"
    model = ""

    conf_dir = _find_config_dir()
    if conf_dir and (conf_dir / "config.yaml").exists() and yaml:
        try:
            y = yaml.safe_load((conf_dir / "config.yaml").read_text(encoding="utf-8"))
            if isinstance(y, dict):
                llm = (y.get("llm") or {})
                ola = (llm.get("ollama") or {})
                if ola.get("host"):
                    host = str(ola["host"]).strip()
                sel = str(ola.get("selected_model") or "").strip()
                if sel:
                    model = sel
                else:
                    models = ola.get("models") or []
                    if isinstance(models, list) and models:
                        model = str(models[0]).strip()
        except Exception as e:
            print(f"[WARN] config.yaml 読み込み失敗: {e}", file=sys.stderr)

    if conf_dir:
        envf = conf_dir / ".env"
        if envf.exists():
            env_local = _read_env_file(envf)
            if env_local.get("OLLAMA_HOST"):
                host = env_local["OLLAMA_HOST"].strip()

    if os.environ.get("OLLAMA_HOST"):
        host = os.environ["OLLAMA_HOST"].strip()

    return {"host": host, "model": model}


# ================================
# Ollama 呼び出し
# ================================
def _normalize_host(host: str) -> str:
    h = (host or "").strip()
    if not h:
        raise RuntimeError("OLLAMA_HOST が空です。例: http://127.0.0.1:11434")
    if h.startswith(("http://", "https://")):
        return h.rstrip("/")
    return "http://" + h.rstrip("/")


def _consume_piece(obj: Any) -> str:
    """ストリームJSON 1行からテキスト片を抽出"""
    if not isinstance(obj, dict):
        return ""
    if isinstance(obj.get("response"), str):
        return obj["response"]
    msg = obj.get("message") or {}
    if isinstance(msg, dict) and isinstance(msg.get("content"), str):
        return msg["content"]
    return ""


def _stream_json_lines(response: requests.Response):
    """requests Response から安全に JSONL を読む（bytes対応版）"""
    buf = ""
    for chunk in response.iter_content(chunk_size=None, decode_unicode=False):
        if not chunk:
            continue
        # bytes → str に安全変換
        if isinstance(chunk, bytes):
            chunk = chunk.decode("utf-8", errors="ignore")
        buf += chunk
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue
    tail = buf.strip()
    if tail:
        try:
            yield json.loads(tail)
        except json.JSONDecodeError:
            pass


def _chat_request(
    host: str,
    model: str,
    prompt: str,
    *,
    system: Optional[str],
    options: Optional[Dict[str, Any]],
    keep_alive: Optional[str],
    timeout: int,
    debug: bool,
) -> requests.Response:
    """ /api/chat を叩く """
    url = _normalize_host(host) + "/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            *( [{"role": "system", "content": system}] if system else [] ),
            {"role": "user", "content": prompt},
        ],
        "stream": True,
    }
    if options:
        payload["options"] = options
    if keep_alive:
        payload["keep_alive"] = keep_alive

    if debug:
        print(f"[debug] POST {url} model={model} stream=True", file=sys.stderr)

    try:
        r = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            stream=True,
            timeout=timeout,
        )
    except Exception as e:
        raise RuntimeError(f"Ollama 接続エラー: {e}")
    return r


def ollama_generate(
    host: Optional[str] = None,
    model: Optional[str] = None,
    prompt: str = "",
    *,
    stream: bool = False,
    options: Optional[Dict[str, Any]] = None,
    keep_alive: Optional[str] = "5m",
    timeout: int = 120,
    debug: bool = False,
) -> None:
    """ /api/generate を叩く """
    conf = load_ollama_config()
    host = host or conf["host"]
    model = model or conf["model"]
    if not model:
        raise RuntimeError("Ollama モデルが未設定です。")

    url = _normalize_host(host) + "/api/generate"
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": True,
    }
    if options:
        payload["options"] = options
    if keep_alive:
        payload["keep_alive"] = keep_alive

    if debug:
        print(f"[debug] POST {url} model={model} stream=True", file=sys.stderr)

    try:
        r = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            stream=True,
            timeout=timeout,
        )
    except Exception as e:
        raise RuntimeError(f"Ollama 接続エラー: {e}")

    if r.status_code != 200:
        raise RuntimeError(f"Ollama 応答エラー: HTTP {r.status_code} {r.text[:400]}")

    if stream:
        got_any = False
        for obj in _stream_json_lines(r):
            piece = str(obj.get("response") or "")
            if piece:
                got_any = True
                print(piece, end="", flush=True)
        print()
        if not got_any:
            print("[empty response]")
    else:
        out: list[str] = []
        for obj in _stream_json_lines(r):
            piece = str(obj.get("response") or "")
            if piece:
                out.append(piece)
        txt = "".join(out).strip()
        print(txt if txt else "[empty response]")


def ollama_chat(
    host: Optional[str] = None,
    model: Optional[str] = None,
    prompt: str = "",
    *,
    stream: bool = False,
    system: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    keep_alive: Optional[str] = "5m",
    timeout: int = 120,
    debug: bool = False,
) -> None:
    """ Ollama にチャット問い合わせして標準出力に結果を出す """
    conf = load_ollama_config()
    host = host or conf["host"]
    model = model or conf["model"]
    if not model:
        raise RuntimeError("Ollama モデルが未設定です。")

    r = _chat_request(
        host=host,
        model=model,
        prompt=prompt,
        system=system,
        options=options,
        keep_alive=keep_alive,
        timeout=timeout,
        debug=debug,
    )

    if r.status_code != 200:
        raise RuntimeError(f"Ollama 応答エラー: HTTP {r.status_code} {r.text[:400]}")

    if stream:
        got_any = False
        for obj in _stream_json_lines(r):
            piece = _consume_piece(obj)
            if piece:
                got_any = True
                print(piece, end="", flush=True)
        print()
        if not got_any:
            if debug:
                print("[debug] chat had no text → fallback to /api/generate", file=sys.stderr)
            ollama_generate(host=host, model=model, prompt=prompt, stream=True)
        return
    else:
        buf: list[str] = []
        for obj in _stream_json_lines(r):
            piece = _consume_piece(obj)
            if piece:
                buf.append(piece)
        text = "".join(buf).strip()
        if text:
            print(text)
        else:
            if debug:
                print("[debug] chat had no text → fallback to /api/generate", file=sys.stderr)
            ollama_generate(host=host, model=model, prompt=prompt, stream=False)


# ================================
# CLI エントリ
# ================================
def _parse_kv_pairs(pairs: list[str] | None) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not pairs:
        return out
    for s in pairs:
        if "=" in s:
            k, v = s.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Ollama chat CLI（config連携）")
    ap.add_argument("prompt", nargs="+", help="ユーザープロンプト（スペース可）")
    ap.add_argument("--host", help="Ollama ホスト（未指定なら config/.env）")
    ap.add_argument("--model", help="Ollama モデル（未指定なら config.yaml）")
    ap.add_argument("--system", help="system プロンプト")
    ap.add_argument("--opt", action="append", help="オプション key=val（複数可）")
    ap.add_argument("--keep-alive", default="5m")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--no-stream", action="store_true", help="逐次表示を行わず、最後にまとめて表示")
    args = ap.parse_args()

    prompt = " ".join(args.prompt).strip()
    options = _parse_kv_pairs(args.opt)

    try:
        ollama_chat(
            host=args.host or None,
            model=args.model or None,
            prompt=prompt,
            stream=(not args.no_stream),
            system=args.system or None,
            options=options or None,
            keep_alive=args.keep_alive,
            timeout=args.timeout,
            debug=args.debug,
        )
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
