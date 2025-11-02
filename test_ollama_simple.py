#!/usr/bin/env python3
"""
Ollama動作確認テスト
"""
import requests
import json

def test_ollama_simple():
    """シンプルなOllamaテスト"""
    
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "neurohub-mcp-assistant",
        "prompt": "こんにちは！簡単な自己紹介をしてください。",
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 200
        }
    }
    
    print("=" * 80)
    print("Ollama 動作確認テスト")
    print("=" * 80)
    print(f"\nモデル: {payload['model']}")
    print(f"プロンプト: {payload['prompt']}")
    print("\nリクエスト送信中...")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        print("\n✅ レスポンス受信成功！")
        print("=" * 80)
        print(result.get('response', ''))
        print("=" * 80)
        
        print(f"\n生成トークン数: {result.get('eval_count', 'N/A')}")
        print(f"処理時間: {result.get('total_duration', 0) / 1e9:.2f}秒")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ エラー: {e}")
        return False

if __name__ == "__main__":
    success = test_ollama_simple()
    exit(0 if success else 1)
