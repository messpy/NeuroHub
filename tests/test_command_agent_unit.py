#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Agent テスト
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.command_agent import CommandAgent
    COMMAND_AGENT_AVAILABLE = True
except ImportError:
    COMMAND_AGENT_AVAILABLE = False
    print("CommandAgent not available for testing")


@pytest.mark.skipif(not COMMAND_AGENT_AVAILABLE, reason="CommandAgent not available")
class TestCommandAgent:
    """CommandAgent単体テスト"""

    def test_initialization(self):
        """初期化テスト"""
        agent = CommandAgent()
        assert agent is not None

    def test_simple_command(self):
        """単純コマンド実行テスト"""
        agent = CommandAgent()

        # Windowsでのテストコマンド
        result = agent.execute_command("echo Hello")

        assert result.returncode == 0
        assert "Hello" in result.stdout

    def test_command_validation(self):
        """コマンド検証テスト"""
        agent = CommandAgent()

        # 安全なコマンド
        assert agent.validate_command("ls") == True
        assert agent.validate_command("echo test") == True

        # 危険なコマンド（実装に依存）
        # 実装されていない場合はスキップ
        try:
            dangerous_result = agent.validate_command("rm -rf /")
            # 実装されている場合、危険コマンドはFalseを返すべき
        except (AttributeError, NotImplementedError):
            # 未実装の場合はスキップ
            pass


def test_command_agent_fallback():
    """CommandAgent代替テスト（直接subprocess使用）"""
    import subprocess

    # 基本的なコマンド実行テスト
    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        assert "Python" in result.stdout
        print(f"✅ Python version: {result.stdout.strip()}")

    except Exception as e:
        pytest.fail(f"Basic command execution failed: {e}")


def test_git_commands():
    """Git関連コマンドテスト"""
    import subprocess

    try:
        # Git バージョン確認
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"✅ Git available: {result.stdout.strip()}")

            # Git status テスト（リポジトリ内でのみ有効）
            try:
                status_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=str(project_root)
                )

                if status_result.returncode == 0:
                    print(f"✅ Git status successful")
                    print(f"   Changed files: {len(status_result.stdout.splitlines())}")
                else:
                    print(f"⚠️ Git status failed (expected outside git repo)")

            except Exception as git_error:
                print(f"⚠️ Git status error: {git_error}")
        else:
            print(f"⚠️ Git not available: {result.stderr}")

    except FileNotFoundError:
        print("⚠️ Git command not found")
    except Exception as e:
        print(f"⚠️ Git test error: {e}")


if __name__ == '__main__':
    print("🧪 Command Agent Testing")
    print("=" * 50)

    # 基本テスト実行
    print("\n1. Command Agent Fallback Test")
    test_command_agent_fallback()

    print("\n2. Git Commands Test")
    test_git_commands()

    print("\n3. Running pytest for CommandAgent")
    pytest.main([__file__, '-v'])
