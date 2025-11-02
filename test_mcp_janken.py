#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP じゃんけんゲーム生成テスト

OllamaでMCPを使ってDBベースのじゃんけんゲームを自動生成するテスト
"""

import sys
import os
import json
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.agent_llm import LLMAgent


def load_janken_spec():
    """じゃんけんゲーム仕様を読み込み"""
    spec_path = project_root / "data" / "project_plans" / "janken_game_spec.json"

    if not spec_path.exists():
        raise FileNotFoundError(f"仕様ファイルが見つかりません: {spec_path}")

    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_mcp_prompt(spec: dict) -> str:
    """仕様からMCP用プロンプトを生成"""

    prompt = f"""# プロジェクト生成依頼

## プロジェクト概要
- プロジェクト名: {spec['project_name']}
- 説明: {spec['description']}
- バージョン: {spec['version']}

## 機能要件
"""

    for req in spec['requirements']['functional']:
        prompt += f"- {req}\n"

    prompt += "\n## データベース設計\n\n"

    for table in spec['requirements']['database']['tables']:
        prompt += f"### {table['name']}テーブル\n"
        prompt += f"{table['description']}\n\n"
        prompt += "| カラム名 | 型 | 制約 |\n"
        prompt += "|---------|-----|------|\n"
        for col in table['columns']:
            prompt += f"| {col['name']} | {col['type']} | {col['constraints']} |\n"
        prompt += "\n"

    prompt += "## CLIコマンド\n\n"

    for cmd in spec['requirements']['cli_commands']:
        prompt += f"### {cmd['command']} コマンド\n"
        prompt += f"- 説明: {cmd['description']}\n"
        prompt += f"- 引数: {', '.join(cmd['args'])}\n"
        if 'choices' in cmd:
            prompt += f"- 選択肢: {', '.join(cmd['choices'])}\n"
        prompt += f"- 例: `{cmd['example']}`\n\n"

    prompt += f"\n## 技術スタック\n"
    prompt += f"- 言語: {spec['technical_stack']['language']}\n"
    prompt += f"- データベース: {spec['technical_stack']['database']}\n"
    prompt += "- ライブラリ:\n"
    for lib in spec['technical_stack']['libraries']:
        prompt += f"  - {lib}\n"

    prompt += f"\n## アーキテクチャ\n"
    prompt += f"メインファイル: {spec['architecture']['main_file']}\n\n"

    for module in spec['architecture']['modules']:
        prompt += f"### {module['name']} クラス\n"
        prompt += f"{module['description']}\n\n"
        prompt += "メソッド:\n"
        for method in module['methods']:
            prompt += f"- `{method}`\n"
        prompt += "\n"

    prompt += "\n## テスト要件\n\n"
    prompt += "### ユニットテスト\n"
    for test in spec['test_requirements']['unit_tests']:
        prompt += f"- {test}\n"

    prompt += "\n### 統合テスト\n"
    for test in spec['test_requirements']['integration_tests']:
        prompt += f"- {test}\n"

    prompt += f"\n## エラーハンドリング\n\n"
    for error, msg in spec['error_handling'].items():
        prompt += f"- **{error}**: {msg}\n"

    prompt += f"\n## 期待する成果物\n"
    for file in spec['expected_files']:
        prompt += f"- {file}\n"

    prompt += "\n## 成功基準\n"
    for criteria in spec['success_criteria']:
        prompt += f"- {criteria}\n"

    prompt += f"\n---\n\n{spec['mcp_generation_prompt']}"

    return prompt


def test_mcp_janken_generation():
    """MCPでじゃんけんゲーム生成テスト"""

    print("=" * 80)
    print("MCP じゃんけんゲーム生成テスト")
    print("=" * 80)

    # 1. 仕様読み込み
    print("\n[1] 仕様ファイル読み込み中...")
    spec = load_janken_spec()
    print(f"✅ 仕様読み込み完了: {spec['project_name']}")

    # 2. プロンプト生成
    print("\n[2] MCP用プロンプト生成中...")
    prompt = create_mcp_prompt(spec)
    print(f"✅ プロンプト生成完了 ({len(prompt)} 文字)")

    # プロンプトをファイルに保存
    prompt_path = project_root / "data" / "project_plans" / "janken_game_prompt.txt"
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print(f"   プロンプトを保存: {prompt_path}")

    # 3. LLMエージェント初期化（Ollama優先）
    print("\n[3] LLMエージェント初期化中...")
    try:
        agent = LLMAgent(provider='ollama')
        print("✅ Ollamaエージェント初期化完了")
        print(f"   優先プロバイダー: {', '.join(agent.provider_priority)}")

    except Exception as e:
        print(f"❌ エラー: {e}")
        print("   フォールバック: 利用可能なプロバイダーを自動選択")
        agent = LLMAgent()

    # 4. プロンプト送信
    print("\n[4] MCPにプロジェクト生成を依頼中...")
    print("-" * 80)
    print("プロンプト:")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("-" * 80)

    try:
        # LLMRequestオブジェクトを作成
        from agents.agent_llm import LLMRequest

        system_prompt = """あなたは優秀なPythonプログラマーです。
