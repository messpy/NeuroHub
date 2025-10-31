#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
provider_huggingface.py - Hugging Face Router(OpenAI互換) 簡易クライアント
- Inference API ではなく Router(OpenAI互換) に統一
- 404 対策: モデルは <model-id>:<provider> 形式で指定
- 依存: requests, (任意) python-dotenv
- 環境変数: HF_TOKEN（必須）, HF_HOST（任意）
"""

import os
import sys
import json
import argparse
import requests
from typing import Any, Dict, List, Optional
from pathlib import Path

# === .env を自動ロード（プロジェクト直下） ===
try:
    from dotenv import load_dotenv
    ROOT_DIR = Path(__file__).resolve().parents[2]
    ENV_PATH = ROOT_DIR / ".env"
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=False)
        print(f"[info] loaded .env from {ENV_PATH}", file=sys.stderr)
    else:
        print(f"[warn] .env not found at {ENV_PATH}", file=sys.stderr)
except Exception as e:
    print(f"[warn] dotenv load skipped ({e})", file=sys.stderr)

# === 共通ユーティリティ ===
from .llm_common import DebugLogger, load_config, get_llm_model_from_config, parse_opt_kv, LLMProviderConfig, make_api_request, LLMResponse, create_llm_response, LLMResponse, create_llm_response

# === Hugging Face設定の共通化 ===
class HuggingFaceConfig(LLMProviderConfig):
    def __init__(self):
        super().__init__("huggingface")
        # 環境変数から設定を取得
        self.token = os.getenv("HF_TOKEN")
        self.base_url = (os.getenv("HF_HOST") or "https://router.huggingface.co/v1").rstrip("/")
        self.default_model = "openai/gpt-oss-20b:groq"
        # config.yamlからモデルを取得
        self.model = self.get_model_from_config(self.default_model)

    def get_api_url(self, model: str = None) -> str:
        """API URLを生成"""
        return f"{self.base_url}/chat/completions"

    def is_configured(self) -> bool:
        """設定が有効かチェック"""
        return bool(self.token)

    def build_messages(self, system_text: Optional[str], user_text: str) -> List[Dict[str, str]]:
        """メッセージ配列を構築"""
        msgs: List[Dict[str, str]] = []
        if system_text:
            msgs.append({"role": "system", "content": system_text})
        msgs.append({"role": "user", "content": user_text})
        return msgs

    def build_payload(self, text: str, opts: Dict[str, Any] = None, system_text: str = None) -> Dict[str, Any]:
        """リクエストペイロードを構築"""
        messages = self.build_messages(system_text, text)
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        if opts:
            # openai互換の代表パラメータ
            allow = {"temperature","top_p","max_tokens","frequency_penalty","presence_penalty","stop","seed","response_format"}
            for k, v in opts.items():
                if k in allow:
                    payload[k] = v

        return payload

    def get_headers(self) -> Dict[str, str]:
        """APIリクエストヘッダーを取得"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def test_connection(self) -> bool:
        """接続テスト（基底クラスメソッドの実装）"""
        if not self.is_configured():
            print("❌ 設定エラー: HF_TOKEN が設定されていません")
            return False

        # 軽量なテストペイロード
        test_payload = self.build_payload("Hello", {"max_tokens": 10})
        url = self.get_api_url()
        headers = self.get_headers()
        logger = DebugLogger(enabled=False)

        response = make_api_request(
            url, test_payload, headers, 10, self, self.model, logger
        )

        if response.is_success:
            print("✅ 接続成功: Hugging Face Router は利用可能です")
            print(f"   モデル: {self.model}")
            print(f"   エンドポイント: {self.base_url}")
            return True
        else:
            print(f"❌ 接続失敗: {response.error}")
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """利用可能なHugging Faceモデル一覧を動的に取得"""
        try:
            # HF Routerのmodelsエンドポイントを試行
            models_url = f"{self.base_url}/models"
            headers = self.get_headers()

            response = requests.get(models_url, headers=headers, timeout=10)

            if response.status_code == 200:
                models_data = response.json()
                if isinstance(models_data, dict) and "data" in models_data:
                    # OpenAI API形式の場合
                    return [{"name": model.get("id", "unknown"), "description": model.get("description", "")}
                           for model in models_data["data"]]
                elif isinstance(models_data, list):
                    # 直接リストの場合
                    return [{"name": str(model), "description": ""} for model in models_data]

        except Exception as e:
            pass  # APIエラーの場合はフォールバック

        # API取得に失敗した場合は既知の動作するモデルを返す
        return [
            {"name": "openai/gpt-oss-20b:groq", "description": "GPT model via Groq (fallback)"},
            {"name": "meta-llama/Llama-3.1-8B-Instruct:groq", "description": "Llama 3.1 8B via Groq (fallback)"},
        ]

    def infer(self, prompt: str, opts: Dict[str, Any] = None, system_text: str = None) -> LLMResponse:
        """テキスト生成を実行（独自実装でより詳細な情報を取得）"""
        import time
        start_time = time.time()

        try:
            payload = self.build_payload(prompt, opts, system_text)
            url = self.get_api_url()
            headers = self.get_headers()

            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response_time = time.time() - start_time

            if response.status_code != 200:
                return create_llm_response(
                    status_code=response.status_code,
                    provider="huggingface",
                    model=self.model,
                    content="",
                    error=f"HTTP {response.status_code}: {response.text}",
                    response_time=response_time,
                    request_url=url,
                    request_payload=payload,
                    raw_response={"status_code": response.status_code, "text": response.text}
                )

            data = response.json()

            # コンテンツ抽出
            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                content = json.dumps(data, ensure_ascii=False)

            # トークン情報の抽出（HuggingFaceの場合）
            usage = data.get("usage", {})
            tokens_input = usage.get("prompt_tokens")
            tokens_output = usage.get("completion_tokens")
            tokens_total = usage.get("total_tokens")

            return create_llm_response(
                status_code=200,
                provider="huggingface",
                model=self.model,
                content=content,
                response_time=response_time,
                tokens_used=tokens_total,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                request_url=url,
                request_payload=payload,
                raw_response=data,
                metadata={
                    "router_host": self.base_url,
                    "model_provider": self.model.split(':')[-1] if ':' in self.model else "unknown",
                    "finish_reason": data.get("choices", [{}])[0].get("finish_reason") if data.get("choices") else None,
                    "api_type": "openai_compatible"
                }
            )

        except Exception as e:
            response_time = time.time() - start_time
            return create_llm_response(
                status_code=500,
                provider="huggingface",
                model=self.model,
                content="",
                error=f"Request failed: {str(e)}",
                response_time=response_time,
                request_url=url if 'url' in locals() else None,
                request_payload=payload if 'payload' in locals() else None,
                metadata={"exception_type": type(e).__name__}
            )


