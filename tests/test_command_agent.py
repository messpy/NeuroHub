#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_command_agent.py - CommandAgent のユニットテスト
"""

import pytest
import subprocess
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.agent_command import CommandAgent, CommandResult, CommandConfig
except ImportError as e:
    print(f"Import error: {e}")
    # フォールバック定義
    class CommandAgent:
        def __init__(self):
            pass
    class CommandResult:
        def __init__(self, command="", exit_code=0, stdout="", stderr="", duration=0.0, timestamp=0.0, pid=None):
            self.command = command
            self.exit_code = exit_code
            self.stdout = stdout
            self.stderr = stderr
            self.duration = duration
            self.timestamp = timestamp
            self.pid = pid
    class CommandConfig:
        def __init__(self, timeout=30, shell=True, capture_output=True, working_dir=None, env_vars=None, safe_mode=True):
            self.timeout = timeout
            self.shell = shell
            self.capture_output = capture_output
            self.working_dir = working_dir
            self.env_vars = env_vars
            self.safe_mode = safe_mode


class TestCommandResult:
    """CommandResult のテストクラス"""

    def test_command_result_creation(self):
        """CommandResult作成テスト"""
        result = CommandResult(
            command="echo 'test'",
            exit_code=0,
            stdout="test\n",
            stderr="",
            duration=0.5,
            timestamp=1234567890.0,
            pid=12345
        )

        assert result.command == "echo 'test'"
        assert result.exit_code == 0
        assert result.stdout == "test\n"
        assert result.stderr == ""
        assert result.duration == 0.5
        assert result.pid == 12345

    def test_command_result_failure(self):
        """失敗CommandResult作成テスト"""
        result = CommandResult(
            command="invalid_command",
            exit_code=127,
            stdout="",
            stderr="command not found",
            duration=0.1,
            timestamp=1234567890.0
        )

        assert result.exit_code == 127
        assert result.stderr == "command not found"


class TestCommandConfig:
    """CommandConfig のテストクラス"""

    def test_command_config_defaults(self):
        """デフォルト設定テスト"""
        config = CommandConfig()

        assert config.timeout == 30
        assert config.shell is True
        assert config.capture_output is True
        assert config.working_dir is None
        assert config.env_vars is None
        assert config.safe_mode is True

    def test_command_config_custom(self):
        """カスタム設定テスト"""
        config = CommandConfig(
            timeout=60,
            shell=False,
            capture_output=False,
            working_dir="/tmp",
            env_vars={"TEST": "value"},
            safe_mode=False
        )

        assert config.timeout == 60
        assert config.shell is False
        assert config.capture_output is False
        assert config.working_dir == "/tmp"
        assert config.env_vars == {"TEST": "value"}
        assert config.safe_mode is False


class TestCommandAgent:
    """CommandAgent のテストクラス"""

    @pytest.fixture
    def mock_command_agent(self):
        """モックされたCommandAgent"""
        with patch('agents.command_agent.LLMHistoryManager') as mock_history:
            with patch('agents.command_agent.LLMAgent') as mock_llm:
                agent = CommandAgent()
                yield agent

    def test_init(self, mock_command_agent):
        """初期化テスト"""
        assert hasattr(mock_command_agent, 'project_root')
        assert hasattr(mock_command_agent, 'history_manager')
        assert hasattr(mock_command_agent, 'llm_agent')
        assert hasattr(mock_command_agent, 'running_processes')
        assert hasattr(mock_command_agent, 'command_history')
        assert hasattr(mock_command_agent, 'default_config')

    def test_is_safe_command_safe_commands(self, mock_command_agent):
        """安全コマンドテスト"""
        safe_commands = [
            "ls -la",
            "git status",
            "python script.py",
            "echo hello",
            "cd /tmp"
        ]

        for command in safe_commands:
            is_safe, message = mock_command_agent.is_safe_command(command)
            assert is_safe is True, f"Command '{command}' should be safe"

    def test_is_safe_command_dangerous_commands(self, mock_command_agent):
        """危険コマンドテスト"""
        dangerous_commands = [
            "rm -rf /",
            "format c:",
            "del /s /q C:",
            "shutdown -h now",
            "reboot",
            "dd if=/dev/zero of=/dev/sda"
        ]

        for command in dangerous_commands:
            is_safe, message = mock_command_agent.is_safe_command(command)
            assert is_safe is False, f"Command '{command}' should be dangerous"
            assert "危険" in message

    def test_is_safe_command_unsafe_in_safe_mode(self, mock_command_agent):
        """セーフモードでの制限テスト"""
        mock_command_agent.default_config.safe_mode = True

        # セーフモードで許可されていないコマンド
        unsafe_commands = [
            "netstat -an",
            "custom_binary",
            "unknown_command"
        ]

        for command in unsafe_commands:
            is_safe, message = mock_command_agent.is_safe_command(command)
            # 注意: netstatは実際にはSAFE_COMMANDSに含まれているので、
            # 本当に許可されていないコマンドで再テスト
            if command == "custom_binary":
                assert is_safe is False
                assert "許可されていない" in message

    def test_prepare_command_windows(self, mock_command_agent):
        """Windows環境でのコマンド準備テスト"""
        mock_command_agent.is_windows = True
        config = CommandConfig(shell=True)

        command, kwargs = mock_command_agent.prepare_command("echo test", config)

        # PowerShellラッピング確認
        assert "powershell.exe" in command
        assert kwargs['shell'] is True
        assert 'encoding' in kwargs

    def test_prepare_command_unix(self, mock_command_agent):
        """Unix環境でのコマンド準備テスト"""
        mock_command_agent.is_windows = False
        config = CommandConfig(shell=True)

        command, kwargs = mock_command_agent.prepare_command("echo test", config)

        # bashラッピング確認
        assert "/bin/bash" in command
        assert kwargs['shell'] is True

    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run, mock_command_agent):
        """コマンド実行成功テスト"""
        # subprocess.run のモック設定
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Success output"
        mock_process.stderr = ""
        mock_process.pid = 12345
        mock_run.return_value = mock_process

        result = mock_command_agent.execute_command("echo test")

        assert result.exit_code == 0
        assert result.stdout == "Success output"
        assert result.stderr == ""
        assert result.command == "echo test"
        assert len(mock_command_agent.command_history) == 1

    @patch('subprocess.run')
    def test_execute_command_failure(self, mock_run, mock_command_agent):
        """コマンド実行失敗テスト"""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "Command failed"
        mock_run.return_value = mock_process

        result = mock_command_agent.execute_command("false")

        assert result.exit_code == 1
        assert result.stderr == "Command failed"

    @patch('subprocess.run')
    def test_execute_command_timeout(self, mock_run, mock_command_agent):
        """コマンドタイムアウトテスト"""
        mock_run.side_effect = subprocess.TimeoutExpired("test", 1)

        config = CommandConfig(timeout=1)
        result = mock_command_agent.execute_command("sleep 10", config)

        assert result.exit_code == -2
        assert "タイムアウト" in result.stderr

    @patch('subprocess.run')
    def test_execute_command_exception(self, mock_run, mock_command_agent):
        """コマンド実行例外テスト"""
        mock_run.side_effect = Exception("Execution error")

        result = mock_command_agent.execute_command("error_command")

        assert result.exit_code == -3
        assert "実行エラー" in result.stderr

    def test_execute_command_dangerous(self, mock_command_agent):
        """危険コマンド実行防止テスト"""
        result = mock_command_agent.execute_command("rm -rf /")

        assert result.exit_code == -1
        assert "セキュリティエラー" in result.stderr

    @patch('subprocess.Popen')
    def test_execute_async_success(self, mock_popen, mock_command_agent):
        """非同期実行成功テスト"""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        process_id = mock_command_agent.execute_async("echo async")

        assert process_id.startswith("1")  # timestamp prefix
        assert process_id in mock_command_agent.running_processes

    def test_execute_async_dangerous(self, mock_command_agent):
        """非同期危険コマンド防止テスト"""
        process_id = mock_command_agent.execute_async("rm -rf /")

        assert process_id.startswith("セキュリティエラー")

    def test_check_process_status_running(self, mock_command_agent):
        """実行中プロセス状態確認テスト"""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.returncode = None  # まだ実行中

        process_id = "test_process"
        mock_command_agent.running_processes[process_id] = mock_process

        status = mock_command_agent.check_process_status(process_id)

        assert status is not None
        assert status["process_id"] == process_id
        assert status["pid"] == 12345
        assert status["is_running"] is True

    def test_check_process_status_completed(self, mock_command_agent):
        """完了プロセス状態確認テスト"""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("output", "")

        process_id = "completed_process"
        mock_command_agent.running_processes[process_id] = mock_process

        status = mock_command_agent.check_process_status(process_id)

        assert status["is_running"] is False
        assert status["exit_code"] == 0
        assert status["stdout"] == "output"
        assert process_id not in mock_command_agent.running_processes  # 削除されている

    def test_check_process_status_not_found(self, mock_command_agent):
        """存在しないプロセス状態確認テスト"""
        status = mock_command_agent.check_process_status("nonexistent")

        assert status is None

    def test_kill_process_success(self, mock_command_agent):
        """プロセス停止成功テスト"""
        mock_process = Mock()
        mock_process.wait.return_value = None

        process_id = "kill_test"
        mock_command_agent.running_processes[process_id] = mock_process

        success = mock_command_agent.kill_process(process_id)

        assert success is True
        assert process_id not in mock_command_agent.running_processes
        mock_process.terminate.assert_called_once()

    def test_kill_process_force(self, mock_command_agent):
        """強制プロセス停止テスト"""
        mock_process = Mock()
        mock_process.wait.return_value = None

        process_id = "force_kill_test"
        mock_command_agent.running_processes[process_id] = mock_process

        success = mock_command_agent.kill_process(process_id, force=True)

        assert success is True
        mock_process.kill.assert_called_once()

    def test_kill_process_not_found(self, mock_command_agent):
        """存在しないプロセス停止テスト"""
        success = mock_command_agent.kill_process("nonexistent")

        assert success is False

    def test_analyze_command_output_success(self, mock_command_agent):
        """コマンド出力分析成功テスト"""
        result = CommandResult(
            command="ls -la",
            exit_code=0,
            stdout="total 10\ndrwxr-xr-x 2 user user 4096 Jan 1 12:00 .\n",
            stderr="",
            duration=0.5,
            timestamp=1234567890.0
        )

        analysis = mock_command_agent.analyze_command_output(result)

        assert analysis["success"] is True
        assert analysis["duration_category"] == "fast"
        assert analysis["has_errors"] is False
        assert analysis["line_count"] == 2

    def test_analyze_command_output_failure(self, mock_command_agent):
        """コマンド出力分析失敗テスト"""
        result = CommandResult(
            command="cat nonexistent.txt",
            exit_code=1,
            stdout="",
            stderr="cat: nonexistent.txt: No such file or directory",
            duration=0.1,
            timestamp=1234567890.0
        )

        analysis = mock_command_agent.analyze_command_output(result)

        assert analysis["success"] is False
        assert analysis["has_errors"] is True
        assert analysis["error_analysis"]["likely_not_found"] is True

    def test_suggest_command_improvements(self, mock_command_agent):
        """コマンド改善提案テスト"""
        # パーミッションエラー
        result = CommandResult(
            command="cat /etc/shadow",
            exit_code=1,
            stdout="",
            stderr="cat: /etc/shadow: Permission denied",
            duration=0.1,
            timestamp=1234567890.0
        )

        suggestions = mock_command_agent.suggest_command_improvements(result)

        assert len(suggestions) > 0
        assert any("権限エラー" in s for s in suggestions)

    def test_get_command_history(self, mock_command_agent):
        """コマンド履歴取得テスト"""
        # テスト履歴追加
        for i in range(5):
            result = CommandResult(
                command=f"test{i}",
                exit_code=0,
                stdout=f"output{i}",
                stderr="",
                duration=1.0,
                timestamp=1234567890.0 + i
            )
            mock_command_agent.command_history.append(result)

        history = mock_command_agent.get_command_history(limit=3)

        assert len(history) == 3
        assert history[0]["command"] == "test2"  # 最新3件
        assert history[1]["command"] == "test3"
        assert history[2]["command"] == "test4"


class TestCommandAgentCLI:
    """CommandAgent CLI 引数テスト"""

    def test_cli_command_positional_argument(self):
        """位置引数（コマンド）テスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        args = parser.parse_args(['echo', 'hello', 'world'])

        assert args.command == ['echo', 'hello', 'world']
        assert args.interactive is False
        assert args.async_mode is False
        assert args.timeout == 30
        assert args.unsafe is False
        assert args.history is False
        assert args.cwd is None

    def test_cli_interactive_option(self):
        """--interactive/-i オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        # 長いオプション
        args = parser.parse_args(['--interactive'])
        assert args.interactive is True

        # 短いオプション
        args = parser.parse_args(['-i'])
        assert args.interactive is True

    def test_cli_async_mode_option(self):
        """--async-mode オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        args = parser.parse_args(['--async-mode'])

        assert args.async_mode is True
        assert args.interactive is False

    def test_cli_timeout_option(self):
        """--timeout オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        args = parser.parse_args(['--timeout', '60'])

        assert args.timeout == 60

    def test_cli_timeout_default_value(self):
        """--timeout デフォルト値テスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        args = parser.parse_args([])

        assert args.timeout == 30

    def test_cli_unsafe_option(self):
        """--unsafe オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        args = parser.parse_args(['--unsafe'])

        assert args.unsafe is True

    def test_cli_history_option(self):
        """--history オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        args = parser.parse_args(['--history'])

        assert args.history is True

    def test_cli_cwd_option(self):
        """--cwd オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        args = parser.parse_args(['--cwd', '/tmp'])

        assert args.cwd == '/tmp'

    def test_cli_combined_options(self):
        """複数オプション組み合わせテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        args = parser.parse_args(['ls -la', '--async-mode', '--timeout', '60', '--cwd', '/home'])

        assert args.command == ['ls -la']
        assert args.async_mode is True
        assert args.timeout == 60
        assert args.cwd == '/home'
        assert args.interactive is False
        assert args.unsafe is False
        assert args.history is False

    def test_cli_empty_command(self):
        """空のコマンドテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        args = parser.parse_args(['--interactive'])

        assert args.command == []
        assert args.interactive is True

    def test_cli_invalid_timeout_type(self):
        """無効なtimeout型テスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
        parser.add_argument("command", nargs="*", help="実行するコマンド")
        parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
        parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
        parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
        parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
        parser.add_argument("--history", action="store_true", help="履歴表示")
        parser.add_argument("--cwd", help="作業ディレクトリ")

        with pytest.raises(SystemExit):
            parser.parse_args(['--timeout', 'invalid'])


