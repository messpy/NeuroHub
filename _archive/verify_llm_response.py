#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM レスポンス詳細検証
実際にテキストが返ってきているかを厳密にチェック
"""

import os
import sys
import json
from pathlib import Path

# プロジェクトパス追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def detailed_response_check():
    """詳細レスポンス検証"""
    print("🔍 LLMレスポンス詳細検証")
    print("=" * 60)

    try:
        from agents.llm_agent import LLMAgent, LLMRequest

        agent = LLMAgent()

        # シンプルなテストプロンプト
        request = LLMRequest(
            prompt="こんにちは",
            max_tokens=50,
            temperature=0.7
        )

        print("📝 送信プロンプト: 'こんにちは'")
        print("⚙️ 設定: max_tokens=50, temperature=0.7")
        print()

        response = agent.generate_text(request)

        print(f"📤 使用プロバイダー: {response.provider}")
        print(f"⏱️ レスポンス時間: {response.response_time:.3f}秒")
        print(f"📊 ステータス: {response.status_code}")
        print()

        print("🔍 完全レスポンス内容:")
        print("-" * 40)
        print(f"型: {type(response.content)}")
        print(f"長さ: {len(str(response.content))} 文字")
        print(f"内容: {response.content}")
        print("-" * 40)

        # JSONかどうか確認
        try:
            if isinstance(response.content, str) and response.content.startswith('{'):
                parsed = json.loads(response.content)
                print("\n📋 JSON解析結果:")
                print(json.dumps(parsed, indent=2, ensure_ascii=False))

                # 実際のテキスト抽出試行
                if 'candidates' in parsed:
                    for i, candidate in enumerate(parsed['candidates']):
                        print(f"\n📄 候補{i+1}:")
                        if 'content' in candidate:
                            content = candidate['content']
                            print(f"   内容: {content}")
                            if 'parts' in content:
                                for j, part in enumerate(content['parts']):
                                    print(f"   パート{j+1}: {part}")
                        if 'finishReason' in candidate:
                            print(f"   終了理由: {candidate['finishReason']}")
        except json.JSONDecodeError:
            print("⚠️ JSON形式ではない")

        # 他のプロバイダーも確認
        print(f"\n" + "=" * 60)
        print("🔄 他のプロバイダーも確認:")

        for provider_name in ['huggingface', 'ollama']:
            print(f"\n🧪 {provider_name.upper()} テスト:")
            try:
                request_provider = LLMRequest(
                    prompt="Hello",
                    max_tokens=30,
                    preferred_provider=provider_name
                )

                response_provider = agent.generate_text(request_provider)
                print(f"   プロバイダー: {response_provider.provider}")
                print(f"   時間: {response_provider.response_time:.3f}秒")
                print(f"   内容型: {type(response_provider.content)}")
                print(f"   内容: {str(response_provider.content)[:100]}...")

            except Exception as e:
                print(f"   ❌ エラー: {str(e)}")

        return True

    except Exception as e:
        print(f"❌ 全体エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_actual_text_generation():
    """実際のテキスト生成確認"""
    print(f"\n" + "=" * 60)
    print("📝 実際のテキスト生成確認")
    print("=" * 60)

    try:
        from agents.llm_agent import LLMAgent, LLMRequest

        agent = LLMAgent()

        # 明確な質問で実際の応答を確認
        test_cases = [
            "1+1は？",
            "猫を英語で言うと？",
            "Pythonでprint文を書いて"
        ]

        for i, prompt in enumerate(test_cases, 1):
            print(f"\n🧪 テスト{i}: {prompt}")

            request = LLMRequest(
                prompt=prompt,
                max_tokens=100
            )

            response = agent.generate_text(request)

            print(f"   📤 プロバイダー: {response.provider}")
            print(f"   📊 レスポンス型: {type(response.content)}")

            # 実際のテキスト内容確認
            content_str = str(response.content)

            if len(content_str) > 200:
                print(f"   💬 内容（先頭100文字）: {content_str[:100]}...")
                print(f"   💬 内容（末尾50文字）: ...{content_str[-50:]}")
            else:
                print(f"   💬 内容（全体）: {content_str}")

            # 質問への適切な回答かチェック
            if prompt == "1+1は？":
                has_answer = any(x in content_str for x in ['2', '二', 'two', 'Two'])
                print(f"   ✅ 数学的回答: {'あり' if has_answer else 'なし'}")
            elif prompt == "猫を英語で言うと？":
                has_answer = any(x in content_str for x in ['cat', 'Cat', 'CAT'])
                print(f"   ✅ 英語回答: {'あり' if has_answer else 'なし'}")
            elif "print" in prompt:
                has_answer = any(x in content_str for x in ['print', 'Print', 'PRINT'])
                print(f"   ✅ Python回答: {'あり' if has_answer else 'なし'}")

    except Exception as e:
        print(f"❌ テスト失敗: {str(e)}")
        return False

def main():
    """メイン実行"""
    print("🔬 LLM実際動作検証")

    # 詳細レスポンス確認
    detailed_response_check()

    # 実際のテキスト生成確認
    check_actual_text_generation()

    print(f"\n" + "=" * 60)
    print("🏁 検証完了")
    print("実際にテキストが生成されているか確認してください")

if __name__ == "__main__":
    main()
