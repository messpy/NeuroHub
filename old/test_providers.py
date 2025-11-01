#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各LLMプロバイダーの個別テスト - 直接API呼び出し版
"""

import os
import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_gemini_direct():
    """Gemini直接テスト"""
    print(f"\n🧪 Gemini 直接APIテスト")
    print("=" * 50)

    try:
        from services.llm.provider_gemini import GeminiConfig

        # 設定確認
        gemini = GeminiConfig()
        print(f"📊 設定状態: {gemini.is_configured()}")

        if not gemini.is_configured():
            print("❌ Gemini が設定されていません")
            return

        # 直接生成
        prompt = "PythonでFibonacci数列を計算する関数を1行で書いてください。"

        print(f"📤 プロンプト送信: {prompt}")

        response = gemini.generate_text(
            prompt=prompt,
            system_message="あなたは親切なプログラミングアシスタントです。",
            max_tokens=100,
            temperature=0.3
        )

        print(f"� 応答:")
        print(f"   成功: {response.is_success}")
        print(f"   実行時間: {response.execution_time:.2f}秒")

        if response.is_success:
            print(f"   ✅ 生成内容: {response.content}")
            print(f"   📊 トークン: 入力={response.prompt_tokens}, 出力={response.completion_tokens}")
        else:
            print(f"   ❌ エラー: {response.error}")

    except Exception as e:
        print(f"❌ Geminiテストエラー: {e}")
        import traceback
        traceback.print_exc()

def test_huggingface_direct():
    """HuggingFace直接テスト"""
    print(f"\n🧪 HuggingFace 直接APIテスト")
    print("=" * 50)

    try:
        from services.llm.provider_huggingface import HuggingFaceConfig

        # 設定確認
        hf = HuggingFaceConfig()
        print(f"📊 設定状態: {hf.is_configured()}")

        if not hf.is_configured():
            print("❌ HuggingFace が設定されていません")
            return

        # 直接生成
        prompt = "PythonでFibonacci数列を計算する関数を1行で書いてください。"

        print(f"📤 プロンプト送信: {prompt}")

        response = hf.generate_text(
            prompt=prompt,
            system_message="あなたは親切なプログラミングアシスタントです。",
            max_tokens=100,
            temperature=0.3
        )

        print(f"📨 応答:")
        print(f"   成功: {response.is_success}")
        print(f"   実行時間: {response.execution_time:.2f}秒")

        if response.is_success:
            print(f"   ✅ 生成内容: {response.content}")
            print(f"   � トークン: 入力={response.prompt_tokens}, 出力={response.completion_tokens}")
        else:
            print(f"   ❌ エラー: {response.error}")

    except Exception as e:
        print(f"❌ HuggingFaceテストエラー: {e}")
        import traceback
        traceback.print_exc()

def test_ollama_direct():
    """Ollama直接テスト"""
    print(f"\n🧪 Ollama 直接APIテスト")
    print("=" * 50)

    try:
        from services.llm.provider_ollama import OllamaConfig

        # 設定確認
        ollama = OllamaConfig()
        print(f"� 設定状態: {ollama.is_configured()}")

        if not ollama.is_configured():
            print("❌ Ollama が設定されていません")
            return

        # 直接生成
        prompt = "PythonでFibonacci数列を計算する関数を1行で書いてください。"

        print(f"📤 プロンプト送信: {prompt}")

        response = ollama.generate_text(
            prompt=prompt,
            system_message="あなたは親切なプログラミングアシスタントです。",
            max_tokens=100,
            temperature=0.3
        )

        print(f"📨 応答:")
        print(f"   成功: {response.is_success}")
        print(f"   実行時間: {response.execution_time:.2f}秒")

        if response.is_success:
            print(f"   ✅ 生成内容: {response.content}")
            print(f"   📊 トークン: 入力={response.prompt_tokens}, 出力={response.completion_tokens}")
        else:
            print(f"   ❌ エラー: {response.error}")

    except Exception as e:
        print(f"❌ Ollamaテストエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    print("🔬 LLMプロバイダー直接APIテスト")
    print("=" * 60)

    # 各プロバイダーを直接テスト
    test_gemini_direct()
    print("\n" + "-" * 60)

    test_huggingface_direct()
    print("\n" + "-" * 60)

    test_ollama_direct()
    print("\n" + "-" * 60)

    print("\n🏁 全プロバイダー直接テスト完了")

if __name__ == "__main__":
    main()
