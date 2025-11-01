#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLMAgent デバッグスクリプト
"""

from agents.llm_agent import LLMAgent, LLMRequest
import traceback
import time

def debug_generate_text():
    agent = LLMAgent()
    request = LLMRequest(prompt='Hello', max_tokens=50, temperature=0.3)

    print("=== デバッグ開始 ===")
    start_time = time.time()

    # プロバイダー選択
    status = agent.check_provider_status()
    provider_order = [name for name in agent.provider_priority
                     if status.get(name, {}).available]

    print(f"利用可能プロバイダー: {provider_order}")

    last_error = None

    for provider_name in provider_order:
        print(f"\n--- {provider_name} プロバイダーテスト ---")

        try:
            provider = agent.providers[provider_name]
            print(f"プロバイダー設定済み: {provider.is_configured()}")

            if not provider.is_configured():
                print("設定未完了でスキップ")
                continue

            # API設定取得
            from services.llm.llm_common import get_api_defaults
            api_defaults = get_api_defaults(provider_name)
            max_tokens = api_defaults.get('max_tokens', request.max_tokens)
            temperature = api_defaults.get('temperature', request.temperature)

            print(f"API設定: max_tokens={max_tokens}, temperature={temperature}")

            # テキスト生成
            if hasattr(provider, 'infer'):
                print("inferメソッド使用")
                opts = {
                    'max_tokens': max_tokens,
                    'temperature': temperature
                }

                if provider_name == 'ollama':
                    print("Ollama用パラメータ")
                    response = provider.infer(request.prompt)
                else:
                    print("Gemini/HuggingFace用パラメータ")
                    if provider_name == 'huggingface' and request.system_message:
                        response = provider.infer(
                            request.prompt,
                            opts=opts,
                            system_text=request.system_message
                        )
                    else:
                        response = provider.infer(
                            request.prompt,
                            opts=opts
                        )

                print(f"レスポンス受信: success={response.is_success}")
                print(f"コンテンツ: {response.content[:50]}")

                # 履歴記録
                print("履歴記録中...")
                agent._log_request(
                    provider_name=provider_name,
                    request=request,
                    response=response,
                    response_time=time.time() - start_time
                )
                print("履歴記録完了")

                if response.is_success:
                    print(f"成功! プロバイダー: {provider_name}")
                    return response

                last_error = response.error
                print(f"失敗: {last_error}")

            else:
                print("inferメソッドなし")
                last_error = f"No infer method for {provider_name}"

        except Exception as e:
            print(f"例外発生: {e}")
            traceback.print_exc()
            last_error = str(e)
            continue

    print(f"\n=== 全プロバイダー失敗 ===")
    print(f"最後のエラー: {last_error}")

    # エラーレスポンス作成
    from services.llm.llm_common import LLMResponse
    error_response = LLMResponse(
        status_code=500,
        provider="none",
        model="none",
        content="",
        error=f"全プロバイダーで失敗: {last_error}",
        response_time=time.time() - start_time
    )

    return error_response

if __name__ == "__main__":
    result = debug_generate_text()
    print(f"\n=== 最終結果 ===")
    print(f"成功: {result.is_success}")
    print(f"コンテンツ: {result.content}")
    print(f"エラー: {result.error}")
