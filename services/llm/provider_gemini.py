#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
provider_gemini.py - Google Generative Language API (Gemini) クライアント最小版
- 依存: requests, (任意) python-dotenv, PyYAML
- 環境変数: GEMINI_API_KEY（必須）, GEMINI_API_URL(任意)
- モデル: config.yaml の llm.gemini.model があれば優先、無ければ gemini-2.5-flash
"""

from __future__ import annotations
import os
import sys
import json
import argparse
from typing import Any, Dict, List, Optional
from pathlib import Path
import requests

# === .env の読み込みをここで強制 ===
try:
    from dotenv import load_dotenv
    # プロジェクトルートを自動特定（このファイル -> llm -> services -> プロジェクト）
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
from .llm_common import DebugLogger, load_config, get_llm_model_from_config, parse_opt_kv, LLMProviderConfig, make_api_request, LLMResponse, create_llm_response

# === Gemini設定の共通化 ===
class GeminiConfig(LLMProviderConfig):
    def __init__(self):
        super().__init__("gemini")
        # 環境変数から設定を取得
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.base_url = (os.getenv("GEMINI_API_URL") or "https://generativelanguage.googleapis.com/v1").rstrip("/")
        self.default_model = "gemini-2.5-flash"
        # config.yamlからモデルを取得
        self.model = self.get_model_from_config(self.default_model)

    def get_api_url(self, model: str = None) -> str:
        """API URLを生成"""
        target_model = model or self.model
        return f"{self.base_url}/models/{target_model}:generateContent?key={self.api_key}"

    def is_configured(self) -> bool:
        """設定が有効かチェック"""
        return bool(self.api_key)

    def build_payload(self, text: str, opts: Dict[str, Any] = None) -> Dict[str, Any]:
        """リクエストペイロードを構築"""
        payload: Dict[str, Any] = {"contents": [{"parts": [{"text": text}]}]}

        if opts:
            gen = {}
            if "temperature" in opts:
                gen["temperature"] = float(opts["temperature"])
            if "top_p" in opts:
                gen["topP"] = float(opts["top_p"])
            if "max_tokens" in opts:
                gen["maxOutputTokens"] = int(opts["max_tokens"])
            if gen:
                payload["generationConfig"] = gen

        return payload

    def test_connection(self) -> bool:
        """接続テスト（基底クラスメソッドの実装）"""
        if not self.is_configured():
            print("❌ 設定エラー: GEMINI_API_KEY が設定されていません")
            return False

        # 軽量なテストペイロード
        test_payload = self.build_payload("Hello", {"max_tokens": 10})
        url = self.get_api_url(self.default_model)
        headers = {"Content-Type": "application/json"}
        logger = DebugLogger(enabled=False)

        response = make_api_request(
            url, test_payload, headers, 10, self, self.default_model, logger
        )

        if response.is_success:
            print("✅ 接続成功: Gemini API は利用可能です")
            print(f"   モデル: {self.model}")
            print(f"   エンドポイント: {self.base_url}")
            return True
        else:
            print(f"❌ 接続失敗: {response.error}")
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """利用可能なGeminiモデル一覧を動的に取得"""
        try:
            # Gemini APIのmodelsエンドポイントを使用
            models_url = f"{self.base_url}/models?key={self.api_key}"

            response = requests.get(models_url, timeout=10)

            if response.status_code == 200:
                models_data = response.json()
                models = []

                if "models" in models_data:
                    for model in models_data["models"]:
                        name = model.get("name", "").replace("models/", "")
                        if name and "generateContent" in model.get("supportedGenerationMethods", []):
                            models.append({
                                "name": name,
                                "description": model.get("displayName", "")
                            })

                if models:
                    return models

        except Exception as e:
            pass  # APIエラーの場合はフォールバック

        # API取得に失敗した場合は既知の動作するモデルを返す
        return [
            {"name": "gemini-2.5-flash", "description": "Latest fast model (fallback)"},
            {"name": "gemini-1.5-flash", "description": "Previous generation fast model (fallback)"},
        ]

    def infer(self, prompt: str, opts: Dict[str, Any] = None) -> LLMResponse:
        """テキスト生成を実行（独自実装でより詳細な情報を取得）"""
        import time
        start_time = time.time()

        try:
            payload = self.build_payload(prompt, opts)
            url = self.get_api_url()
            headers = {"Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response_time = time.time() - start_time

            if response.status_code != 200:
                return create_llm_response(
                    status_code=response.status_code,
                    provider="gemini",
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
                content = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError):
                content = json.dumps(data, ensure_ascii=False)

            # トークン情報の抽出（Geminiの場合）
            usage_metadata = data.get("usageMetadata", {})
            tokens_input = usage_metadata.get("promptTokenCount")
            tokens_output = usage_metadata.get("candidatesTokenCount")
            tokens_total = usage_metadata.get("totalTokenCount")

            return create_llm_response(
                status_code=200,
                provider="gemini",
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
                    "generation_config": payload.get("generationConfig", {}),
                    "safety_ratings": data.get("candidates", [{}])[0].get("safetyRatings", []) if data.get("candidates") else [],
                    "api_version": "v1beta"
                }
            )

        except Exception as e:
            response_time = time.time() - start_time
            return create_llm_response(
                status_code=500,
                provider="gemini",
                model=self.model,
                content="",
                error=f"Request failed: {str(e)}",
                response_time=response_time,
                request_url=url if 'url' in locals() else None,
                request_payload=payload if 'payload' in locals() else None,
                metadata={"exception_type": type(e).__name__}
            )


def main() -> int:
    ap = argparse.ArgumentParser(description="Gemini provider")
    ap.add_argument("prompt", nargs="*", help="ユーザープロンプト（スペース可）")
    ap.add_argument("--system", help="system プロンプト")
    ap.add_argument("--opt", action="append", help="key=val（temperature, top_p など）")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--debug", type=int, default=0, metavar="LEVEL",
                    help="Debug level: 0=content only, 1=basic info, 2=token info, 3=full details")
    ap.add_argument("--test", action="store_true", help="接続テストのみ実行")
    ap.add_argument("--list", action="store_true", help="利用可能なモデル一覧を表示")
    ap.add_argument("--model", type=str, help="使用するモデル名")
    args = ap.parse_args()

    logger = DebugLogger(enabled=args.debug > 0, level=args.debug)

    # === 設定の初期化 ===
    config = GeminiConfig()

    # モデル指定があれば上書き
    if args.model:
        config.model = args.model

    if not config.is_configured():
        print("[error] 環境変数 GEMINI_API_KEY が未設定です", file=sys.stderr)
        return 2

    # === テストモード ===
    if args.test:
        print("=== Gemini API 接続テスト ===")
        success = config.test_connection()
        return 0 if success else 1

    # === モデルリスト表示 ===
    if args.list:
        models = config.list_models()
        print("利用可能なGeminiモデル:")
        for model in models:
            if args.debug >= 2:
                print(f"  {model}")
            else:
                name = model.get('name', 'unknown')
                desc = model.get('description', '')
                print(f"  {name:<20} - {desc}")
        return 0

    # === 通常のチャット処理 ===
    if not args.prompt:
        print("[error] プロンプトが必要です（--test, --list 以外）", file=sys.stderr)
        return 2

    # プロンプト構築
    user_text = " ".join(args.prompt)
    text = (args.system + "\n" if args.system else "") + user_text

    # オプション解析とペイロード構築
    opts = parse_opt_kv(args.opt)

    try:
        response = config.infer(text, opts)

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
