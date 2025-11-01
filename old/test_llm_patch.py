#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLMプロバイダー修正パッチ - 統合版
各プロバイダーのmax_tokens設定とレスポンス処理を最適化
"""

import os
import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_fixed_providers():
    """修正されたプロバイダーをテスト"""
    print("🔧 LLMプロバイダー修正パッチテスト")
    print("=" * 60)

    # Gemini高品質テスト
    test_gemini_optimized()
    print("\n" + "-" * 60)

    # HuggingFace高品質テスト
    test_huggingface_optimized()
    print("\n" + "-" * 60)

    # Ollama修正テスト
    test_ollama_fixed()
    print("\n" + "-" * 60)

def test_gemini_optimized():
    """Gemini最適化テスト"""
    print("\n🔥 Gemini 最適化テスト")
    print("=" * 50)

    try:
        from services.llm.provider_gemini import GeminiConfig

        gemini = GeminiConfig()
        if not gemini.is_configured():
            print("❌ Gemini設定エラー")
            return

        # 高品質設定でテスト
        prompt = "PythonでFibonacci数列を計算する関数を1行で書いてください。"

        response = gemini.infer(
            prompt=prompt,
            opts={
                "max_tokens": 200,    # 十分な長さ
                "temperature": 0.1    # 確実な応答
            }
        )

        print(f"📨 応答:")
        print(f"   成功: {response.is_success}")
        print(f"   実行時間: {response.response_time:.2f}秒")

        if response.is_success:
            # レスポンス解析
            content = response.content
            if content and content.strip():
                print(f"   ✅ 生成内容: {content}")
            else:
                print("   ⚠️ 空のレスポンス")
                # Raw responseを確認
                if hasattr(response, 'raw_response'):
                    print(f"   🔍 Raw response: {str(response.raw_response)[:200]}")

            print(f"   📊 トークン: {response.tokens_used}")
        else:
            print(f"   ❌ エラー: {response.error}")

    except Exception as e:
        print(f"❌ Geminiテストエラー: {e}")

def test_huggingface_optimized():
    """HuggingFace最適化テスト"""
    print("\n⚡ HuggingFace 最適化テスト")
    print("=" * 50)

    try:
        from services.llm.provider_huggingface import HuggingFaceConfig

        hf = HuggingFaceConfig()
        if not hf.is_configured():
            print("❌ HuggingFace設定エラー")
            return

        # 高品質設定でテスト
        prompt = "PythonでFibonacci数列を計算する関数を1行で書いてください。"

        response = hf.infer(
            prompt=prompt,
            opts={
                "max_tokens": 200,    # 十分な長さ
                "temperature": 0.1,   # 確実な応答
            },
            system_text="あなたは親切なプログラミングアシスタントです。簡潔で実用的なコードを提供してください。"
        )

        print(f"📨 応答:")
        print(f"   成功: {response.is_success}")
        print(f"   実行時間: {response.response_time:.2f}秒")

        if response.is_success:
            content = response.content
            if not content.strip():
                print("   ⚠️ 空のレスポンス")
                # Raw responseを確認
                if hasattr(response, 'raw_response'):
                    print(f"   🔍 Raw response: {response.raw_response}")
            else:
                print(f"   ✅ 生成内容: {content}")

            print(f"   📊 トークン: {response.tokens_used}")
        else:
            print(f"   ❌ エラー: {response.error}")

    except Exception as e:
        print(f"❌ HuggingFaceテストエラー: {e}")

def test_ollama_fixed():
    """Ollama修正テスト"""
    print("\n🦙 Ollama 修正テスト")
    print("=" * 50)

    try:
        from services.llm.provider_ollama import OllamaConfig

        ollama = OllamaConfig()
        if not ollama.is_configured():
            print("❌ Ollama設定エラー")
            return

        # サーバー状態確認
        server_running = ollama._test_server_connection()
        print(f"📊 サーバー状態: {'✅ 起動中' if server_running else '❌ 停止中'}")

        if not server_running:
            print("🔄 サーバー起動を試行...")
            if ollama._ensure_server_running():
                print("✅ サーバー起動成功")
            else:
                print("❌ サーバー起動失敗")
                return

        # モデル確認
        print(f"🤖 現在のモデル: {ollama.current_model}")

        # テスト実行
        prompt = "PythonでFibonacci数列を計算する関数を1行で書いてください。"

        response = ollama.infer(prompt=prompt)

        print(f"📨 応答:")
        print(f"   成功: {response.is_success}")
        print(f"   実行時間: {response.response_time:.2f}秒")

        if response.is_success:
            print(f"   ✅ 生成内容: {response.content}")
            if hasattr(response, 'tokens_used') and response.tokens_used:
                print(f"   📊 トークン: {response.tokens_used}")
        else:
            print(f"   ❌ エラー: {response.error}")
            if hasattr(response, 'raw_response'):
                print(f"   🔍 Raw response: {response.raw_response}")

    except Exception as e:
        print(f"❌ Ollamaテストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_providers()
