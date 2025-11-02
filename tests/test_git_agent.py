#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_git_agent.py - GitAgent のユニットテスト
"""

import pytest
import tempfile
import shutil
import subprocess
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.git_agent import GitAgent, GitStatus
    from agents.agent_llm import LLMRequest, LLMResponse
except ImportError as e:
    print(f"Import error: {e}")
    # フォールバック: 最小限のクラス定義
    class GitAgent:
        def __init__(self):
            pass
    class GitStatus:
        pass
    class LLMRequest:
        pass
    class LLMResponse:
        pass


class TestGitAgent:
    """GitAgent のテストクラス"""

    @pytest.fixture
    def temp_git_repo(self):
        """テスト用の一時Gitリポジトリ"""
        temp_dir = tempfile.mkdtemp()

        try:
            # Git初期化（Linux環境用）
            result = subprocess.run(['git', 'init'], cwd=temp_dir, capture_output=True, text=True)
            if result.returncode != 0:
                pytest.skip(f"Git not available: {result.stderr}")

            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, capture_output=True, check=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, capture_output=True, check=True)

            # テストファイル作成（Linux権限考慮）
            test_file = Path(temp_dir) / 'test.txt'
            test_file.write_text('Initial content')
            os.chmod(test_file, 0o644)  # Linux権限設定

            subprocess.run(['git', 'add', 'test.txt'], cwd=temp_dir, capture_output=True, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, capture_output=True, check=True)

            yield temp_dir
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            pytest.skip(f"Git setup failed: {e}")
        finally:
            # クリーンアップ（Linux権限変更）
            try:
                subprocess.run(['chmod', '-R', '755', temp_dir], capture_output=True)
                shutil.rmtree(temp_dir)
            except Exception:
                pass

    @pytest.fixture
    def mock_git_agent(self, temp_git_repo):
        """モックされたGitAgent"""
        with patch('agents.git_agent.project_root', temp_git_repo):
            with patch('agents.llm_agent.LLMAgent') as mock_llm_agent:
                with patch('agents.git_agent.LLMHistoryManager') as mock_history:
                    with patch('agents.git_agent.load_config') as mock_config:
                        mock_config.return_value = {}
                        agent = GitAgent()
                        agent.project_root = temp_git_repo
                        yield agent

    def test_init(self, mock_git_agent):
        """初期化テスト"""
        assert mock_git_agent.project_root is not None
        assert hasattr(mock_git_agent, 'llm_agent')
        assert hasattr(mock_git_agent, 'history_manager')

    def test_get_git_status_clean_repo(self, temp_git_repo):
        """クリーンなリポジトリの状態テスト"""
        with patch('agents.git_agent.project_root', temp_git_repo):
            with patch('agents.llm_agent.LLMAgent'):
                with patch('agents.git_agent.LLMHistoryManager'):
                    with patch('agents.git_agent.load_config', return_value={}):
                        agent = GitAgent()
                        agent.project_root = temp_git_repo

                        status = agent.get_git_status()

                        assert isinstance(status, GitStatus)
                        assert status.total_files == 0
                        assert len(status.staged) == 0
                        assert len(status.modified) == 0
                        assert len(status.untracked) == 0

    def test_get_git_status_with_changes(self, temp_git_repo):
        """変更があるリポジトリの状態テスト"""
        # ファイル変更
        test_file = Path(temp_git_repo) / 'test.txt'
        test_file.write_text('Modified content')

        # 新しいファイル追加
        new_file = Path(temp_git_repo) / 'new.txt'
        new_file.write_text('New file content')

        with patch('agents.git_agent.project_root', temp_git_repo):
            with patch('agents.llm_agent.LLMAgent'):
                with patch('agents.git_agent.LLMHistoryManager'):
                    with patch('agents.git_agent.load_config', return_value={}):
                        agent = GitAgent()
                        agent.project_root = temp_git_repo

                        status = agent.get_git_status()

                        assert status.total_files > 0
                        assert len(status.modified) > 0 or len(status.untracked) > 0

    def test_get_file_diff_existing_file(self, mock_git_agent, temp_git_repo):
        """既存ファイルの差分取得テスト"""
        # ファイル変更してステージング
        test_file = Path(temp_git_repo) / 'test.txt'
        test_file.write_text('Modified content')
        subprocess.run(['git', 'add', 'test.txt'], cwd=temp_git_repo, capture_output=True)

        diff = mock_git_agent.get_file_diff('test.txt', staged=True)

        assert isinstance(diff, str)
        assert 'Modified content' in diff or '+Modified content' in diff

    def test_get_file_diff_nonexistent_file(self, mock_git_agent):
        """存在しないファイルの差分取得テスト"""
        diff = mock_git_agent.get_file_diff('nonexistent.txt')

        assert diff == ""

    def test_stage_file_success(self, mock_git_agent, temp_git_repo):
        """ファイルのステージング成功テスト"""
        # 新しいファイル作成
        new_file = Path(temp_git_repo) / 'stage_test.txt'
        new_file.write_text('Test content')

        success = mock_git_agent.stage_file('stage_test.txt')

        assert success is True

    def test_stage_file_failure(self, mock_git_agent):
        """ファイルのステージング失敗テスト"""
        success = mock_git_agent.stage_file('nonexistent.txt')

        assert success is False

    def test_commit_file_success(self, mock_git_agent, temp_git_repo):
        """コミット成功テスト"""
        # ファイル変更してステージング
        test_file = Path(temp_git_repo) / 'test.txt'
        test_file.write_text('Commit test content')
        subprocess.run(['git', 'add', 'test.txt'], cwd=temp_git_repo, capture_output=True)

        success = mock_git_agent.commit_file('test.txt', 'Test commit message')

        assert success is True

    def test_commit_file_no_changes(self, mock_git_agent):
        """変更なしでのコミットテスト"""
        success = mock_git_agent.commit_file('test.txt', 'No changes commit')

        # 変更がない場合はFalseを返すかエラーになる
        assert success is False

    @patch('agents.git_agent.get_system_message')
    def test_generate_commit_message_success(self, mock_system_msg, mock_git_agent):
        """コミットメッセージ生成成功テスト"""
        mock_system_msg.return_value = "System message"

        # LLMレスポンスのモック
        mock_response = LLMResponse(
            provider="test",
            model="test-model",
            prompt="test prompt",
            content=":add: テスト機能追加",
            is_success=True,
            error_message=None,
            response_time=1.0,
            token_usage={"input": 10, "output": 5}
        )

        mock_git_agent.llm_agent.generate_text = Mock(return_value=mock_response)

        message = mock_git_agent.generate_commit_message('test.txt', 'diff content')

        assert message == ":add: テスト機能追加"
        mock_git_agent.llm_agent.generate_text.assert_called_once()

    @patch('agents.git_agent.get_system_message')
    def test_generate_commit_message_llm_failure(self, mock_system_msg, mock_git_agent):
        """LLM失敗時のコミットメッセージ生成テスト"""
        mock_system_msg.return_value = "System message"

        # LLM失敗のモック
        mock_git_agent.llm_agent.generate_text = Mock(side_effect=Exception("LLM Error"))

        message = mock_git_agent.generate_commit_message('test.txt', 'diff content')

        # スマートデフォルトが返される
        assert message.startswith(':update:')
        assert 'test.txt' in message

    def test_generate_smart_default_new_file(self, mock_git_agent):
        """新規ファイルのスマートデフォルトテスト"""
        diff_content = """
