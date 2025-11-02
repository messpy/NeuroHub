#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Agent - コマンド実行エージェント
安全なコマンド実行、履歴管理、結果分析
"""

import os
import sys
import subprocess
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
import shlex
import signal
import threading

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.db.llm_history_manager import LLMHistoryManager
from agents.agent_llm import LLMAgent


@dataclass
class CommandResult:
    """コマンド実行結果"""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timestamp: float
    pid: Optional[int] = None
    signal_used: Optional[int] = None


@dataclass
class CommandConfig:
    """コマンド設定"""
    timeout: int = 30
    shell: bool = True
    capture_output: bool = True
    working_dir: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    safe_mode: bool = True


class CommandAgent:
    """コマンド実行エージェント"""

    # 危険なコマンドパターン
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'format\s+[c-z]:',
        r'del\s+/[sq]',
        r'shutdown',
        r'reboot',
        r'halt',
        r'systemctl\s+stop',
        r'service\s+.*\s+stop',
        r'kill\s+-9\s+1',
        r'dd\s+if=.*of=/dev/',
        r'fdisk',
        r'mkfs',
        r'mount.*umount'
    ]

    # 許可されたコマンド（セーフモード）
    SAFE_COMMANDS = [
        'ls', 'dir', 'pwd', 'cd', 'cat', 'type', 'echo', 'find', 'grep',
        'git', 'python', 'pip', 'npm', 'node', 'curl', 'wget',
        'ps', 'top', 'netstat', 'ping', 'tracert', 'nslookup',
        'head', 'tail', 'wc', 'sort', 'uniq', 'cut', 'awk', 'sed',
        'cp', 'copy', 'mv', 'move', 'mkdir', 'touch', 'which', 'where'
    ]

    def __init__(self):
        self.project_root = project_root
        self.history_manager = LLMHistoryManager()
        self.llm_agent = LLMAgent()

        # 実行中プロセス管理
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.command_history: List[CommandResult] = []

        # デフォルト設定
        self.default_config = CommandConfig()

        # プラットフォーム検出
        self.is_windows = os.name == 'nt'
        self.shell_command = 'powershell.exe' if self.is_windows else '/bin/bash'

    def is_safe_command(self, command: str) -> Tuple[bool, str]:
        """コマンドの安全性チェック"""
        import re

        # 危険パターンチェック
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"危険なパターンを検出: {pattern}"

        # セーフモードの場合、許可コマンドのみ
        if self.default_config.safe_mode:
            command_parts = shlex.split(command) if not self.is_windows else command.split()
            if command_parts:
                base_command = command_parts[0].lower()
                # パスを除去してコマンド名のみ取得
                base_command = os.path.basename(base_command).replace('.exe', '')

                if base_command not in self.SAFE_COMMANDS:
                    return False, f"セーフモードで許可されていないコマンド: {base_command}"

        return True, "安全"

    def prepare_command(self, command: str, config: CommandConfig) -> Tuple[str, Dict[str, Any]]:
        """コマンド実行準備"""

        # 環境変数準備
        env = os.environ.copy()
        if config.env_vars:
            env.update(config.env_vars)

        # 作業ディレクトリ設定
        cwd = config.working_dir or str(self.project_root)

        # プラットフォーム別コマンド調整
        if self.is_windows:
            if config.shell:
                # PowerShellコマンドラッピング
                if not command.startswith('powershell'):
                    command = f'powershell.exe -Command "{command}"'
        else:
            if config.shell and not command.startswith('/bin/'):
                command = f'/bin/bash -c "{command}"'

        # subprocess引数
        kwargs = {
            'shell': config.shell,
            'cwd': cwd,
            'env': env,
            'timeout': config.timeout
        }

        if config.capture_output:
            kwargs.update({
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True,
                'encoding': 'utf-8',
                'errors': 'replace'
            })

        return command, kwargs

    def execute_command(self, command: str, config: Optional[CommandConfig] = None) -> CommandResult:
        """コマンド実行"""

        if config is None:
            config = self.default_config

        start_time = time.time()

        # 安全性チェック
        is_safe, safety_msg = self.is_safe_command(command)
        if not is_safe:
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"セキュリティエラー: {safety_msg}",
                duration=0,
                timestamp=start_time
            )

        try:
            # コマンド準備
            prepared_command, kwargs = self.prepare_command(command, config)

            print(f"🔧 コマンド実行: {command}")
            if config.working_dir:
                print(f"   作業ディレクトリ: {config.working_dir}")

            # 実行
            process = subprocess.run(prepared_command, **kwargs)

            duration = time.time() - start_time

            result = CommandResult(
                command=command,
                exit_code=process.returncode,
                stdout=process.stdout or "",
                stderr=process.stderr or "",
                duration=duration,
                timestamp=start_time,
                pid=process.pid if hasattr(process, 'pid') else None
            )

            # 履歴に追加
            self.command_history.append(result)

            # 実行ログ記録
            self.log_command_execution(result)

            return result

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            result = CommandResult(
                command=command,
                exit_code=-2,
                stdout="",
                stderr=f"タイムアウト ({config.timeout}秒)",
                duration=duration,
                timestamp=start_time
            )
            self.command_history.append(result)
            return result

        except Exception as e:
            duration = time.time() - start_time
            result = CommandResult(
                command=command,
                exit_code=-3,
                stdout="",
                stderr=f"実行エラー: {str(e)}",
                duration=duration,
                timestamp=start_time
            )
            self.command_history.append(result)
            return result

    def execute_async(self, command: str, config: Optional[CommandConfig] = None) -> str:
        """非同期コマンド実行（バックグラウンド）"""

        if config is None:
            config = self.default_config

        # 安全性チェック
        is_safe, safety_msg = self.is_safe_command(command)
        if not is_safe:
            return f"セキュリティエラー: {safety_msg}"

        try:
            # コマンド準備
            prepared_command, kwargs = self.prepare_command(command, config)

            # 非同期実行用の調整
            kwargs.pop('timeout', None)  # 非同期ではタイムアウト削除

            process = subprocess.Popen(prepared_command, **kwargs)

            # プロセス管理に追加
            process_id = f"{int(time.time())}_{process.pid}"
            self.running_processes[process_id] = process

            print(f"🚀 バックグラウンド実行開始: {command}")
            print(f"   プロセスID: {process_id}")

            return process_id

        except Exception as e:
            return f"非同期実行エラー: {str(e)}"

    def check_process_status(self, process_id: str) -> Optional[Dict[str, Any]]:
        """プロセス状態確認"""

        if process_id not in self.running_processes:
            return None

        process = self.running_processes[process_id]

        status = {
            "process_id": process_id,
            "pid": process.pid,
            "returncode": process.returncode,
            "is_running": process.returncode is None
        }

        # 完了している場合は出力を取得
        if process.returncode is not None:
            try:
                stdout, stderr = process.communicate(timeout=1)
                status.update({
                    "stdout": stdout or "",
                    "stderr": stderr or "",
                    "exit_code": process.returncode
                })

                # 完了したプロセスは削除
                del self.running_processes[process_id]

            except subprocess.TimeoutExpired:
                status["error"] = "出力取得タイムアウト"

        return status

    def kill_process(self, process_id: str, force: bool = False) -> bool:
        """プロセス停止"""

        if process_id not in self.running_processes:
            return False

        process = self.running_processes[process_id]

        try:
            if force:
                process.kill()
                signal_used = signal.SIGKILL if not self.is_windows else None
            else:
                process.terminate()
                signal_used = signal.SIGTERM if not self.is_windows else None

            # 停止待機
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if not force:
                    # 強制終了を試行
                    process.kill()
                    process.wait(timeout=5)

            # プロセス削除
            del self.running_processes[process_id]

            print(f"⏹️ プロセス停止: {process_id}")
            return True

        except Exception as e:
            print(f"プロセス停止エラー: {e}")
            return False

    def analyze_command_output(self, result: CommandResult) -> Dict[str, Any]:
        """コマンド出力分析"""

        analysis = {
            "success": result.exit_code == 0,
            "duration_category": "fast" if result.duration < 1 else "normal" if result.duration < 10 else "slow",
            "output_size": len(result.stdout) + len(result.stderr),
            "has_errors": bool(result.stderr),
            "line_count": len(result.stdout.splitlines()) if result.stdout else 0
        }

        # エラー分析
        if result.stderr:
            analysis["error_analysis"] = {
                "likely_permission_error": "permission denied" in result.stderr.lower(),
                "likely_not_found": "not found" in result.stderr.lower() or "command not found" in result.stderr.lower(),
                "likely_network_error": any(term in result.stderr.lower() for term in ["connection", "network", "timeout", "unreachable"]),
                "likely_syntax_error": "syntax error" in result.stderr.lower()
            }

        # 成功時の出力パターン分析
        if analysis["success"] and result.stdout:
            analysis["output_analysis"] = {
                "is_json": self._is_json_output(result.stdout),
                "is_table": self._is_table_output(result.stdout),
                "is_list": self._is_list_output(result.stdout),
                "contains_paths": self._contains_paths(result.stdout)
            }

        return analysis

    def _is_json_output(self, output: str) -> bool:
        """JSON出力判定"""
        try:
            json.loads(output.strip())
            return True
        except:
            return False

    def _is_table_output(self, output: str) -> bool:
        """テーブル出力判定"""
        lines = output.strip().splitlines()
        if len(lines) < 2:
            return False

        # 列区切り文字の存在確認
        separators = ['\t', '|', '  +']
        for sep in separators:
            if all(sep in line for line in lines[:3]):
                return True
        return False

    def _is_list_output(self, output: str) -> bool:
        """リスト出力判定"""
        lines = output.strip().splitlines()
        if len(lines) < 2:
            return False

        # リストマーカーの確認
        list_markers = ['-', '*', '+', '•']
        for marker in list_markers:
            if sum(1 for line in lines if line.strip().startswith(marker)) > len(lines) / 2:
                return True
        return False

    def _contains_paths(self, output: str) -> bool:
        """パス含有判定"""
        import re

        # Windows/Unixパスパターン
        path_patterns = [
            r'[a-zA-Z]:\\[\w\\.-]+',  # Windows絶対パス
            r'/[\w/.-]+',              # Unix絶対パス
            r'\.[\w/.-]+',             # 相対パス
            r'~[\w/.-]*'               # ホームパス
        ]

        for pattern in path_patterns:
            if re.search(pattern, output):
                return True
        return False

    def suggest_command_improvements(self, result: CommandResult) -> List[str]:
        """コマンド改善提案"""
        suggestions = []

        analysis = self.analyze_command_output(result)

        # エラーベースの提案
        if result.exit_code != 0:
            if analysis.get("error_analysis", {}).get("likely_not_found"):
                suggestions.append("コマンドまたはファイルが見つかりません。パスの確認をお勧めします。")

            if analysis.get("error_analysis", {}).get("likely_permission_error"):
                suggestions.append("権限エラーです。管理者権限での実行を検討してください。")

            if analysis.get("error_analysis", {}).get("likely_network_error"):
                suggestions.append("ネットワークエラーです。接続確認とタイムアウト設定の見直しをお勧めします。")

        # パフォーマンス提案
        if result.duration > 30:
            suggestions.append("実行時間が長いです。並列処理やフィルタリングの使用を検討してください。")

        # 出力改善提案
        if analysis["output_size"] > 10000:
            suggestions.append("出力が大きいです。`head`、`tail`、`grep`等での絞り込みをお勧めします。")

        return suggestions

    def log_command_execution(self, result: CommandResult):
        """コマンド実行ログ記録"""

        try:
            # 分析結果
            analysis = self.analyze_command_output(result)

            # 履歴マネージャーに記録
            self.history_manager.log_command_execution(
                command=result.command,
                exit_code=result.exit_code,
                duration=result.duration,
                output_size=analysis["output_size"],
                success=analysis["success"],
                error_message=result.stderr if result.stderr else None
            )

        except Exception as e:
            print(f"コマンドログ記録エラー: {e}")

    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """コマンド履歴取得"""

        recent_history = self.command_history[-limit:] if limit > 0 else self.command_history

        return [
            {
                "command": cmd.command,
                "exit_code": cmd.exit_code,
                "duration": cmd.duration,
                "timestamp": cmd.timestamp,
                "success": cmd.exit_code == 0,
                "has_output": bool(cmd.stdout),
                "has_errors": bool(cmd.stderr)
            }
            for cmd in recent_history
        ]

    def interactive_mode(self):
        """対話モード"""

        print("🔧 Command Agent - 対話モード")
        print("コマンドを入力してください（'exit'で終了、'help'でヘルプ）")
        print("=" * 50)

        while True:
            try:
                command = input("\n> ").strip()

                if command.lower() in ['exit', 'quit', 'q']:
                    break

                elif command.lower() == 'help':
                    self._show_help()
                    continue

                elif command.lower() == 'history':
                    history = self.get_command_history()
                    for i, cmd in enumerate(history, 1):
                        status = "✅" if cmd["success"] else "❌"
                        print(f"{i:2d}. {status} {cmd['command'][:50]}...")
                    continue

                elif command.lower() == 'status':
                    if self.running_processes:
                        print("実行中プロセス:")
                        for pid, process in self.running_processes.items():
                            status = "実行中" if process.returncode is None else f"終了({process.returncode})"
                            print(f"  {pid}: {status}")
                    else:
                        print("実行中プロセスなし")
                    continue

                elif command.startswith('kill '):
                    process_id = command[5:].strip()
                    if self.kill_process(process_id):
                        print(f"✅ プロセス停止: {process_id}")
                    else:
                        print(f"❌ プロセス停止失敗: {process_id}")
                    continue

                elif command.startswith('async '):
                    async_command = command[6:].strip()
                    process_id = self.execute_async(async_command)
                    if not process_id.startswith("セキュリティエラー"):
                        print(f"🚀 バックグラウンド実行: {process_id}")
                    else:
                        print(f"❌ {process_id}")
                    continue

                if not command:
                    continue

                # 通常コマンド実行
                result = self.execute_command(command)

                # 結果表示
                if result.exit_code == 0:
                    print(f"✅ 実行成功 ({result.duration:.2f}秒)")
                    if result.stdout:
                        print(result.stdout)
                else:
                    print(f"❌ 実行失敗 (コード: {result.exit_code}, {result.duration:.2f}秒)")
                    if result.stderr:
                        print(f"エラー: {result.stderr}")

                # 改善提案
                suggestions = self.suggest_command_improvements(result)
                if suggestions:
                    print("\n💡 改善提案:")
                    for suggestion in suggestions:
                        print(f"   • {suggestion}")

            except KeyboardInterrupt:
                print("\n\n中断されました")
                break
            except Exception as e:
                print(f"エラー: {e}")

    def _show_help(self):
        """ヘルプ表示"""
        help_text = """
