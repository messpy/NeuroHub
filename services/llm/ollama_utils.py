#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Utils — config連携 & /chat + /generate 両対応 + サーバ自動起動
- config/config.yaml / .env / 環境変数 から host/model を自動取得
- /api/chat の message.content と /api/generate の response 両対応
- stream安全化（bytes対応）
- サーバ未起動時は ollama serve を自動起動して待機
- embedモデル誤指定時の自動回避、HTTP400の本文を見て自動フォールバック
"""

from __future__ import annotations
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import subprocess
import time
import re

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
# サーバ確保（未起動なら起動）
# ================================
def _normalize_host(host: str) -> str:
    h = (host or "").strip()
    if not h:
        raise RuntimeError("OLLAMA_HOST が空です。例: http://127.0.0.1:11434")
    if h.startswith(("http://", "https://")):
        return h.rstrip("/")
    return "http://" + h.rstrip("/")


def _http_ok(url: str, timeout: float = 1.0) -> bool:
    try:
        r = requests.get(url, timeout=timeout)
        return (r.status_code == 200)
    except Exception:
        return False


def ensure_ollama_running(host: str, *, use_systemd: bool = False, debug: bool = False) -> bool:
    """
    Ollamaサーバが応答しない場合に起動を試み、最大10秒待って可否を返す。
    - host: "http://127.0.0.1:11434" など
    - use_systemd: systemd管理なら True（--user start ollama）
    """
    base = _normalize_host(host)
    ver_url = base + "/api/version"

    # 1) 既に生存していればOK
    if _http_ok(ver_url, timeout=1.0):
        if debug:
            print(f"[debug] ollama alive: {ver_url}", file=sys.stderr)
        return True

    # 2) 起動試行
    if use_systemd:
        cmd = ["systemctl", "--user", "start", "ollama"]
        if debug:
            print(f"[debug] start via systemd: {' '.join(cmd)}", file=sys.stderr)
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception as e:
            print(f"[warn] systemd 起動失敗: {e}", file=sys.stderr)
    else:
        # デーモン化（前面に出さずバックグラウンド）
        cmd = ["ollama", "serve"]
        if debug:
            print(f"[debug] start via subprocess: {' '.join(cmd)}", file=sys.stderr)
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[error] ollama serve 起動失敗: {e}", file=sys.stderr)
            return False

    # 3) 起動待機（最大10秒、0.5秒ステップ）
    for _ in range(20):
        time.sleep(0.5)
        if _http_ok(ver_url, timeout=0.6):
            if debug:
                print("[debug] ollama サーバ起動完了", file=sys.stderr)
            return True

    print("[error] ollama サーバ起動を確認できませんでした（10秒タイムアウト）", file=sys.stderr)
    return False


# ================================
# ヘルパ
# ================================
_EMBED_HINT = re.compile(r"(embed|embedding|text-embedding)", re.I)

def _looks_embed_model(name: str) -> bool:
    return bool(name and _EMBED_HINT.search(name))

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


# ================================
# コア: テキスト返却
# ================================
def _run_generate(
    host: str,
    model: str,
    prompt: str,
    *,
    options: Optional[Dict[str, Any]],
    keep_alive: Optional[str],
    timeout: int,
    debug: bool,
) -> Tuple[bool, str]:
    url = _normalize_host(host) + "/api/generate"
    payload: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": True}
    if options:
        payload["options"] = options
    if keep_alive:
        payload["keep_alive"] = keep_alive
    if debug:
        print(f"[debug] POST {url} model={model} stream=True", file=sys.stderr)
    rr = requests.post(url, headers={"Content-Type":"application/json"},
                       data=json.dumps(payload), stream=True, timeout=timeout)
    if rr.status_code != 200:
        return False, ""
    g_pieces: list[str] = []
    for obj in _stream_json_lines(rr):
        p = str(obj.get("response") or "")
        if p:
            g_pieces.append(p)
    text = "".join(g_pieces).strip()
    return (len(text) > 0), text


def ollama_chat_text(
    host: Optional[str] = None,
    model: Optional[str] = None,
    prompt: str = "",
    *,
    system: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    keep_alive: Optional[str] = "5m",
    timeout: int = 120,
    debug: bool = False,
    mode: str = "auto",  # "auto" | "chat" | "generate"
) -> Tuple[bool, str]:
    """
    Ollama を叩いて「成功フラグ, 本文」を返す。
      - mode="auto": まず /api/chat、ダメなら /api/generate へ
      - mode="chat": /api/chat 固定
      - mode="generate": /api/generate 固定
    """
    conf = load_ollama_config()
    host = host or conf["host"]
    model = model or conf["model"]

    if not model:
        # 最低限の既定（チャット寄り）
        model = os.environ.get("OLLAMA_CHAT_MODEL", "llama3.2:1b-instruct")

    # サーバ自動起動
    if not ensure_ollama_running(host, debug=debug):
        return False, ""

    # embed系が来たときはチャット既定に差し替え（auto & chat時）
    if mode in ("auto", "chat") and _looks_embed_model(model):
        if debug:
            print(f"[debug] embed-like model '{model}' -> switch to chat model", file=sys.stderr)
        model = os.environ.get("OLLAMA_CHAT_MODEL", "llama3.2:1b-instruct")

    if mode == "generate":
        return _run_generate(host, model, prompt, options=options, keep_alive=keep_alive, timeout=timeout, debug=debug)

    # まず /api/chat
    try:
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
    except Exception as e:
        if debug:
            print(f"[debug] ollama_chat_text connect error: {e}", file=sys.stderr)
        # auto の場合は generate へ
        if mode == "auto":
            return _run_generate(host, model, prompt, options=options, keep_alive=keep_alive, timeout=timeout, debug=debug)
        return False, ""

    if r.status_code != 200:
        # 400 などでも本文を見て「チャット非対応」なら generate へ
        if mode == "auto":
            try:
                body = r.text
            except Exception:
                body = ""
            if ("does not support chat" in body) or ("not support chat" in body) or ("unsupported" in body.lower()):
                if debug:
                    print(f"[debug] chat -> generate fallback due to: {body[:200]}", file=sys.stderr)
                return _run_generate(host, model, prompt, options=options, keep_alive=keep_alive, timeout=timeout, debug=debug)
        if debug:
            print(f"[debug] ollama_chat_text HTTP {r.status_code}", file=sys.stderr)
        return False, ""

    pieces: list[str] = []
    for obj in _stream_json_lines(r):
        piece = _consume_piece(obj)
        if piece:
            pieces.append(piece)
    text = "".join(pieces).strip()

    # /api/chat が空なら /api/generate にフォールバック（auto時）
    if not text and mode == "auto":
        if debug:
            print(f"[debug] empty chat -> fallback to /api/generate", file=sys.stderr)
        return _run_generate(host, model, prompt, options=options, keep_alive=keep_alive, timeout=timeout, debug=debug)

    return (len(text) > 0), text


# ================================
# CLI互換関数（既存用途保持）
# ================================
def ollama_chat(
    host: Optional[str] = None,
    model: Optional[str] = None,
    prompt: str = "",
    *,
    stream: bool = False,  # 互換用（未使用）
    system: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    keep_alive: Optional[str] = "5m",
    timeout: int = 120,
    debug: bool = False,
    mode: str = "auto",
) -> None:
    """CLI表示用: /api/chat -> 必要に応じて generate へ自動フォールバック"""
    ok, text = ollama_chat_text(
        host=host,
        model=model,
        prompt=prompt,
        system=system,
        options=options,
        keep_alive=keep_alive,
        timeout=timeout,
        debug=debug,
        mode=mode,
    )
    print(text if ok else "[empty response]")


# ================================
# CLIエントリ
# ================================
def main() -> int:
    ap = argparse.ArgumentParser(description="Ollama chat CLI（config連携・自動起動）")
    ap.add_argument("prompt", nargs="+", help="ユーザープロンプト（スペース可）")
    ap.add_argument("--host", help="Ollama ホスト（未指定なら config/.env）")
    ap.add_argument("--model", help="Ollama モデル（未指定なら config.yaml）")
    ap.add_argument("--system", help="system プロンプト")
    ap.add_argument("--opt", action="append", help="オプション key=val（複数可）")
    ap.add_argument("--keep-alive", default="5m")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--systemd", action="store_true", help="systemd(--user)で起動を試みる")
    ap.add_argument("--mode", choices=["auto", "chat", "generate"], default="auto",
                    help="auto: まずchat、失敗/空ならgenerateに自動切替")
    args = ap.parse_args()

    # サーバ自動起動（hostの決定を先に）
    cfg = load_ollama_config()
    host_cfg = args.host or cfg["host"]
    if not ensure_ollama_running(host_cfg, use_systemd=args.systemd, debug=args.debug):
        print("[error] ollama サーバを起動できませんでした", file=sys.stderr)
        return 3

    prompt = " ".join(args.prompt).strip()

    options = {}
    if args.opt:
        for s in args.opt:
            if "=" in s:
                k, v = s.split("=", 1)
                options[k.strip()] = v.strip()

    ok, text = ollama_chat_text(
        host=args.host,
        model=args.model,
        prompt=prompt,
        system=args.system,
        options=options or None,
        keep_alive=args.keep_alive,
        timeout=args.timeout,
        debug=args.debug,
        mode=args.mode,
    )
    print(text if ok else "[empty response]")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
