#!/usr/bin/env python3
"""
LLMAgent詳細デバッグテスト
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.llm_agent import LLMAgent, LLMRequest

def test_llm_agent_debug():
    """LLMAgent動作確認"""
    
    print("=" * 80)
    print("LLMAgent デバッグテスト")
    print("=" * 80)
    
    # 1. 初期化
    print("\n[1] LLMAgent初期化中...")
    agent = LLMAgent(provider='ollama')
    
    print(f"✅ 初期化完了")
    print(f"   プロバイダー優先順位: {agent.provider_priority}")
    print(f"   利用可能プロバイダー: {list(agent.providers.keys())}")
    
    # 2. プロバイダー状態確認
    print("\n[2] プロバイダー状態確認中...")
    for name, provider in agent.providers.items():
        print(f"\n   プロバイダー: {name}")
        print(f"   - configured: {provider.is_configured()}")
        if hasattr(provider, 'host'):
            print(f"   - host: {provider.host}")
        if hasattr(provider, 'current_model'):
            print(f"   - model: {provider.current_model}")
    
    # 3. シンプルなリクエスト
    print("\n[3] シンプルなリクエスト送信中...")
    request = LLMRequest(
        prompt="1+1の答えは？",
        system_message="あなたは数学の先生です。",
        request_type="simple_test",
        max_tokens=100,
        temperature=0.3,
        preferred_provider='ollama'
    )
    
    print(f"   プロンプト: {request.prompt}")
    print(f"   優先プロバイダー: {request.preferred_provider}")
    
    try:
        response = agent.generate_text(request)
        
        print("\n✅ レスポンス受信！")
        print("=" * 80)
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Status: {response.status_code}")
        if response.error:
            print(f"Error: {response.error}")
        print(f"\nContent:\n{response.content}")
        print("=" * 80)
        
        if hasattr(response, 'response_time'):
            print(f"\nレスポンス時間: {response.response_time:.2f}秒")
        if hasattr(response, 'tokens_used'):
            print(f"トークン数: {response.tokens_used}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_agent_debug()
    exit(0 if success else 1)
