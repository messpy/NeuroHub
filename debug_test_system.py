#!/usr/bin/env python3
import sys
sys.path.append('.')

from agents.agent_mcp import MCPAgent
from pathlib import Path

# テストファイルパス
test_file = Path("services/mcp/generated_projects/calculator_app/main.py")

agent = MCPAgent()

# 詳細実行テストを直接実行
print("=== 直接実行テスト ===")
result1 = agent._detailed_execution_test(test_file, "", "引数なし実行テスト")
print(f"Success: {result1['success']}")
print(f"Return Code: {result1['returncode']}")
print(f"Output: {repr(result1['output'])}")
print(f"Error: {repr(result1['error'])}")

print("\n=== ヘルプテスト ===")
result2 = agent._detailed_execution_test(test_file, "--help", "ヘルプ表示テスト")
print(f"Success: {result2['success']}")
print(f"Return Code: {result2['returncode']}")
print(f"Output: {repr(result2['output'])}")
print(f"Error: {repr(result2['error'])}")

print("\n=== 品質スコア確認 ===")
with open(test_file, 'r', encoding='utf-8') as f:
    code = f.read()

score = agent._calculate_code_quality_score(code)
print(f"品質スコア: {score}%")

# 構文エラーチェック
syntax_errors = agent._strict_syntax_check(code, 'python')
print(f"構文エラー: {len(syntax_errors)} 個")
for error in syntax_errors:
    print(f"  - {error}")