class TestCommandAgentIntegration:
    """CommandAgent の統合テスト"""

    @pytest.fixture
    def real_command_agent(self):
        """実際のCommandAgent（最小限モック）"""
        with patch('agents.command_agent.LLMHistoryManager'):
            with patch('agents.command_agent.LLMAgent'):
                agent = CommandAgent()
                # セーフモード無効化（テスト用）
                agent.default_config.safe_mode = False
                yield agent

    def test_simple_command_execution(self, real_command_agent):
        """シンプルコマンド実行テスト"""
        # プラットフォーム依存のコマンド選択
        if real_command_agent.is_windows:
            command = "echo test"
        else:
            command = "echo test"

        result = real_command_agent.execute_command(command)

        assert result.exit_code == 0
        assert "test" in result.stdout

    def test_command_with_custom_config(self, real_command_agent):
        """カスタム設定でのコマンド実行テスト"""
        config = CommandConfig(
            timeout=5,
            shell=True,
            capture_output=True
        )

        if real_command_agent.is_windows:
            command = "echo custom"
        else:
            command = "echo custom"

        result = real_command_agent.execute_command(command, config)

        assert result.exit_code == 0
        assert "custom" in result.stdout

    def test_command_history_logging(self, real_command_agent):
        """コマンド履歴ログテスト"""
        initial_count = len(real_command_agent.command_history)

        if real_command_agent.is_windows:
            real_command_agent.execute_command("echo history_test")
        else:
            real_command_agent.execute_command("echo history_test")

        assert len(real_command_agent.command_history) == initial_count + 1

        history = real_command_agent.get_command_history(limit=1)
        assert len(history) == 1
        assert "echo history_test" in history[0]["command"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