以下の要件に基づいて、完全に動作するPythonプロジェクトを生成してください。

重要な注意事項:
1. **データベース設計を厳密に守る**: テーブル定義、カラム型、制約を正確に実装
2. **エラーハンドリングを必ず実装**: 想定されるエラーケースをすべて処理
3. **テストコードを必ず含める**: ユニットテストと統合テストの両方
4. **実行可能なコードのみ**: input()は使用禁止、argparseで引数処理
5. **コメントを適切に**: 各クラス、メソッドにdocstringを記述

生成するファイル:
1. メインプログラム（janken_game_cli.py）
2. テストコード（test_janken_game.py）
3. README.md（使用方法、コマンド例）
4. requirements.txt

各ファイルの内容を明確に分けて出力してください。"""

        request = LLMRequest(
            prompt=prompt,
            system_message=system_prompt,
            request_type="code_generation",
            max_tokens=8000,
            temperature=0.3,
            preferred_provider='ollama'
        )

        response = agent.generate_text(request)

        print("\n✅ レスポンス受信")
        print("=" * 80)
        print(response.content)
        print("=" * 80)

        # 5. レスポンスを保存
        response_path = project_root / "data" / "project_plans" / "janken_game_response.txt"
        with open(response_path, 'w', encoding='utf-8') as f:
            f.write(f"Provider: {response.provider}\n")
            f.write(f"Model: {response.model}\n")
            f.write(f"Status Code: {response.status_code}\n")
            if hasattr(response, 'response_time') and response.response_time:
                f.write(f"Response Time: {response.response_time:.2f}s\n")
            if hasattr(response, 'request_timestamp') and response.request_timestamp:
                f.write(f"Timestamp: {response.request_timestamp}\n")
            f.write(f"\n{'=' * 80}\n")
            f.write(f"Response:\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(response.content)

        print(f"\n✅ レスポンスを保存: {response_path}")

        # 6. メタデータ表示
        print(f"\n[5] メタデータ:")
        print(f"   プロバイダー: {response.provider}")
        print(f"   モデル: {response.model}")
        print(f"   ステータスコード: {response.status_code}")
        if hasattr(response, 'response_time') and response.response_time:
            print(f"   レスポンス時間: {response.response_time:.2f}秒")
        if hasattr(response, 'tokens_used') and response.tokens_used:
            print(f"   トークン数: {response.tokens_used}")

        return True

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン実行"""
    try:
        success = test_mcp_janken_generation()

        if success:
            print("\n" + "=" * 80)
            print("✅ テスト成功！")
            print("=" * 80)
            print("\n次のステップ:")
            print("1. data/project_plans/janken_game_response.txt を確認")
            print("2. 生成されたコードを generated_projects/janken_game_cli/ に展開")
            print("3. テストを実行して動作確認")
            return 0
        else:
            print("\n" + "=" * 80)
            print("❌ テスト失敗")
            print("=" * 80)
            return 1

    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
