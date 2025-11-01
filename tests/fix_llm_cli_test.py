#!/usr/bin/env python3
"""
fix_llm_cli_test.py - LLM CLIの修正版テスト
"""
import sys
import os
sys.path.insert(0, '/mnt/c/Users/kenny/sandbox/NeuroHub')
os.environ['PYTHONPATH'] = '/mnt/c/Users/kenny/sandbox/NeuroHub'
os.environ['OLLAMA_HOST'] = 'http://127.0.0.1:11434'

def test_direct_ollama_api():
    """直接OllamaAPIを呼び出してテスト"""
    import urllib.request
    import json

    try:
        # Ollama API直接呼び出し
        url = "http://127.0.0.1:11434/api/generate"
        payload = {
            "model": "qwen2.5:1.5b-instruct",
            "prompt": "Return exactly: PONG",
            "stream": False
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Ollama API Response: {result.get('response', 'No response')}")
            print(f"   Model: {result.get('model', 'Unknown')}")
            print(f"   Done: {result.get('done', False)}")
            return True

    except Exception as e:
        print(f"❌ Ollama API Error: {e}")
        return False

def test_mcp_core_ask_llm():
    """MCPコアのask_llm関数をテスト"""
    try:
        from services.mcp.core import ask_llm
        from services.llm.llm_common import DebugLogger

        debug = DebugLogger(True)
        body, meta = ask_llm("Return exactly: PONG", debug)
        print(f"✅ MCP ask_llm Response: {body}")
        print(f"   Meta: {meta}")
        return True

    except Exception as e:
        print(f"❌ MCP ask_llm Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 API取得テスト開始")
    print("=" * 50)

    print("\n1. 直接Ollama API呼び出しテスト:")
    api_result = test_direct_ollama_api()

    print("\n2. MCP ask_llm 関数テスト:")
    mcp_result = test_mcp_core_ask_llm()

    print("\n" + "=" * 50)
    if api_result and mcp_result:
        print("✅ 全てのAPIテストが成功しました！")
    else:
        print("❌ 一部のAPIテストが失敗しました")

    print("\n💡 回避策:")
    print("   - 直接コマンド実行: python3 services/mcp/cmd_exec.py --cmd 'ls' --no-explain")
    print("   - 手動プロジェクトテスト: python3 simple_mcp_test.py projects/file_list_demo")
