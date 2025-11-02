#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCPエージェントでファイル管理CLIツールを生成するデモ
"""

from agents.agent_mcp import MCPAgent, MCPRequest

def main():
    # MCPエージェント初期化
    agent = MCPAgent()
    
    # シンプルなファイル管理CLIツールを生成
    prompt = """
ファイル管理CLIツールを作成してください。

機能:
1. ファイル一覧表示（ls）
2. ファイル検索（find）
3. ファイルコピー（cp）
4. ファイル削除（rm）
5. ディレクトリ作成（mkdir）

要件:
- Pythonで実装
- argparseでCLI構築
- エラーハンドリング実装
- テストコード付き
- README.md付き
"""
    
    # MCPリクエスト作成
    request = MCPRequest(
        mode='project',
        prompt=prompt,
        project_name='file_manager_cli',
        project_type='cli',
        language='python',
        include_tests=True,
        include_docs=True
    )
    
    print("=" * 60)
    print("MCPエージェント: ファイル管理CLIツール生成開始")
    print("=" * 60)
    
    result = agent.execute(request)
    
    print("\n" + "=" * 60)
    print("生成結果:")
    print("=" * 60)
    print(f"成功: {result.success}")
    print(f"\n生成内容:\n{result.content}")
    print(f"\n作成ファイル: {result.files_created}")
    
    if result.errors:
        print(f"\nエラー: {result.errors}")
    if result.warnings:
        print(f"\n警告: {result.warnings}")
    
if __name__ == '__main__':
    main()
