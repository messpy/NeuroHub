#!/usr/bin/env python3
import sys
sys.path.append('.')

from agents.agent_mcp import MCPAgent

agent = MCPAgent()
with open('services/mcp/generated_projects/calculator_app_test/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

score = agent._calculate_code_quality_score(code)
print(f'実際の品質スコア: {score}%')

# 詳細分析
print('\n品質分析:')
print(f'import文あり: {"import" in code}')
print(f'def文あり: {"def " in code}')
main_check = 'if __name__ == "__main__"' in code
print(f'main関数あり: {main_check}')
print(f'コード長: {len(code.strip())} 文字')
print(f'計算機能あり (+,-,*,/): {any(op in code for op in ["+", "-", "*", "/"])}')

syntax_errors = agent._strict_syntax_check(code, 'python')
print(f'構文エラー: {len(syntax_errors)} 個')
if syntax_errors:
    for error in syntax_errors[:3]:
        print(f'  - {error}')

# 問題詳細チェック
print('\n問題詳細チェック:')
if 'json' in code and 'import json' not in code:
    print('❌ jsonを使用してるがimportなし')
if 'Dict[' in code and 'from typing import' not in code:
    print('❌ Dict型ヒントを使用してるがimportなし')
if 'result_list.append' in code and 'result_list = ' not in code:
    print('❌ 未定義の変数result_listを使用')
if 'args.options' in code and '.add_argument' not in code:
    print('❌ 定義されていないargument')

print('\nコード品質の判定:')
if score < 85:
    print(f'❌ 品質不合格: {score}% (目標: 85%以上)')
else:
    print(f'✅ 品質合格: {score}%')

print('\n実行テスト:')
exec_result = agent._strict_execution_test(code)
print(f'実行成功: {exec_result["success"]}')
if not exec_result["success"]:
    print(f'実行エラー: {exec_result["error"]}')