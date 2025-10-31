#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
import os
import sys
import subprocess
import shlex
from pathlib import Path
from typing import Dict, Any, List
import urllib.request
import urllib.error

"""provider_ollama.py - Ollama LLM クライアント最小版

# 接続テスト
python provider_ollama.py --test --debug

# モデル一覧表示
python provider_ollama.py --list

# テキスト生成
python provider_ollama.py --model qwen2.5:1.5b-instruct --prompt "こんにちは"

# Modelfileからカスタムモデル作成
python provider_ollama.py --create my-assistant --modelfile my_modelfile.txt --debug


"""
# ===== llm_common から .env / config 読み込み =====
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from .llm_common import (
    load_env_from_config,
    load_config,
    get_llm_model_from_config,
    DebugLogger,
    LLMProviderConfig,
    make_api_request,
    LLMResponse,
    create_llm_response,
)

load_env_from_config()   # ~/work/NeuroHub/config/.env を反映

# ===== Ollama設定の共通化 =====
class OllamaConfig(LLMProviderConfig):
    def __init__(self, host: str = None, debug_logger: DebugLogger = None):
        super().__init__("ollama")
        # デバッグロガー設定
        self.debug_logger = debug_logger or DebugLogger(False)

        # 環境変数から設定を取得
        self.host = (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self.default_model = "qwen2.5:0.5b-instruct"

        # モデル優先順位: 環境変数 > config.yaml > 既定
        self.preferred_model = (
            os.getenv("OLLAMA_MODEL")
            or os.getenv("OLLAMA_TEST_MODEL")
            or self.get_model_from_config(self.default_model)
        )

        # フォールバックモデルを動的に取得
        self.fallback_models = self._get_fallback_models()
        self.current_model = None  # 実際に利用可能なモデル

        # サーバー確認と自動起動
        self._ensure_server_running()

    def _ensure_server_running(self) -> bool:
        """Ollamaサーバーが動いているか確認し、必要に応じて起動"""
        if ensure_ollama_running(self.host):
            self.debug_logger.dbg("Ollama server is already running")
            return True

        # ローカルホストの場合のみ自動起動を試行
        if "127.0.0.1" in self.host or "localhost" in self.host:
            self.debug_logger.dbg("Attempting to start Ollama server...")
            try:
                # バックグラウンドでOllamaサーバーを起動
                import subprocess
                import time

                # ollama serveコマンドをバックグラウンドで実行
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )

                # サーバー起動を待つ（最大10秒）
                for i in range(10):
                    time.sleep(1)
                    if ensure_ollama_running(self.host):
                        self.debug_logger.dbg(f"Ollama server started successfully after {i+1} seconds")
                        return True

                self.debug_logger.dbg("Ollama server failed to start within 10 seconds")
                return False

            except Exception as e:
                self.debug_logger.dbg(f"Failed to start Ollama server: {e}")
                return False
        else:
            self.debug_logger.dbg(f"Cannot auto-start server for remote host: {self.host}")
            return False

    def _get_fallback_models(self) -> List[str]:
        """ollama listから利用可能なモデルを取得してフォールバックモデルとして使用"""
        try:
            # まずサーバーが動いているか確認
            if not ensure_ollama_running(self.host):
                # サーバーが動いていない場合はデフォルトのフォールバック
                return [
                    "qwen2.5:0.5b-instruct",
                    "llama3.2:1b",
                    "qwen2.5:1.5b-instruct",
                    "phi4:latest",
                ]

            # ollama listを実行
            models = self._tags()
            if models:
                self.debug_logger.dbg(f"Found {len(models)} models from ollama list: {models}")
                return models
            else:
                # モデルがない場合は小さめのモデルをフォールバック
                return [
                    "qwen2.5:0.5b-instruct",
                    "llama3.2:1b",
                    "qwen2.5:1.5b-instruct",
                ]
        except Exception as e:
            self.debug_logger.dbg(f"Failed to get models from ollama list: {e}")
            return [
                "qwen2.5:0.5b-instruct",
                "llama3.2:1b",
                "qwen2.5:1.5b-instruct",
                "phi4:latest",
            ]

    def get_api_url(self, endpoint: str = "/api/generate") -> str:
        """API URLを生成"""
        return f"{self.host}{endpoint}"

    def is_configured(self) -> bool:
        """設定が有効かチェック（Ollamaは常にTrue、サーバーの生存確認は別途）"""
        return True

    def build_payload(self, text: str, opts: Dict[str, Any] = None, endpoint_type: str = "generate") -> Dict[str, Any]:
        """リクエストペイロードを構築"""
        if endpoint_type == "generate":
            payload = {
                "model": self.current_model or self.preferred_model,
                "prompt": text,
                "stream": False
            }
        else:  # chat
            payload = {
                "model": self.current_model or self.preferred_model,
                "messages": [{"role": "user", "content": text}],
                "stream": False
            }

        # オプション追加（temperature, top_p等）
        if opts:
            for key in ["temperature", "top_p", "top_k", "num_predict"]:
                if key in opts:
                    payload[key] = opts[key]

        return payload

    def _http_json(self, method: str, path: str, payload: dict | None = None, timeout: int = 120) -> dict:
        """HTTPリクエストを実行してJSONを返す"""
        url = f"{self.host}{path}"
        if payload is None:
            data = None
            headers = {}
        else:
            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            if not body:
                return {}
            return json.loads(body.decode("utf-8"))

    def _tags(self) -> List[str]:
        """ローカルにあるモデル名一覧（/api/tags）。"""
        try:
            obj = self._http_json("GET", "/api/tags", None, timeout=10)
            models = obj.get("models", []) if isinstance(obj, dict) else []
            names = []
            for m in models:
                n = (m or {}).get("name")
                if n:
                    names.append(str(n))
            return names
        except Exception:
            return []

    def _has_model_locally(self, name: str) -> bool:
        name = name.strip()
        existing = self._tags()
        if name in existing:
            return True
        # ":latest" 指定に対する簡易一致（ベース名一致）
        if name.endswith(":latest"):
            base = name.split(":")[0]
            return any(x.split(":")[0] == base for x in existing)
        return False

    def _pull(self, model: str, debug_logger: DebugLogger) -> bool:
        """`ollama pull <model>` を実行。成功で True。"""
        cmd = ["ollama", "pull", model]
        debug_logger.dbg("pull:", " ".join(shlex.quote(x) for x in cmd))
        try:
            p = subprocess.run(cmd, check=False, text=True, capture_output=True)
            debug_logger.dbg("pull.rc=", p.returncode, "out.len=", len(p.stdout), "err.len=", len(p.stderr))
            return p.returncode == 0
        except Exception as e:
            debug_logger.dbg("pull.error:", e)
            return False

    def test_connection(self) -> bool:
        """接続テスト（基底クラスメソッドの実装）"""
        try:
            version = self._http_json("GET", "/api/version", None, timeout=5)
            self.debug_logger.dbg("Ollama version:", version)
            models = self._tags()
            self.debug_logger.dbg(f"Available models count: {len(models)}")
            print(f"✅ 接続成功: Ollama は利用可能です (モデル数: {len(models)})")
            return True
        except Exception as e:
            self.debug_logger.dbg("Connection test failed:", str(e))
            print(f"❌ 接続失敗: {e}")
            return False

    def ensure_model_available(self, preferred: str = None) -> str:
        """
        1) preferred を優先（ローカル無ければ pull）
        2) ダメなら fallback_models を順に pull
        戻り値: 利用可能なモデル名（全滅なら例外）
        """
        candidates: List[str] = []
        if preferred:
            candidates.append(preferred)
        for m in self.fallback_models:
            if m not in candidates:
                candidates.append(m)

        for name in candidates:
            if self._has_model_locally(name):
                self.debug_logger.dbg("model exists:", name)
                self.current_model = name
                return name
            self.debug_logger.dbg("model missing:", name, " -> try pull")
            if self._pull(name, self.debug_logger) and self._has_model_locally(name):
                self.current_model = name
                return name

        raise RuntimeError("no available model (pull failed). Tried: " + ", ".join(candidates))

    def infer(self, prompt: str) -> LLMResponse:
        """
        /api/generate → 404/405 のとき /api/chat へフォールバック。
        戻り値はLLMResponseオブジェクト。
        """
        import time
        start_time = time.time()

        try:
            try:
                obj = self._http_json("POST", "/api/generate", {
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False
                })
                api_endpoint = "/api/generate"
            except urllib.error.HTTPError as e:
                if e.code not in (404, 405):
                    response_time = time.time() - start_time
                    return create_llm_response(
                        status_code=e.code,
                        provider="ollama",
                        model=self.current_model,
                        content="",
                        error=f"HTTP {e.code}: {e.reason}",
                        response_time=response_time,
                        request_url=f"{self.host}/api/generate",
                        metadata={"fallback_attempted": False}
                    )

                # フォールバック to /api/chat
                obj = self._http_json("POST", "/api/chat", {
                    "model": self.current_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                })
                api_endpoint = "/api/chat"

            response_time = time.time() - start_time
            content = ""

            # レスポンス解析
            if isinstance(obj, dict):
                if isinstance(obj.get("response"), str):
                    content = obj["response"].strip()
                elif isinstance(obj.get("message"), dict):
                    msg = obj.get("message", {})
                    if isinstance(msg.get("content"), str):
                        content = msg["content"].strip()
                else:
                    content = json.dumps(obj, ensure_ascii=False)
            else:
                content = json.dumps(obj, ensure_ascii=False)

            # トークン情報の抽出（利用可能な場合）
            tokens_input = obj.get("prompt_eval_count") if isinstance(obj, dict) else None
            tokens_output = obj.get("eval_count") if isinstance(obj, dict) else None
            tokens_total = None
            if tokens_input and tokens_output:
                tokens_total = tokens_input + tokens_output

            return create_llm_response(
                status_code=200,
                provider="ollama",
                model=self.current_model,
                content=content,
                response_time=response_time,
                tokens_used=tokens_total,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                request_url=f"{self.host}{api_endpoint}",
                raw_response=obj,
                metadata={
                    "api_endpoint": api_endpoint,
                    "fallback_used": api_endpoint == "/api/chat",
                    "ollama_host": self.host
                }
            )

        except Exception as e:
            response_time = time.time() - start_time
            return create_llm_response(
                status_code=500,
                provider="ollama",
                model=self.current_model,
                content="",
                error=f"Request failed: {str(e)}",
                response_time=response_time,
                request_url=f"{self.host}/api/generate",
                metadata={"exception_type": type(e).__name__}
            )

    def list_models(self, show_details: bool = False) -> List[Dict[str, Any]]:
        """ローカルモデル一覧を取得 (ollama list相当)"""
        try:
            obj = self._http_json("GET", "/api/tags", None, timeout=10)
            models = obj.get("models", []) if isinstance(obj, dict) else []

            if show_details:
                return models
            else:
                # 簡略表示用
                simple_list = []
                for m in models:
                    simple_list.append({
                        "name": m.get("name", ""),
                        "size": m.get("size", 0),
                        "modified_at": m.get("modified_at", ""),
                        "description": f"Local model ({m.get('size', 0)} bytes)"
                    })
                return simple_list
        except Exception:
            # サーバーにアクセスできない場合は空のリストを返す
            return []

    def pull_model(self, model_name: str, debug_logger: DebugLogger) -> bool:
        """モデルをプル (ollama pull相当)"""
        cmd = ["ollama", "pull", model_name]
        debug_logger.dbg("pull command:", " ".join(shlex.quote(x) for x in cmd))
        try:
            p = subprocess.run(cmd, check=False, text=True, capture_output=True)
            debug_logger.dbg("pull result:", f"rc={p.returncode}, stdout_len={len(p.stdout)}, stderr_len={len(p.stderr)}")
            if p.returncode == 0:
                debug_logger.dbg("pull success for:", model_name)
                return True
            else:
                debug_logger.dbg("pull failed:", p.stderr)
                return False
        except Exception as e:
            debug_logger.dbg("pull error:", str(e))
            return False

    def create_model_from_modelfile(self, model_name: str, modelfile_content: str,
                                  base_model: str = None, debug_logger: DebugLogger = None) -> bool:
        """
        Modelfileからカスタムモデルを作成

        Args:
            model_name: 作成するモデル名
            modelfile_content: Modelfileの内容
            base_model: ベースモデル（Modelfile内で指定されていない場合）
            debug_logger: デバッグロガー
        """
        if debug_logger is None:
            debug_logger = DebugLogger(False)

        # Modelfileの内容を準備
        if base_model and "FROM" not in modelfile_content.upper():
            modelfile_content = f"FROM {base_model}\n{modelfile_content}"

        payload = {
            "name": model_name,
            "modelfile": modelfile_content,
            "stream": False
        }

        try:
            debug_logger.dbg("Creating model:", model_name)
            debug_logger.dbg("Modelfile content:", modelfile_content)
            debug_logger.dbg("API payload:", payload)

            # /api/create エンドポイントを使用
            response = self._http_json("POST", "/api/create", payload, timeout=300)
            debug_logger.dbg("Create response:", response)
            return True

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            debug_logger.dbg("Model creation HTTP error:", f"Status: {e.code}, Body: {error_body}")
            return False
        except Exception as e:
            debug_logger.dbg("Model creation failed:", str(e))
            return False

    def delete_model(self, model_name: str, debug_logger: DebugLogger = None) -> bool:
        """モデルを削除"""
        if debug_logger is None:
            debug_logger = DebugLogger(False)

        payload = {"name": model_name}

        try:
            debug_logger.dbg("Deleting model:", model_name)
            response = self._http_json("DELETE", "/api/delete", payload, timeout=30)
            debug_logger.dbg("Delete response:", response)
            return True
        except Exception as e:
            debug_logger.dbg("Model deletion failed:", str(e))
            return False