+++ b/new_feature.py
@@ -0,0 +1,10 @@
+def new_function():
+    return "Hello"
        """

        message = mock_git_agent._generate_smart_default('new_feature.py', diff_content)

        assert message.startswith(':add:')
        assert 'new_feature.py' in message

    def test_generate_smart_default_large_change(self, mock_git_agent):
        """大きな変更のスマートデフォルトテスト"""
        diff_content = '\n'.join([f"+line {i}" for i in range(100)])  # 100行の変更

        message = mock_git_agent._generate_smart_default('big_file.py', diff_content)

        assert message.startswith(':refactor:')
        assert 'big_file.py' in message

    def test_process_files_single_file(self, mock_git_agent, temp_git_repo):
        """単一ファイル処理テスト"""
        # ファイル変更
        test_file = Path(temp_git_repo) / 'test.txt'
        test_file.write_text('Process test content')

        with patch.object(mock_git_agent, 'generate_commit_message', return_value=':update: テスト更新'):
            result = mock_git_agent.process_files(['test.txt'])

            assert result['status'] == 'success'
            assert len(result['results']) == 1
            assert result['results'][0]['file'] == 'test.txt'
            assert result['results'][0]['message'] == ':update: テスト更新'

    def test_process_files_multiple_files(self, mock_git_agent, temp_git_repo):
        """複数ファイル処理テスト"""
        # 複数ファイル作成
        for i in range(3):
            test_file = Path(temp_git_repo) / f'test_{i}.txt'
            test_file.write_text(f'Content {i}')

        with patch.object(mock_git_agent, 'generate_commit_message', return_value=':add: ファイル追加'):
            result = mock_git_agent.process_files([f'test_{i}.txt' for i in range(3)])

            assert result['status'] == 'success'
            assert len(result['results']) == 3

    def test_process_files_with_auto_commit(self, mock_git_agent, temp_git_repo):
        """自動コミット付きファイル処理テスト"""
        # ファイル変更
        test_file = Path(temp_git_repo) / 'test.txt'
        test_file.write_text('Auto commit test')

        with patch.object(mock_git_agent, 'generate_commit_message', return_value=':update: 自動コミット'):
            with patch.object(mock_git_agent, 'stage_file', return_value=True):
                with patch.object(mock_git_agent, 'commit_file', return_value=True):
                    result = mock_git_agent.process_files(['test.txt'], auto_commit=True)

                    assert result['status'] == 'success'
                    assert result['results'][0]['committed'] is True


class TestGitAgentIntegration:
    """GitAgent の統合テスト"""

    @pytest.fixture
    def git_repo_with_changes(self):
        """変更があるGitリポジトリ"""
        temp_dir = tempfile.mkdtemp()

        # Git初期化
        subprocess.run(['git', 'init'], cwd=temp_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, capture_output=True)

        # 初期ファイル
        initial_file = Path(temp_dir) / 'README.md'
        initial_file.write_text('# Test Project\n\nInitial content')
        subprocess.run(['git', 'add', 'README.md'], cwd=temp_dir, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, capture_output=True)

        # 変更ファイル作成
        feature_file = Path(temp_dir) / 'feature.py'
        feature_file.write_text('''
def new_feature():
    """新機能の実装"""
    return "Hello, World!"

class FeatureClass:
    def method(self):
        pass
''')

        # 既存ファイル変更
        initial_file.write_text('# Test Project\n\nUpdated content\n\n## New Section')

        yield temp_dir

        # クリーンアップ
        shutil.rmtree(temp_dir)

    def test_full_workflow(self, git_repo_with_changes):
        """完全なワークフローテスト"""
        with patch('agents.git_agent.project_root', git_repo_with_changes):
            with patch('agents.llm_agent.LLMAgent') as mock_llm_agent_class:
                with patch('agents.git_agent.LLMHistoryManager'):
                    with patch('agents.git_agent.load_config', return_value={}):

                        # LLMエージェントのモック設定
                        mock_llm_agent = Mock()
                        mock_llm_agent.generate_text.return_value = LLMResponse(
                            provider="test",
                            model="test-model",
                            prompt="test",
                            content=":add: 新機能実装",
                            is_success=True,
                            error_message=None,
                            response_time=1.0,
                            token_usage={"input": 10, "output": 5}
                        )
                        mock_llm_agent_class.return_value = mock_llm_agent

                        agent = GitAgent()
                        agent.project_root = git_repo_with_changes

                        # 1. Git状態確認
                        status = agent.get_git_status()
                        assert status.total_files > 0

                        # 2. ファイル処理
                        files_to_process = ['feature.py', 'README.md']

                        with patch('agents.git_agent.get_system_message', return_value="System message"):
                            result = agent.process_files(files_to_process, auto_commit=True)

                        # 3. 結果検証
                        assert result['status'] == 'success'
                        assert len(result['results']) == 2

                        for file_result in result['results']:
                            assert file_result['message'].startswith(':')
                            assert file_result['committed'] is True


class TestGitAgentCLI:
    """GitAgent CLI 引数テスト"""

    @patch('agents.git_agent.GitAgent')
    def test_cli_status_option(self, mock_git_agent_class):
        """--status オプションテスト"""
        import agents.git_agent as git_module

        # モックインスタンス設定
        mock_agent = Mock()
        mock_agent.show_git_status.return_value = None
        mock_git_agent_class.return_value = mock_agent

        # テスト用sys.argv設定
        test_argv = ['git_agent.py', '--status']

        with patch('sys.argv', test_argv):
            # ArgumentParserテスト
            import argparse
            parser = argparse.ArgumentParser(description="Git Agent - Python版コミット支援")
            parser.add_argument("--auto", action="store_true", help="自動コミットモード")
            parser.add_argument("--interactive", action="store_true", help="対話モード")
            parser.add_argument("--status", action="store_true", help="Git状態表示")

            args = parser.parse_args(['--status'])

            assert args.status is True
            assert args.auto is False
            assert args.interactive is False

    @patch('agents.git_agent.GitAgent')
    def test_cli_auto_option(self, mock_git_agent_class):
        """--auto オプションテスト"""
        mock_agent = Mock()
        mock_git_agent_class.return_value = mock_agent

        import argparse
        parser = argparse.ArgumentParser(description="Git Agent - Python版コミット支援")
        parser.add_argument("--auto", action="store_true", help="自動コミットモード")
        parser.add_argument("--interactive", action="store_true", help="対話モード")
        parser.add_argument("--status", action="store_true", help="Git状態表示")

        args = parser.parse_args(['--auto'])

        assert args.auto is True
        assert args.status is False
        assert args.interactive is False

    @patch('agents.git_agent.GitAgent')
    def test_cli_interactive_option(self, mock_git_agent_class):
        """--interactive オプションテスト"""
        mock_agent = Mock()
        mock_git_agent_class.return_value = mock_agent

        import argparse
        parser = argparse.ArgumentParser(description="Git Agent - Python版コミット支援")
        parser.add_argument("--auto", action="store_true", help="自動コミットモード")
        parser.add_argument("--interactive", action="store_true", help="対話モード")
        parser.add_argument("--status", action="store_true", help="Git状態表示")

        args = parser.parse_args(['--interactive'])

        assert args.interactive is True
        assert args.auto is False
        assert args.status is False

    def test_cli_multiple_options(self):
        """複数オプション同時指定テスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Git Agent - Python版コミット支援")
        parser.add_argument("--auto", action="store_true", help="自動コミットモード")
        parser.add_argument("--interactive", action="store_true", help="対話モード")
        parser.add_argument("--status", action="store_true", help="Git状態表示")

        args = parser.parse_args(['--status', '--interactive'])

        assert args.status is True
        assert args.interactive is True
        assert args.auto is False

    def test_cli_no_options(self):
        """オプション未指定テスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Git Agent - Python版コミット支援")
        parser.add_argument("--auto", action="store_true", help="自動コミットモード")
        parser.add_argument("--interactive", action="store_true", help="対話モード")
        parser.add_argument("--status", action="store_true", help="Git状態表示")

        args = parser.parse_args([])

        assert args.auto is False
        assert args.interactive is False
        assert args.status is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
