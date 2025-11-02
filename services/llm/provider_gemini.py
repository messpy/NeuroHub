#!/usr/bin/env python3#!/usr/bin/env python3

# -*- coding: utf-8 -*-# -*- coding: utf-8 -*-

""""""

provider_gemini.py - Google Gemini LLM プロバイダーprovider_gemini.py - Google Generative Language API (Gemini) クライアント最小版

- 依存: requests, (任意) python-dotenv, PyYAML

使い方:- 環境変数: GEMINI_API_KEY（必須）, GEMINI_API_URL(任意)

  python provider_gemini.py "Hello Worldを日本語で？"- モデル: config.yaml の llm.gemini.model があれば優先、無ければ gemini-2.5-flash

  python provider_gemini.py --model gemini-1.5-flash --debug "質問""""

"""

from __future__ import annotationsfrom __future__ import annotations

import argparseimport os

import osimport sys

import sysimport json

from pathlib import Pathimport argparse

from typing import Any, Dict, List, Optional

# llm_common をインポートfrom pathlib import Path

HERE = Path(__file__).resolve().parentimport requests

sys.path.insert(0, str(HERE))

# === .env の読み込みをここで強制 ===

try:try:

    from .llm_common import load_env_from_config, DebugLogger    from dotenv import load_dotenv

except ImportError:    # プロジェクトルートを自動特定（このファイル -> llm -> services -> プロジェクト）

    from llm_common import load_env_from_config, DebugLogger    ROOT_DIR = Path(__file__).resolve().parents[2]

    ENV_PATH = ROOT_DIR / ".env"

load_env_from_config()    if ENV_PATH.exists():

        load_dotenv(ENV_PATH, override=False)

        print(f"[info] loaded .env from {ENV_PATH}", file=sys.stderr)

class GeminiConfig:    else:

    """Google Gemini設定クラス"""        print(f"[warn] .env not found at {ENV_PATH}", file=sys.stderr)

    except Exception as e:

    def __init__(self, api_key: str = None, debug: bool = False):    print(f"[warn] dotenv load skipped ({e})", file=sys.stderr)

        self.debug_logger = DebugLogger(debug)

        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")# === 共通ユーティリティ ===

        self.default_model = "gemini-1.5-flash"try:

            from .llm_common import DebugLogger, load_config, get_llm_model_from_config, parse_opt_kv, LLMProviderConfig, make_api_request, LLMResponse, create_llm_response

        if not self.api_key:except ImportError:

            raise ValueError("GEMINI_API_KEY not set. Please set it in .env file")    # 直接実行時の対応

        from llm_common import DebugLogger, load_config, get_llm_model_from_config, parse_opt_kv, LLMProviderConfig, make_api_request, LLMResponse, create_llm_response

    def generate(self, prompt: str, model: str = None) -> str:

        """テキスト生成（将来実装予定）"""# === Gemini設定の共通化 ===

        # TODO: Google Gemini APIの実装class GeminiConfig(LLMProviderConfig):

        # 現在はプレースホルダー    def __init__(self):

        self.debug_logger.log(f"[Gemini] Model: {model or self.default_model}")        super().__init__("gemini")

        self.debug_logger.log(f"[Gemini] Prompt: {prompt}")        # 環境変数から設定を取得

                self.api_key = os.getenv("GEMINI_API_KEY", "")

        raise NotImplementedError(        self.base_url = (os.getenv("GEMINI_API_URL") or "https://generativelanguage.googleapis.com/v1").rstrip("/")

            "Gemini provider is not yet implemented. "        self.default_model = "gemini-2.5-flash"

            "Please install google-generativeai and implement the API integration."        # config.yamlからモデルを取得

        )        self.model = self.get_model_from_config(self.default_model)



    def get_api_url(self, model: str = None) -> str:

def main():        """API URLを生成"""

    parser = argparse.ArgumentParser(description="Google Gemini LLM provider")        target_model = model or self.model

    parser.add_argument("prompt", nargs="?", help="入力プロンプト")        return f"{self.base_url}/models/{target_model}:generateContent?key={self.api_key}"

    parser.add_argument("--model", default="gemini-1.5-flash", help="モデル名")

    parser.add_argument("--debug", action="store_true", help="デバッグモード")    def is_configured(self) -> bool:

    args = parser.parse_args()        """設定が有効かチェック"""

            return bool(self.api_key)

    if not args.prompt:

        print("Error: prompt required", file=sys.stderr)    def build_payload(self, text: str, opts: Dict[str, Any] = None) -> Dict[str, Any]:

        return 1        """リクエストペイロードを構築"""

            payload: Dict[str, Any] = {"contents": [{"parts": [{"text": text}]}]}

    try:

        config = GeminiConfig(debug=args.debug)        if opts:

        response = config.generate(args.prompt, model=args.model)            gen = {}

        print(response)            if "temperature" in opts:

        return 0                gen["temperature"] = float(opts["temperature"])

    except Exception as e:            if "top_p" in opts:

        print(f"Error: {e}", file=sys.stderr)                gen["topP"] = float(opts["top_p"])

        return 1            if "max_tokens" in opts:

                max_tokens_value = int(opts["max_tokens"])

                gen["maxOutputTokens"] = max_tokens_value

if __name__ == "__main__":                print(f"[DEBUG-GEMINI] maxOutputTokens設定: {max_tokens_value}")

    sys.exit(main())            if gen:

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

            # コンテンツ抽出（改良版）
            content = ""
            try:
                candidates = data.get("candidates", [])
                if candidates:
                    candidate = candidates[0]
                    candidate_content = candidate.get("content", {})

                    # parts配列からテキスト抽出
                    parts = candidate_content.get("parts", [])
                    if parts:
                        # 最初のパートのテキストを取得
                        for part in parts:
                            if isinstance(part, dict) and "text" in part:
                                text = part["text"].strip()
                                if text:
                                    content = text
                                    break

                    # partsが空または見つからない場合
                    if not content:
                        finish_reason = candidate.get("finishReason", "")
                        if finish_reason == "MAX_TOKENS":
                            content = "[警告] max_tokensに達しました。より長い応答が必要な場合はmax_tokensを増やしてください。"
                        elif finish_reason == "SAFETY":
                            content = "[エラー] セーフティフィルターによりブロックされました。プロンプトを変更してください。"
                        elif finish_reason == "STOP":
                            content = "[情報] 応答が正常に完了しました（内容が空）。"
                        else:
                            # デバッグ用：実際のレスポンス構造を表示
                            content = f"[Gemini解析エラー] finishReason: {finish_reason}, 構造: {json.dumps(candidate_content, ensure_ascii=False, indent=2)}"

                if not content:
                    content = f"[Geminiレスポンス解析失敗] {json.dumps(data, ensure_ascii=False)}"

            except Exception as e:
                content = f"[Gemini例外エラー] {str(e)}: {json.dumps(data, ensure_ascii=False)}"

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
        if success:
            # 接続成功後、実際のプロンプトテストを実行
            print("\n=== レスポンステスト ===")
            test_prompt = "今の日時は？"
            print(f"プロンプト: {test_prompt}")

            try:
                response = config.infer(test_prompt, {"max_tokens": 150})
                print(f"✅ レスポンス成功")
                print(f"内容: {response.content}")
                print(f"レスポンス時間: {response.response_time:.2f}秒")
            except Exception as e:
                print(f"❌ レスポンスエラー: {str(e)}")
                return 1
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
