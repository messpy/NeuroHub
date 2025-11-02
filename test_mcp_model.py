#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
neurohub-mcp-assistantモデルのテスト

MCPルールに基づいてコード生成し、以下を確認:
1. input()を使用していない
2. argparseを使用している
3. --test, --helpオプションが実装されている
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.llm_agent import LLMAgent, LLMRequest


def test_mcp_model_code_generation():
    """neurohub-mcp-assistantでコード生成テスト"""
    print("\n" + "=" * 80)
    print("🧪 neurohub-mcp-assistantモデルテスト")
    print("=" * 80)
    
    # LLMAgent初期化（ollamaプロバイダー指定）
    agent = LLMAgent(provider="ollama")
    
    # neurohub-mcp-assistantモデルを使用するよう設定
    agent.providers['ollama'].current_model = "neurohub-mcp-assistant"
    
    print(f"📍 使用モデル: {agent.providers['ollama'].current_model}")
    
    # テストプロンプト: 簡単な計算機
    prompt = """
四則演算ができるCLI計算機を作成してください。

要件:
- 2つの数値と演算子(+, -, *, /)を受け取る
- --num1, --num2, --operatorオプションで指定
- --testオプションでテストケース実行
- エラーハンドリング（ゼロ除算など）

必ず以下を守ってください:
- input()は絶対に使用しない
- argparseを使用
- 実行可能な完全なコードを出力

コードブロック ```python で囲んで出力してください。
"""
    
    print("\n📝 プロンプト:")
    print("-" * 80)
    print(prompt)
    print("-" * 80)
    
    # コード生成
    print("\n🤖 コード生成中...")
    request = LLMRequest(
        prompt=prompt,
        system_message="あなたはMCPルールに従ってPythonコードを生成するアシスタントです。input()は絶対に使用せず、argparseを使用してください。",
        request_type="code_generation",
        max_tokens=4000,
        temperature=0.2,
        preferred_provider="ollama"
    )
    
    try:
        response = agent.generate_text(request)
        
        if not response.is_success:
            print(f"\n❌ コード生成失敗: {response.error_message}")
            return False
        
        print("\n✅ コード生成完了")
        print("=" * 80)
        
        # コードブロックから抽出
        content = response.content
        if '```python' in content:
            start = content.find('```python') + len('```python')
            end = content.find('```', start)
            code = content[start:end].strip()
        else:
            code = content.strip()
        
        print(code)
        print("=" * 80)
        
        # コード検証
        print("\n🔍 コード検証:")
        print("-" * 80)
        
        checks = {
            "input()なし": 'input(' not in code,
            "argparse使用": 'import argparse' in code or 'from argparse' in code,
            "ArgumentParser作成": 'ArgumentParser' in code,
            "--testオプション": '--test' in code,
            "main()関数": 'def main(' in code,
            "if __name__": 'if __name__' in code
        }
        
        all_passed = True
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        
        print("-" * 80)
        
        if all_passed:
            print("\n🎉 全チェック合格! MCPルールに完全準拠しています!")
            
            # 生成されたコードを保存
            output_file = project_root / "generated_calculator_mcp.py"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(code)
            print(f"\n💾 コードを {output_file.name} に保存しました")
        else:
            print("\n⚠️ 一部チェック失敗")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 neurohub-mcp-assistantモデルテスト開始")
    
    # メインテスト
    result = test_mcp_model_code_generation()
    
    if result:
        print("\n" + "=" * 80)
        print("🎊 テスト完了！neurohub-mcp-assistantは正常に動作しています！")
        print("=" * 80)
    else:
        print("\n⚠️ テスト失敗")