# ===== 独立関数（簡易版） =====
def ensure_ollama_running(host: str) -> bool:
    """Ollama /api/version が 200 を返せば True。"""
    import urllib.request
    url = f"{host.rstrip('/')}/api/version"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False

# 使用例
if __name__ == "__main__":
    import argparse
    from llm_common import DebugLogger

    parser = argparse.ArgumentParser(description="Ollama LLM provider")
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--model", type=str, help="Model name to use")
    parser.add_argument("--prompt", type=str, help="Prompt to generate")
    parser.add_argument("--host", type=str, help="Ollama host URL")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--pull", type=str, help="Pull a model")
    parser.add_argument("--create", type=str, help="Create custom model from Modelfile")
    parser.add_argument("--modelfile", type=str, help="Path to Modelfile")
    parser.add_argument("--base-model", type=str, help="Base model for custom model")
    parser.add_argument("--delete", type=str, help="Delete a model")
    parser.add_argument("--debug", type=int, default=0, metavar="LEVEL",
                        help="Debug level: 0=content only, 1=basic info, 2=token info, 3=full details")
    args = parser.parse_args()

    debug_logger = DebugLogger(args.debug > 0, args.debug)

    try:
        config = OllamaConfig(host=args.host, debug_logger=debug_logger)

        if args.test:
            config.test_connection()
        elif args.list:
            models = config.list_models(show_details=args.debug > 2)
            if models:
                print("Available models:")
                for model in models:
                    if args.debug >= 2:
                        print(f"  {model}")
                    else:
                        print(f"  {model.get('name', 'unknown')}")
            else:
                print("No models found or connection failed")
        elif args.pull:
            print(f"Pulling model: {args.pull}")
            success = config.pull_model(args.pull, debug_logger)
            if success:
                print("Pull successful")
            else:
                print("Pull failed")
        elif args.create and args.modelfile:
            if not os.path.exists(args.modelfile):
                print(f"Modelfile not found: {args.modelfile}")
                exit(1)

            with open(args.modelfile, 'r', encoding='utf-8') as f:
                modelfile_content = f.read()

            print(f"Creating model: {args.create}")
            success = config.create_model_from_modelfile(
                args.create, modelfile_content, args.base_model, debug_logger
            )
            if success:
                print("Model creation successful")
            else:
                print("Model creation failed")
        elif args.delete:
            print(f"Deleting model: {args.delete}")
            success = config.delete_model(args.delete, debug_logger)
            if success:
                print("Model deletion successful")
            else:
                print("Model deletion failed")
        elif args.model and args.prompt:
            config.ensure_model_available(args.model)
            response = config.infer(args.prompt)

            # デバッグレベルに応じた出力
            if args.debug > 0:
                debug_logger.log_response(response)
            else:
                print(response.content)
        else:
            parser.print_help()

    except Exception as e:
        if args.debug > 0:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}")
            exit(1)