def main() -> int:
    ap = argparse.ArgumentParser(description="HF Router(OpenAI互換) client")
    ap.add_argument("prompt", nargs="*", help="ユーザープロンプト（スペース可）")
    ap.add_argument("--host", help="HF Router base URL（既定: env HF_HOST or https://router.huggingface.co/v1）")
    ap.add_argument("--model", help="モデル（既定: openai/gpt-oss-20b:groq）")
    ap.add_argument("--system", help="system プロンプト")
    ap.add_argument("--opt", action="append", help="key=val（temperature, top_p, max_tokens, stop など）")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--debug", type=int, default=0, metavar="LEVEL",
                    help="Debug level: 0=content only, 1=basic info, 2=token info, 3=full details")
    ap.add_argument("--test", action="store_true", help="接続テストのみ実行")
    ap.add_argument("--list", action="store_true", help="利用可能なモデル一覧を表示")
    args = ap.parse_args()

    logger = DebugLogger(enabled=args.debug > 0, level=args.debug)

    # === 設定の初期化 ===
    config = HuggingFaceConfig()
    if args.host:
        config.base_url = args.host.rstrip("/")
    if args.model:
        config.model = args.model

    if not config.is_configured():
        print("[error] 環境変数 HF_TOKEN が未設定です", file=sys.stderr)
        return 2

    # === テストモード ===
    if args.test:
        print("=== Hugging Face Router 接続テスト ===")
        success = config.test_connection()
        return 0 if success else 1

    # === モデルリスト表示 ===
    if args.list:
        models = config.list_models()
        print("利用可能なHugging Faceモデル:")
        for model in models:
            if args.debug >= 2:
                print(f"  {model}")
            else:
                name = model.get('name', 'unknown')
                desc = model.get('description', '')
                print(f"  {name:<40} - {desc}")
        return 0

    # === 通常のチャット処理 ===
    if not args.prompt:
        print("[error] プロンプトが必要です（--test, --list 以外）", file=sys.stderr)
        return 2

    user_text = " ".join(args.prompt)
    opts = parse_opt_kv(args.opt)

    try:
        response = config.infer(user_text, opts, args.system)

        # デバッグレベルに応じた出力
        if args.debug > 0:
            logger.log_response(response)
        else:
            print(response.content)
        return 0
    except Exception as e:
        if args.debug > 0:
            import traceback
            traceback.print_exc()
        else:
            print(f"[error] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
