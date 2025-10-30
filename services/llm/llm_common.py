#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/llm/llm_common.py
- 共通ユーティリティ: .env ロード / config.yaml ロード / Ollamaヘルスチェック
- 前提: .env はプロジェクト直下に配置する（例: ~/work/NeuroHub/.env）
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict

# プロジェクトルートを基点に固定
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
YAML_FILE = CONFIG_DIR / "config.yaml"
ENV_FILE = PROJECT_ROOT / ".env"


# ==========================================================
# .env ロード
# ==========================================================
def load_env_from_config(debug: bool = False) -> None:
    """
    プロジェクト直下 (.env) を読み込むだけの最小実装。
    例: ~/work/NeuroHub/.env
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        if debug:
            print("[llm_common] python-dotenv 未インストール。環境読み込みスキップ。", flush=True)
        return

    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
        if debug:
            print(f"[llm_common] loaded .env: {ENV_FILE}", flush=True)
    else:
        if debug:
            print(f"[llm_common] .env not found: {ENV_FILE}", flush=True)


# ==========================================================
# config.yaml ロード
# ==========================================================
def load_config(path: Path | None = None) -> Dict[str, Any]:
    """config/config.yaml を辞書で返す（無ければ {}）。"""
    import yaml
    p = Path(path) if path else YAML_FILE
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[llm_common] warn: failed to read yaml: {e}", flush=True)
        return {}


# ==========================================================
# Ollama /api/version チェック
# ==========================================================
def ensure_ollama_running(host: str) -> bool:
    """Ollama /api/version が 200 を返せば True。"""
    import urllib.request
    url = f"{host.rstrip('/')}/api/version"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


# ==========================================================
# デバッグ用最小ロガー
# ==========================================================
class DebugLogger:
    """極小デバッガ（stderr出力）。enabled=False なら無動作。"""
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    def dbg(self, *args) -> None:
        if self.enabled:
            try:
                import sys
                out = " ".join(str(a) for a in args)
                print(f"[debug] {out}", file=sys.stderr)
            except Exception:
                pass


# ==========================================================
# モデル名取得
# ==========================================================
def get_llm_model_from_config(cfg: Dict[str, Any], provider: str, default_model: str) -> str:
    """
    config.yaml の llm.<provider>.model を返す（なければ default_model）。
    例:
      llm:
        gemini:
          model: gemini-2.5-flash
    """
    try:
        node = (cfg or {}).get("llm", {}).get(provider, {})
        model = node.get("model") or default_model
        return str(model)
    except Exception:
        return default_model
