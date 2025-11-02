#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3つのLLMプロバイダーで「こんにちは」応答テスト

WSL環境で実行:
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && \
  source venv_linux/bin/activate && \
  python3 test_hello_llm.py"
"""

import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.ai.provider_ollama import OllamaConfig
from services.ai.provider_gemini import GeminiConfig
from services.ai.provider_huggingface import HuggingFaceConfig


def test_ollama_hello():
    """Ollamaで「こんにちは」テスト"""
    print("\n=== Ollama テスト ===")
    try:
        config = OllamaConfig()
        if not config.is_configured():
            print("❌ Ollama未設定")
            return False

        response = config.infer("こんにちは")

        if response.status_code == 200:
            print(f"✅ Ollama応答成功")
            print(f"  モデル: {response.model}")
            print(f"  応答: {response.content[:100]}...")
            return True
        else:
            print(f"❌ Ollama応答失敗: {response.error}")
            return False
    except Exception as e:
        print(f"❌ Ollama例外: {e}")
        return False


def test_gemini_hello():
    """Geminiで「こんにちは」テスト"""
    print("\n=== Gemini テスト ===")
    try:
        config = GeminiConfig()
        if not config.is_configured():
            print("❌ Gemini未設定（API キー不足）")
            return False

        response = config.infer("こんにちは")

        if response.status_code == 200:
            print(f"✅ Gemini応答成功")
            print(f"  モデル: {response.model}")
            print(f"  応答: {response.content[:100]}...")
            return True
        else:
            print(f"❌ Gemini応答失敗: {response.error}")
            return False
    except Exception as e:
        print(f"❌ Gemini例外: {e}")
        return False


def test_huggingface_hello():
    """HuggingFaceで「こんにちは」テスト"""
    print("\n=== HuggingFace テスト ===")
    try:
        config = HuggingFaceConfig()
        if not config.is_configured():
            print("❌ HuggingFace未設定（API キー不足）")
            return False

        response = config.infer("こんにちは")

        if response.status_code == 200:
            print(f"✅ HuggingFace応答成功")
            print(f"  モデル: {response.model}")
            print(f"  応答: {response.content[:100]}...")
            return True
        else:
            print(f"❌ HuggingFace応答失敗: {response.error}")
            return False
    except Exception as e:
        print(f"❌ HuggingFace例外: {e}")
        return False


def main():
    """メイン処理"""
    print("=" * 60)
    print("3つのLLMプロバイダー「こんにちは」応答テスト")
    print("=" * 60)

    results = {
        "Ollama": test_ollama_hello(),
        "Gemini": test_gemini_hello(),
        "HuggingFace": test_huggingface_hello()
    }

    print("\n" + "=" * 60)
    print("結果サマリー")
    print("=" * 60)

    success_count = sum(results.values())
    total_count = len(results)

    for provider, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{provider:15s}: {status}")

    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        print("\n🎉 全プロバイダー成功！")
        return 0
    elif success_count > 0:
        print(f"\n⚠️ {total_count - success_count}個のプロバイダーが失敗しました")
        return 1
    else:
        print("\n❌ 全プロバイダーが失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
