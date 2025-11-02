#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Agent テスト
"""

import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.agent_mcp import MCPAgent, MCPRequest, MCPResult


@pytest.fixture
def mcp_agent():
    """MCPエージェント"""
    return MCPAgent(provider='ollama', model='qwen2.5-coder:3b')


@pytest.fixture
def temp_output_dir(tmp_path):
    """一時出力ディレクトリ"""
    output_dir = tmp_path / "mcp_output"
    output_dir.mkdir()
    return output_dir


class TestMCPAgentInit:
    """初期化テスト"""

    def test_init(self, mcp_agent):
        """初期化テスト"""
        assert mcp_agent is not None
        assert mcp_agent.provider == 'ollama'
        assert mcp_agent.llm_agent is not None
        assert mcp_agent.db_agent is not None


class TestCodeGeneration:
    """コード生成テスト"""

    def test_simple_code_generation(self, mcp_agent, temp_output_dir):
        """シンプルなコード生成"""
        output_file = temp_output_dir / "hello.py"

        request = MCPRequest(
            mode='generate',
            prompt="print('Hello, World!')を含むシンプルなPythonスクリプト",
            output_path=str(output_file),
            temperature=0.1,
            max_tokens=500
        )

        result = mcp_agent.execute(request)

        assert result.success is True
        assert len(result.files_created) == 1
        assert output_file.exists()

        content = output_file.read_text(encoding='utf-8')
        assert 'print' in content or 'Hello' in content

    def test_function_generation(self, mcp_agent, temp_output_dir):
        """関数生成テスト"""
        output_file = temp_output_dir / "fibonacci.py"

        request = MCPRequest(
            mode='generate',
            prompt="フィボナッチ数列を計算する関数を作成してください",
            output_path=str(output_file),
            language='python',
            temperature=0.2,
            max_tokens=1000
        )

        result = mcp_agent.execute(request)

        assert result.success is True
        assert output_file.exists()

        content = output_file.read_text(encoding='utf-8')
        assert 'def' in content
        assert 'fibonacci' in content.lower() or 'fib' in content.lower()

    def test_with_hints(self, mcp_agent, temp_output_dir):
        """ヒント使用テスト"""
        output_file = temp_output_dir / "db_example.py"

        request = MCPRequest(
            mode='generate',
            prompt="SQLiteデータベースにユーザーを追加する関数",
            output_path=str(output_file),
            use_hints=True,
            temperature=0.3,
            max_tokens=1500
        )

        result = mcp_agent.execute(request)

        assert result.success is True
        assert output_file.exists()


class TestProjectGeneration:
    """プロジェクト生成テスト"""

    def test_cli_project_generation(self, mcp_agent):
        """CLIプロジェクト生成"""
        request = MCPRequest(
            mode='project',
            prompt="ファイルの行数をカウントするCLIツール",
            project_name="line_counter_test",
            project_type='cli',
            include_tests=True,
            include_docs=True,
            temperature=0.3,
            max_tokens=4000
        )

        result = mcp_agent.execute(request)

        assert result.success is True
        assert len(result.files_created) >= 2  # メインファイル + README

        # プロジェクトディレクトリ確認
        project_dir = project_root / "generated_projects" / "line_counter_test"
        assert project_dir.exists()

        main_file = project_dir / "line_counter_test.py"
        assert main_file.exists()

        # クリーンアップ
        import shutil
        shutil.rmtree(project_dir)

    def test_minimal_project(self, mcp_agent):
        """最小プロジェクト生成（テスト・ドキュメントなし）"""
        request = MCPRequest(
            mode='project',
            prompt="数値を2倍にする関数",
            project_name="double_test",
            include_tests=False,
            include_docs=False,
            temperature=0.1,
            max_tokens=1000
        )

        result = mcp_agent.execute(request)

        assert result.success is True
        assert len(result.files_created) >= 1

        # クリーンアップ
        project_dir = project_root / "generated_projects" / "double_test"
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)


class TestDebugMode:
    """デバッグモードテスト"""

    def test_debug_simple_error(self, mcp_agent, temp_output_dir):
        """シンプルなエラー修正"""
        buggy_code = """
def add(a, b):
    return a + b + c  # cが未定義
