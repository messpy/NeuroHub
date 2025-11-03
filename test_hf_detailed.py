#!/usr/bin/env python3
"""
HuggingFace詳細テストスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.ai.provider_huggingface import HuggingFaceConfig

def test_huggingface_detailed():
    """HuggingFace詳細テスト"""
    print("=" * 60)
    print("🧪 HuggingFace詳細テスト開始")
    print("=" * 60)

    # 環境変数確認
    hf_token = os.getenv('HF_TOKEN')
    hf_api_key = os.getenv('HUGGINGFACE_API_KEY')

    print(f"📋 環境変数確認:")
    print(f"   HF_TOKEN: {'設定済み' if hf_token else '未設定'}")
    print(f"   HUGGINGFACE_API_KEY: {'設定済み' if hf_api_key else '未設定'}")

    if not hf_token and not hf_api_key:
        print("⚠️ API Key未設定。テスト用トークンを設定します")
        os.environ['HF_TOKEN'] = 'hf_test_token'
        hf_token = 'hf_test_token'

    # プロバイダー初期化
    print(f"\n🔧 プロバイダー初期化:")
    try:
        provider = HuggingFaceConfig()
        print(f"   ✅ HuggingFaceConfig初期化成功")
        print(f"   Token: {provider.token[:10]}..." if provider.token else "   Token: 未設定")
        print(f"   Base URL: {provider.base_url}")
        print(f"   Default Model: {provider.default_model}")
        print(f"   Configured: {provider.is_configured()}")
    except Exception as e:
        print(f"   ❌ 初期化失敗: {e}")
        return False

    # 接続テスト
    print(f"\n🔌 接続テスト:")
    try:
        is_available = provider.test_connection()
        print(f"   結果: {'成功' if is_available else '失敗'}")
    except Exception as e:
        print(f"   ❌ 接続テストエラー: {e}")
        is_available = False

    if not is_available:
        print("\n📝 エラー詳細分析:")
        print("   - HF_TOKENが無効の可能性")
        print("   - ネットワーク接続問題")
        print("   - サービス利用制限")
        return False

    # 応答テスト
    print(f"\n📤 応答テスト:")
    test_prompt = "こんにちは世界を英語にしたら？"
    try:
        print(f"   プロンプト: {test_prompt}")
        llm_response = provider.infer(test_prompt)

        print(f"   ✅ 応答取得成功")
        print(f"   応答タイプ: {type(llm_response)}")
        print(f"   応答内容: {llm_response.content[:100]}...")
        print(f"   応答長: {len(llm_response.content)}文字")

        # キーワード検出
        keywords = ["hello", "world", "Hello World"]
        response_lower = llm_response.content.lower()
        detected = [kw for kw in keywords if kw.lower() in response_lower]

        print(f"   検出キーワード: {detected}")
        print(f"   キーワード検出: {'✅ 成功' if detected else '⚠️ 失敗'}")

        return len(detected) > 0

    except Exception as e:
        print(f"   ❌ 応答テストエラー: {e}")
        print(f"   エラータイプ: {type(e)}")
        return False

if __name__ == "__main__":
    success = test_huggingface_detailed()
    print("\n" + "=" * 60)
    print(f"🏁 テスト結果: {'✅ 成功' if success else '❌ 失敗'}")
    print("=" * 60)
    sys.exit(0 if success else 1)
