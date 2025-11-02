#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
システム情報収集モジュール
端末のハードウェア、ソフトウェア、環境情報を収集してDBに保存
"""

import os
import sys
import json
import time
import psutil
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.db.database_manager import DatabaseManager


@dataclass
class SystemInfo:
    """システム情報データクラス"""
    hostname: str
    platform: str
    architecture: str
    cpu_count: int
    cpu_freq: float
    memory_total: int
    memory_available: int
    disk_total: int
    disk_free: int
    python_version: str
    python_executable: str
    environment_vars: dict
    installed_packages: list
    gpu_info: dict
    network_info: dict
    timestamp: str


@dataclass
class DevelopmentEnvironment:
    """開発環境情報"""
    project_path: str
    virtual_env: Optional[str]
    git_info: dict
    dependencies: dict
    ide_info: dict
    terminal_info: dict
    performance_metrics: dict


class SystemInfoCollector:
    """システム情報収集クラス"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self._create_tables()

    def _create_tables(self):
        """システム情報用テーブル作成"""
        # システム基本情報テーブル
        system_info_sql = """
        CREATE TABLE IF NOT EXISTS system_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT NOT NULL,
            platform TEXT NOT NULL,
            architecture TEXT,
            cpu_count INTEGER,
            cpu_freq REAL,
            memory_total INTEGER,
            memory_available INTEGER,
            disk_total INTEGER,
            disk_free INTEGER,
            python_version TEXT,
            python_executable TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT
        )
        """

        # 開発環境情報テーブル
        dev_env_sql = """
        CREATE TABLE IF NOT EXISTS development_environment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_path TEXT NOT NULL,
            virtual_env TEXT,
            git_branch TEXT,
            git_commit TEXT,
            dependencies_count INTEGER,
            ide_name TEXT,
            terminal_type TEXT,
            performance_score REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT
        )
        """

        # パッケージ情報テーブル
        packages_sql = """
        CREATE TABLE IF NOT EXISTS installed_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id INTEGER,
            package_name TEXT NOT NULL,
            package_version TEXT,
            package_type TEXT,
            installation_date TEXT,
            FOREIGN KEY (system_id) REFERENCES system_info (id)
        )
        """

        # パフォーマンス履歴テーブル
        performance_sql = """
        CREATE TABLE IF NOT EXISTS performance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id INTEGER,
            cpu_usage REAL,
            memory_usage REAL,
            disk_usage REAL,
            network_speed REAL,
            response_time REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (system_id) REFERENCES system_info (id)
        )
        """

        for sql in [system_info_sql, dev_env_sql, packages_sql, performance_sql]:
            self.db_manager._execute_sql(sql)

    def collect_system_info(self) -> SystemInfo:
        """基本システム情報収集"""
        try:
            # CPU情報
            cpu_info = psutil.cpu_freq()
            cpu_freq = cpu_info.current if cpu_info else 0.0

            # メモリ情報
            memory = psutil.virtual_memory()

            # ディスク情報
            disk = psutil.disk_usage('/')

            # ネットワーク情報
            network_info = self._get_network_info()

            # GPU情報
            gpu_info = self._get_gpu_info()

            # インストール済みパッケージ
            packages = self._get_installed_packages()

            return SystemInfo(
                hostname=platform.node(),
                platform=platform.system(),
                architecture=platform.architecture()[0],
                cpu_count=psutil.cpu_count(),
                cpu_freq=cpu_freq,
                memory_total=memory.total,
                memory_available=memory.available,
                disk_total=disk.total,
                disk_free=disk.free,
                python_version=platform.python_version(),
                python_executable=sys.executable,
                environment_vars=dict(os.environ),
                installed_packages=packages,
                gpu_info=gpu_info,
                network_info=network_info,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            print(f"システム情報収集エラー: {e}")
            return None

    def collect_development_environment(self) -> DevelopmentEnvironment:
        """開発環境情報収集"""
        try:
            project_path = str(project_root)

            # Git情報
            git_info = self._get_git_info()

            # 仮想環境情報
            virtual_env = os.environ.get('VIRTUAL_ENV')

            # 依存関係情報
            dependencies = self._get_dependencies_info()

            # IDE情報
            ide_info = self._get_ide_info()

            # ターミナル情報
            terminal_info = self._get_terminal_info()

            # パフォーマンス指標
            performance_metrics = self._get_performance_metrics()

            return DevelopmentEnvironment(
                project_path=project_path,
                virtual_env=virtual_env,
                git_info=git_info,
                dependencies=dependencies,
                ide_info=ide_info,
                terminal_info=terminal_info,
                performance_metrics=performance_metrics
            )

        except Exception as e:
            print(f"開発環境情報収集エラー: {e}")
            return None

    def _get_network_info(self) -> dict:
        """ネットワーク情報取得"""
        try:
            network = psutil.net_io_counters()
            interfaces = psutil.net_if_addrs()

            return {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
                "interfaces": len(interfaces),
                "active_connections": len(psutil.net_connections())
            }
        except:
            return {}

    def _get_gpu_info(self) -> dict:
        """GPU情報取得"""
        try:
            # nvidia-smi コマンドを試行
            result = subprocess.run(['nvidia-smi', '--query-gpu=gpu_name,memory.total,memory.used', '--format=csv,noheader,nounits'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                for line in lines:
                    parts = line.split(', ')
                    if len(parts) >= 3:
                        gpus.append({
                            "name": parts[0],
                            "memory_total": int(parts[1]),
                            "memory_used": int(parts[2])
                        })
                return {"gpus": gpus, "driver": "nvidia"}
        except:
            pass

        return {"gpus": [], "driver": "none"}

    def _get_installed_packages(self) -> list:
        """インストール済みパッケージ情報取得"""
        packages = []
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                packages = json.loads(result.stdout)
        except:
            pass

        return packages

    def _get_git_info(self) -> dict:
        """Git情報取得"""
        try:
            os.chdir(project_root)

            # ブランチ情報
            branch_result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                         capture_output=True, text=True)
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

            # コミット情報
            commit_result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                         capture_output=True, text=True)
            commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown"

            # リモート情報
            remote_result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                         capture_output=True, text=True)
            remote = remote_result.stdout.strip() if remote_result.returncode == 0 else "unknown"

            return {
                "branch": branch,
                "commit": commit,
                "remote": remote,
                "has_git": True
            }
        except:
            return {"has_git": False}

    def _get_dependencies_info(self) -> dict:
        """依存関係情報取得"""
        dependencies = {}

        # requirements.txt
        req_file = project_root / "requirements.txt"
        if req_file.exists():
            dependencies["requirements"] = req_file.read_text().splitlines()

        # pyproject.toml
        pyproject_file = project_root / "pyproject.toml"
        if pyproject_file.exists():
            dependencies["pyproject"] = True

        # package.json (Node.js)
        package_file = project_root / "package.json"
        if package_file.exists():
            try:
                package_data = json.loads(package_file.read_text())
                dependencies["npm_packages"] = list(package_data.get("dependencies", {}).keys())
            except:
                pass

        return dependencies

    def _get_ide_info(self) -> dict:
        """IDE情報取得"""
        ide_info = {"detected": []}

        # VSCode
        if (project_root / ".vscode").exists():
            ide_info["detected"].append("vscode")
            ide_info["vscode_settings"] = True

        # PyCharm
        if (project_root / ".idea").exists():
            ide_info["detected"].append("pycharm")

        # Jupyter
        if any(f.suffix == '.ipynb' for f in project_root.rglob('*.ipynb')):
            ide_info["detected"].append("jupyter")

        return ide_info

    def _get_terminal_info(self) -> dict:
        """ターミナル情報取得"""
        terminal_info = {
            "shell": os.environ.get("SHELL", "unknown"),
            "term": os.environ.get("TERM", "unknown"),
            "terminal_program": os.environ.get("TERM_PROGRAM", "unknown"),
            "windows": platform.system() == "Windows"
        }

        if terminal_info["windows"]:
            terminal_info["powershell"] = "pwsh" in os.environ.get("PATH", "")

        return terminal_info

    def _get_performance_metrics(self) -> dict:
        """パフォーマンス指標取得"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)

            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100

            # プロセス数
            process_count = len(psutil.pids())

            return {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "process_count": process_count,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
        except:
            return {}

    def save_system_info(self, system_info: SystemInfo) -> int:
        """システム情報をDBに保存"""
        try:
            insert_sql = """
            INSERT INTO system_info (
                hostname, platform, architecture, cpu_count, cpu_freq,
                memory_total, memory_available, disk_total, disk_free,
                python_version, python_executable, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            cursor = self.db_manager._execute_sql(insert_sql, (
                system_info.hostname,
                system_info.platform,
                system_info.architecture,
                system_info.cpu_count,
                system_info.cpu_freq,
                system_info.memory_total,
                system_info.memory_available,
                system_info.disk_total,
                system_info.disk_free,
                system_info.python_version,
                system_info.python_executable,
                json.dumps(asdict(system_info), ensure_ascii=False)
            ))

            system_id = cursor.lastrowid

            # パッケージ情報保存
            for package in system_info.installed_packages:
                self._save_package_info(system_id, package)

            return system_id

        except Exception as e:
            print(f"システム情報保存エラー: {e}")
            return None

    def save_development_environment(self, dev_env: DevelopmentEnvironment) -> int:
        """開発環境情報をDBに保存"""
        try:
            insert_sql = """
            INSERT INTO development_environment (
                project_path, virtual_env, git_branch, git_commit,
                dependencies_count, ide_name, terminal_type,
                performance_score, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            git_info = dev_env.git_info
            ide_names = ', '.join(dev_env.ide_info.get('detected', []))
            terminal_type = dev_env.terminal_info.get('terminal_program', 'unknown')
            deps_count = len(dev_env.dependencies.get('requirements', []))
            perf_score = dev_env.performance_metrics.get('cpu_usage', 0)

            cursor = self.db_manager._execute_sql(insert_sql, (
                dev_env.project_path,
                dev_env.virtual_env,
                git_info.get('branch', 'unknown'),
                git_info.get('commit', 'unknown'),
                deps_count,
                ide_names,
                terminal_type,
                perf_score,
                json.dumps(asdict(dev_env), ensure_ascii=False)
            ))

            return cursor.lastrowid

        except Exception as e:
            print(f"開発環境情報保存エラー: {e}")
            return None

    def _save_package_info(self, system_id: int, package: dict):
        """パッケージ情報保存"""
        try:
            insert_sql = """
            INSERT INTO installed_packages (
                system_id, package_name, package_version, package_type
            ) VALUES (?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                system_id,
                package.get('name', 'unknown'),
                package.get('version', 'unknown'),
                'pip'
            ))
        except Exception as e:
            print(f"パッケージ情報保存エラー: {e}")

    def get_system_summary(self) -> dict:
        """システム情報サマリー取得"""
        try:
            # 最新のシステム情報
            latest_sql = """
            SELECT * FROM system_info
            ORDER BY timestamp DESC LIMIT 1
            """
            cursor = self.db_manager._execute_sql(latest_sql)
            latest_system = cursor.fetchone()

            # 最新の開発環境情報
            latest_env_sql = """
            SELECT * FROM development_environment
            ORDER BY timestamp DESC LIMIT 1
            """
            cursor = self.db_manager._execute_sql(latest_env_sql)
            latest_env = cursor.fetchone()

            # パッケージ統計
            packages_sql = """
            SELECT COUNT(*) as total_packages FROM installed_packages
            WHERE system_id = (SELECT MAX(id) FROM system_info)
            """
            cursor = self.db_manager._execute_sql(packages_sql)
            package_count = cursor.fetchone()[0] if cursor.fetchone() else 0

            return {
                "system": dict(latest_system) if latest_system else {},
                "environment": dict(latest_env) if latest_env else {},
                "package_count": package_count,
                "collection_time": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"システム情報サマリー取得エラー: {e}")
            return {}


def main():
    """メイン実行"""
    print("🔍 システム情報収集開始...")

    collector = SystemInfoCollector()

    # システム情報収集
    system_info = collector.collect_system_info()
    if system_info:
        system_id = collector.save_system_info(system_info)
        print(f"✅ システム情報保存完了 (ID: {system_id})")

    # 開発環境情報収集
    dev_env = collector.collect_development_environment()
    if dev_env:
        env_id = collector.save_development_environment(dev_env)
        print(f"✅ 開発環境情報保存完了 (ID: {env_id})")

    # サマリー表示
    summary = collector.get_system_summary()
    print("\n📊 システム情報サマリー:")
    print(f"  🖥️  プラットフォーム: {summary.get('system', {}).get('platform', 'Unknown')}")
    print(f"  💾 メモリ: {summary.get('system', {}).get('memory_total', 0) // (1024**3)}GB")
    print(f"  🐍 Python: {summary.get('system', {}).get('python_version', 'Unknown')}")
    print(f"  📦 パッケージ数: {summary.get('package_count', 0)}")
    print(f"  🌿 Gitブランチ: {summary.get('environment', {}).get('git_branch', 'Unknown')}")


if __name__ == "__main__":
    main()
