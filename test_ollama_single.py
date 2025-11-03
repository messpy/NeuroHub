#!/usr/bin/env python3
"""
Ollama単体動作確認テスト
Ollamaが正常に動作し、MCP実装に使用できるかテストする
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent_llm import OllamaConfig

def test_ollama_single():
    """Ollama単体での動作確認"""
    
    print("🔧 Ollama単体動作確認テスト開始")
    print("=" * 50)
    
    try:
        # 1. プロバイダー初期化
        print("1. プロバイダー初期化...")
        provider = OllamaConfig()
        print("   ✅ OllamaConfig初期化成功")
        
        # 2. 接続テスト
        print("\n2. 接続テスト...")
        is_available = provider.test_connection()
        print(f"   接続状況: {'✅ 成功' if is_available else '❌ 失敗'}")
        
        if not is_available:
            print("   ⚠️  Ollama接続失敗 - MCP実装には接続が必要です")
            return False
            
        # 3. 基本応答テスト
        print("\n3. 基本応答テスト...")
        test_prompt = "Hello, can you help me with programming?"
        response = provider.infer(test_prompt)
        
        if response and response.content:
            print(f"   ✅ 応答取得成功")
            print(f"   📝 応答内容: {response.content[:100]}...")
        else:
            print("   ❌ 応答取得失敗")
            return False
        
        # 4. MCP実装適性テスト
        print("\n4. MCP実装適性テスト...")
        mcp_test_prompt = """
Please create a simple Python function that takes a string and returns it in uppercase.
Include proper docstring and error handling.
"""
        mcp_response = provider.infer(mcp_test_prompt)
        
        if mcp_response and mcp_response.content:
            print(f"   ✅ MCP適性テスト成功")
            print(f"   📝 コード生成能力: 確認済み")
            print(f"   📄 応答例: {mcp_response.content[:200]}...")
            
            # 関数定義・docstring・エラーハンドリングの確認
            content = mcp_response.content.lower()
            has_function = 'def ' in content
            has_docstring = '"""' in content or "'''" in content
            has_error_handling = 'try:' in content or 'except' in content or 'raise' in content
            
            print(f"   📊 品質チェック:")
            print(f"      関数定義: {'✅' if has_function else '⚠️'}")
            print(f"      docstring: {'✅' if has_docstring else '⚠️'}")
            print(f"      エラーハンドリング: {'✅' if has_error_handling else '⚠️'}")
            
        else:
            print("   ❌ MCP適性テスト失敗")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Ollama単体動作確認完了")
        print("✅ MCP実装に使用可能")
        return True
        
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        print("⚠️  Ollama単体での実装は困難な可能性があります")
        return False

if __name__ == "__main__":
    success = test_ollama_single()
    sys.exit(0 if success else 1)