🔧 Command Agent - ヘルプ

基本コマンド:
  <command>        - 通常のコマンド実行
  async <command>  - バックグラウンド実行
  history          - コマンド履歴表示
  status           - 実行中プロセス状態
  kill <pid>       - プロセス停止
  help             - このヘルプ表示
  exit             - 終了

セーフモード:
  現在のセーフモード設定により、一部のコマンドは制限されています。
  許可されているコマンド: git, python, pip, ls, cd, cat, grep など

例:
  > git status
  > async python long_running_script.py
  > ps aux
  > kill process_123
        """
        print(help_text)


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Command Agent - コマンド実行")
    parser.add_argument("command", nargs="*", help="実行するコマンド")
    parser.add_argument("--interactive", "-i", action="store_true", help="対話モード")
    parser.add_argument("--async-mode", action="store_true", help="バックグラウンド実行")
    parser.add_argument("--timeout", type=int, default=30, help="タイムアウト秒数")
    parser.add_argument("--unsafe", action="store_true", help="セーフモード無効化")
    parser.add_argument("--history", action="store_true", help="履歴表示")
    parser.add_argument("--cwd", help="作業ディレクトリ")

    args = parser.parse_args()

    agent = CommandAgent()

    # セーフモード設定
    if args.unsafe:
        agent.default_config.safe_mode = False
        print("⚠️ セーフモード無効化")

    # 設定調整
    agent.default_config.timeout = args.timeout
    if args.cwd:
        agent.default_config.working_dir = args.cwd

    if args.history:
        history = agent.get_command_history(20)
        print("📊 コマンド履歴:")
        for i, cmd in enumerate(history, 1):
            status = "✅" if cmd["success"] else "❌"
            duration = f"{cmd['duration']:.2f}s"
            print(f"{i:2d}. {status} [{duration}] {cmd['command']}")

    elif args.interactive:
        agent.interactive_mode()

    elif args.command:
        command = " ".join(args.command)

        if args.async_mode:
            process_id = agent.execute_async(command)
            print(f"バックグラウンド実行: {process_id}")
        else:
            result = agent.execute_command(command)

            if result.exit_code == 0:
                print(result.stdout)
            else:
                print(f"エラー (コード: {result.exit_code}):", file=sys.stderr)
                print(result.stderr, file=sys.stderr)
                sys.exit(result.exit_code)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