"""

        output_file = temp_output_dir / "fixed.py"

        request = MCPRequest(
            mode='debug',
            prompt=f"以下のコードのエラーを修正してください:\n{buggy_code}",
            output_path=str(output_file),
            temperature=0.1,
            max_tokens=1000
        )

        result = mcp_agent.execute(request)

        assert result.success is True
        assert output_file.exists()

        fixed_code = output_file.read_text(encoding='utf-8')
        assert 'def add' in fixed_code


class TestOptimizeMode:
    """プロンプト最適化テスト"""

    def test_prompt_optimization(self, mcp_agent):
        """プロンプト最適化"""
        request = MCPRequest(
            mode='optimize',
            prompt="計算機を作って",
            temperature=0.5,
            max_tokens=1500
        )

        result = mcp_agent.execute(request)

        assert result.success is True
        assert len(result.content) > len(request.prompt)
        assert '計算機' in result.content or 'calculator' in result.content.lower()


class TestDesignMode:
    """設計書参照モードテスト"""

    def test_design_based_generation(self, mcp_agent, temp_output_dir):
        """設計書ベース生成"""
        # 簡易設計書作成
        design_file = temp_output_dir / "design.md"
        design_file.write_text("""
# Todo管理システム設計

## 機能
- Todoアイテムの追加
- Todoアイテムの削除
- Todoアイテムの完了マーク

## データ構造
- id: 整数
- title: 文字列
- completed: 真偽値
""", encoding='utf-8')

        output_file = temp_output_dir / "todo.py"

        request = MCPRequest(
            mode='design',
            prompt="Todo管理クラスを実装してください",
            output_path=str(output_file),
            reference_docs=[str(design_file)],
            temperature=0.3,
            max_tokens=3000
        )

        result = mcp_agent.execute(request)

        assert result.success is True
        assert output_file.exists()

        code = output_file.read_text(encoding='utf-8')
        assert 'class' in code or 'def' in code


class TestHelperMethods:
    """ヘルパーメソッドテスト"""

    def test_extract_code(self, mcp_agent):
        """コード抽出テスト"""
        # コードフェンス付き
        text_with_fence = """
説明文

```python
def hello():
    print("Hello")
```

追加説明
"""

        code = mcp_agent._extract_code(text_with_fence)
        assert 'def hello' in code
        assert '```' not in code

    def test_extract_code_no_fence(self, mcp_agent):
        """コードフェンスなし"""
        text = "def hello():\n    print('Hello')"

        code = mcp_agent._extract_code(text)
        assert code == text.strip()

    def test_validate_code(self, mcp_agent):
        """コードバリデーション"""
        # 完全なコード
        good_code = '''
import os

def process():
    """処理を実行"""
    try:
        return True
    except Exception as e:
        print(e)
'''

        warnings = mcp_agent._validate_code(good_code, 'python')
        assert len(warnings) == 0

        # 不完全なコード
        bad_code = '''
x = 1
y = 2
'''

        warnings = mcp_agent._validate_code(bad_code, 'python')
        assert len(warnings) > 0

    def test_extract_requirements(self, mcp_agent):
        """依存ライブラリ抽出"""
        code = '''
import os
import sys
import requests
from flask import Flask
import numpy as np
'''

        requirements = mcp_agent._extract_requirements(code)
        assert 'requests' in requirements
        assert 'flask' in requirements.lower()
        assert 'numpy' in requirements
        assert 'os' not in requirements  # 標準ライブラリは除外
        assert 'sys' not in requirements


class TestErrorHandling:
    """エラーハンドリングテスト"""

    def test_invalid_mode(self, mcp_agent):
        """無効なモード"""
        request = MCPRequest(
            mode='invalid_mode',
            prompt="test"
        )

        result = mcp_agent.execute(request)

        assert result.success is False
        assert len(result.errors) > 0

    def test_missing_project_name(self, mcp_agent):
        """プロジェクト名なし"""
        request = MCPRequest(
            mode='project',
            prompt="test project"
        )

        result = mcp_agent.execute(request)

        assert result.success is False
        assert 'project_name' in result.errors[0]

    def test_missing_design_docs(self, mcp_agent, temp_output_dir):
        """設計書なし"""
        request = MCPRequest(
            mode='design',
            prompt="test",
            reference_docs=["/nonexistent/file.md"]
        )

        result = mcp_agent.execute(request)

        assert result.success is False
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
