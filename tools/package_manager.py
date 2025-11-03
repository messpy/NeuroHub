#!/usr/bin/env python3
"""
パッケージ管理システム
仮想環境自動切り替え・危険コマンド拒否・安全pip実行
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import venv
import json
import re


class CommandSecurityManager:
    """コマンド安全管理クラス"""

    DANGEROUS_COMMANDS = {
        'rm', 'del', 'rmdir', 'format', 'fdisk', 'dd', 'chmod 777',
        'sudo rm', 'rm -rf', 'del /f', 'shutdown', 'reboot', 'halt',
        'killall', 'taskkill /f', 'reg delete', 'netsh', 'iptables',
        'systemctl stop', 'service stop', 'sc delete'
    }

    RESTRICTED_PATHS = {
        '/etc', '/bin', '/usr/bin', '/system32', '/windows',
        'C:\\Windows', 'C:\\System32', '/System', '/Library'
    }

    def __init__(self):
        """セキュリティマネージャー初期化"""
        self.blocked_commands = []
        self.allowed_pip_commands = ['install', 'uninstall', 'list', 'show', 'freeze']

    def is_command_safe(self, command: str) -> Tuple[bool, str]:
        """コマンドの安全性チェック"""
        try:
            command_lower = command.lower().strip()

            # 危険コマンドチェック
            for dangerous in self.DANGEROUS_COMMANDS:
                if dangerous in command_lower:
                    return False, f"危険コマンド検出: {dangerous}"

            # 制限パスチェック
            for restricted_path in self.RESTRICTED_PATHS:
                if restricted_path.lower() in command_lower:
                    return False, f"制限パス検出: {restricted_path}"

            # システムファイル操作チェック
            if re.search(r'(\.exe|\.dll|\.sys|\.bat|\.cmd|\.ps1).*\s+(del|rm|move|copy)', command_lower):
                return False, "システムファイル操作の可能性"

            return True, "安全"

        except Exception as e:
            return False, f"セキュリティチェックエラー: {e}"

    def validate_pip_command(self, command: str) -> Tuple[bool, str]:
        """pipコマンドの検証"""
        try:
            if not command.startswith('pip'):
                return False, "pipコマンドではありません"

            parts = command.split()
            if len(parts) < 2:
                return False, "不正なpipコマンド形式"

            action = parts[1]
            if action not in self.allowed_pip_commands:
                return False, f"許可されていないpipアクション: {action}"

            # パッケージ名の検証（悪意のあるパッケージ名を防ぐ）
            if action in ['install', 'uninstall', 'show']:
                if len(parts) < 3:
                    return False, "パッケージ名が指定されていません"

                package_name = parts[2]
                if not re.match(r'^[a-zA-Z0-9_-]+$', package_name):
                    return False, f"不正なパッケージ名: {package_name}"

            return True, "検証成功"

        except Exception as e:
            return False, f"pipコマンド検証エラー: {e}"


class VirtualEnvironmentManager:
    """仮想環境管理クラス"""

    def __init__(self, workspace_path: str):
        """仮想環境マネージャー初期化"""
        self.workspace_path = Path(workspace_path)
        self.venv_path = self.workspace_path / "venv_linux"
        self.is_windows = platform.system() == "Windows"

        if self.is_windows:
            self.python_exe = self.venv_path / "Scripts" / "python.exe"
            self.pip_exe = self.venv_path / "Scripts" / "pip.exe"
            self.activate_script = self.venv_path / "Scripts" / "activate.bat"
        else:
            self.python_exe = self.venv_path / "bin" / "python"
            self.pip_exe = self.venv_path / "bin" / "pip"
            self.activate_script = self.venv_path / "bin" / "activate"

    def is_venv_active(self) -> bool:
        """仮想環境がアクティブかチェック"""
        try:
            return (
                'VIRTUAL_ENV' in os.environ or
                self.venv_path.exists() and self.python_exe.exists()
            )
        except Exception:
            return False

    def create_venv_if_not_exists(self) -> Tuple[bool, str]:
        """仮想環境が存在しない場合作成"""
        try:
            if self.venv_path.exists():
                return True, "仮想環境は既に存在します"

            print(f"🔧 仮想環境を作成中: {self.venv_path}")
            venv.create(self.venv_path, with_pip=True)

            return True, "仮想環境作成成功"

        except Exception as e:
            return False, f"仮想環境作成エラー: {e}"

    def get_venv_command_prefix(self) -> List[str]:
        """仮想環境用のコマンドプレフィックス取得"""
        try:
            if not self.venv_path.exists():
                self.create_venv_if_not_exists()

            if self.is_windows:
                return [str(self.python_exe)]
            else:
                return ["bash", "-c", f"source {self.activate_script} && python"]

        except Exception as e:
            print(f"❌ コマンドプレフィックス取得エラー: {e}")
            return ["python"]

    def get_safe_pip_command(self, pip_args: List[str]) -> List[str]:
        """安全なpipコマンド生成"""
        try:
            if not self.venv_path.exists():
                self.create_venv_if_not_exists()

            if self.is_windows:
                return [str(self.pip_exe)] + pip_args
            else:
                pip_command = " ".join([str(self.pip_exe)] + pip_args)
                return ["bash", "-c", f"source {self.activate_script} && {pip_command}"]

        except Exception as e:
            print(f"❌ pipコマンド生成エラー: {e}")
            return ["pip"] + pip_args


class PackageManager:
    """パッケージ管理メインクラス"""

    def __init__(self, workspace_path: str):
        """パッケージマネージャー初期化"""
        self.workspace_path = workspace_path
        self.security = CommandSecurityManager()
        self.venv_manager = VirtualEnvironmentManager(workspace_path)
        self.installed_packages = self._load_package_cache()

    def _load_package_cache(self) -> Dict[str, str]:
        """パッケージキャッシュ読み込み"""
        try:
            cache_file = Path(self.workspace_path) / ".package_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _save_package_cache(self) -> None:
        """パッケージキャッシュ保存"""
        try:
            cache_file = Path(self.workspace_path) / ".package_cache.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.installed_packages, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ キャッシュ保存エラー: {e}")

    def execute_safe_command(self, command: str) -> Tuple[bool, str]:
        """安全なコマンド実行"""
        try:
            # セキュリティチェック
            is_safe, safety_msg = self.security.is_command_safe(command)
            if not is_safe:
                return False, f"🚫 コマンド拒否: {safety_msg}"

            # pipコマンドの特別処理
            if command.startswith('pip'):
                return self._execute_pip_command(command)

            # 一般コマンド実行
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, f"コマンドエラー: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "コマンドタイムアウト"
        except Exception as e:
            return False, f"実行エラー: {e}"

    def _execute_pip_command(self, command: str) -> Tuple[bool, str]:
        """pipコマンド安全実行"""
        try:
            # pipコマンド検証
            is_valid, validation_msg = self.security.validate_pip_command(command)
            if not is_valid:
                return False, f"🚫 pipコマンド拒否: {validation_msg}"

            # 仮想環境確認
            success, venv_msg = self.venv_manager.create_venv_if_not_exists()
            if not success:
                return False, f"仮想環境エラー: {venv_msg}"

            # pipコマンド構築
            pip_args = command.split()[1:]  # 'pip'を除く
            safe_command = self.venv_manager.get_safe_pip_command(pip_args)

            print(f"🔧 仮想環境でpip実行: {' '.join(safe_command)}")

            # 実行
            result = subprocess.run(
                safe_command,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                # インストール成功時はキャッシュ更新
                if pip_args[0] == 'install' and len(pip_args) > 1:
                    package_name = pip_args[1]
                    self.installed_packages[package_name] = "installed"
                    self._save_package_cache()

                return True, f"✅ pip実行成功:\\n{result.stdout}"
            else:
                return False, f"❌ pip実行失敗:\\n{result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "pipコマンドタイムアウト"
        except Exception as e:
            return False, f"pip実行エラー: {e}"

    def install_package(self, package_name: str, version: Optional[str] = None) -> Tuple[bool, str]:
        """パッケージ安全インストール"""
        try:
            if version:
                command = f"pip install {package_name}=={version}"
            else:
                command = f"pip install {package_name}"

            return self._execute_pip_command(command)

        except Exception as e:
            return False, f"パッケージインストールエラー: {e}"

    def list_installed_packages(self) -> Tuple[bool, str]:
        """インストール済みパッケージ一覧"""
        try:
            return self._execute_pip_command("pip list")
        except Exception as e:
            return False, f"パッケージ一覧取得エラー: {e}"

    def check_package_requirements(self, file_path: str) -> List[str]:
        """ファイルの必要パッケージ検出"""
        try:
            missing_packages = []

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # import文から必要パッケージを検出
            import_patterns = [
                r'import\\s+([a-zA-Z0-9_]+)',
                r'from\\s+([a-zA-Z0-9_]+)\\s+import',
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if match not in ['os', 'sys', 'json', 'time', 'datetime', 're', 'pathlib']:
                        if match not in self.installed_packages:
                            missing_packages.append(match)

            return missing_packages

        except Exception as e:
            print(f"❌ パッケージ要件検出エラー: {e}")
            return []


def main():
    """メイン関数 - CLI実行用"""
    try:
        print("📦 パッケージ管理システム")

        workspace = input("ワークスペースパス (Enter でカレント): ").strip()
        if not workspace:
            workspace = os.getcwd()

        manager = PackageManager(workspace)

        while True:
            print("\\n=== メニュー ===")
            print("1. パッケージインストール")
            print("2. インストール済みパッケージ一覧")
            print("3. コマンド安全実行")
            print("4. ファイル依存関係チェック")
            print("5. 仮想環境状態確認")
            print("6. 終了")

            choice = input("選択してください (1-6): ")

            if choice == "1":
                package = input("パッケージ名: ")
                version = input("バージョン (オプション): ").strip() or None

                success, msg = manager.install_package(package, version)
                print(msg)

            elif choice == "2":
                success, msg = manager.list_installed_packages()
                print(msg)

            elif choice == "3":
                command = input("実行コマンド: ")
                success, msg = manager.execute_safe_command(command)
                print(msg)

            elif choice == "4":
                file_path = input("ファイルパス: ")
                missing = manager.check_package_requirements(file_path)
                if missing:
                    print(f"📋 不足パッケージ: {', '.join(missing)}")
                else:
                    print("✅ 全パッケージがインストール済みです")

            elif choice == "5":
                is_active = manager.venv_manager.is_venv_active()
                venv_exists = manager.venv_manager.venv_path.exists()
                print(f"🌍 仮想環境状態:")
                print(f"  - 存在: {'✅' if venv_exists else '❌'}")
                print(f"  - アクティブ: {'✅' if is_active else '❌'}")
                print(f"  - パス: {manager.venv_manager.venv_path}")

            elif choice == "6":
                print("👋 終了します")
                break

            else:
                print("❌ 無効な選択です")

    except KeyboardInterrupt:
        print("\\n👋 終了します")
    except Exception as e:
        print(f"❌ エラー: {e}")


if __name__ == "__main__":
    main()
