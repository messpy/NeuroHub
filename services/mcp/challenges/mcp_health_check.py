#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/mcp/challenges/mcp_health_check.py

MCPヘルスチェック機能 - レベル1チャレンジ

要件:
- データベース接続確認
- LLM Agent接続確認
- ファイルシステムアクセス確認
- 各機能の応答時間測定
"""

from __future__ import annotations
import os
import sys
import time
import json
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from services.db.database_manager import DatabaseManager
    from services.db.knowledge_manager import KnowledgeManager
    from agents.agent_llm import LLMAgent
    from services.ai.llm_common import load_env_from_config
except ImportError as e:
    print(f"Import error: {e}")
    print("Some health checks may be skipped.")

@dataclass
class HealthCheckResult:
    """ヘルスチェック結果"""
    component: str
    status: str  # "healthy", "warning", "critical", "error"
    response_time_ms: float
    details: str
    timestamp: str
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class MCPHealthChecker:
    """MCPシステムヘルスチェッカー"""

    def __init__(self):
        self.results: List[HealthCheckResult] = []
        load_env_from_config(debug=True)

    def add_result(self, component: str, status: str, response_time: float,
                   details: str, error_message: Optional[str] = None):
        """ヘルスチェック結果を追加"""
        result = HealthCheckResult(
            component=component,
            status=status,
            response_time_ms=round(response_time * 1000, 2),
            details=details,
            timestamp=datetime.now().isoformat(),
            error_message=error_message
        )
        self.results.append(result)
        return result

    async def check_database_connection(self) -> HealthCheckResult:
        """データベース接続確認"""
        start_time = time.time()

        try:
            # データベースマネージャー初期化
            db_manager = DatabaseManager()

            # 基本的な接続テスト（SQLクエリ実行）
            def test_db_connection():
                cursor = db_manager._execute_sql("SELECT 1")
                return cursor is not None

            connection_success = await asyncio.to_thread(test_db_connection)
            response_time = time.time() - start_time

            if connection_success:
                # テーブル存在確認
                def get_tables():
                    cursor = db_manager._execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
                    return [row[0] for row in cursor.fetchall()]

                tables = await asyncio.to_thread(get_tables)
                details = f"Connection successful. Tables found: {len(tables)}"
                if len(tables) > 0:
                    details += f" (sample: {', '.join(tables[:3])})"

                return self.add_result(
                    "Database", "healthy", response_time, details
                )
            else:
                return self.add_result(
                    "Database", "critical", response_time,
                    "Connection failed", "Unable to establish database connection"
                )

        except Exception as e:
            response_time = time.time() - start_time
            return self.add_result(
                "Database", "error", response_time,
                f"Database check failed: {str(e)}", str(e)
            )

    async def check_llm_agent_connection(self) -> HealthCheckResult:
        """LLM Agent接続確認"""
        start_time = time.time()

        try:
            # LLM Agent初期化
            llm_agent = LLMAgent()

            # プロバイダー状態確認
            provider_status = llm_agent.check_provider_status()
            response_time = time.time() - start_time

            available_providers = []
            for provider_name, status in provider_status.items():
                # ProviderStatusオブジェクトのavailable属性にアクセス
                if hasattr(status, 'available') and status.available:
                    available_providers.append(provider_name)

            if available_providers:
                details = f"Available providers: {', '.join(available_providers)}"
                return self.add_result(
                    "LLM_Agent", "healthy", response_time, details
                )
            else:
                return self.add_result(
                    "LLM_Agent", "critical", response_time,
                    "No LLM providers available", "All LLM providers are unavailable"
                )

        except Exception as e:
            response_time = time.time() - start_time
            return self.add_result(
                "LLM_Agent", "error", response_time,
                f"LLM Agent check failed: {str(e)}", str(e)
            )

    async def check_filesystem_access(self) -> HealthCheckResult:
        """ファイルシステムアクセス確認"""
        start_time = time.time()

        try:
            # プロジェクトルートアクセス確認
            root_path = ROOT
            if not root_path.exists():
                response_time = time.time() - start_time
                return self.add_result(
                    "Filesystem", "critical", response_time,
                    f"Project root not accessible: {root_path}",
                    f"Cannot access {root_path}"
                )

            # 重要ディレクトリの存在確認
            critical_dirs = ["services", "agents", "config", "logs"]
            missing_dirs = []
            for dir_name in critical_dirs:
                if not (root_path / dir_name).exists():
                    missing_dirs.append(dir_name)

            # 一時ファイル作成テスト
            temp_dir = root_path / "logs"
            temp_dir.mkdir(exist_ok=True)

            test_file = temp_dir / f"health_check_test_{int(time.time())}.tmp"
            try:
                test_file.write_text("Health check test")
                test_content = test_file.read_text()
                test_file.unlink()  # クリーンアップ

                if test_content != "Health check test":
                    raise Exception("File read/write test failed")

            except Exception as e:
                response_time = time.time() - start_time
                return self.add_result(
                    "Filesystem", "warning", response_time,
                    f"File operations failed: {str(e)}", str(e)
                )

            response_time = time.time() - start_time

            if missing_dirs:
                return self.add_result(
                    "Filesystem", "warning", response_time,
                    f"Some directories missing: {', '.join(missing_dirs)}",
                    f"Missing directories: {missing_dirs}"
                )
            else:
                return self.add_result(
                    "Filesystem", "healthy", response_time,
                    f"All critical directories accessible, R/W operations working"
                )

        except Exception as e:
            response_time = time.time() - start_time
            return self.add_result(
                "Filesystem", "error", response_time,
                f"Filesystem check failed: {str(e)}", str(e)
            )

    async def check_mcp_services(self) -> HealthCheckResult:
        """MCPサービス確認"""
        start_time = time.time()

        try:
            # MCPサービスファイルの存在確認
            mcp_dir = ROOT / "services" / "mcp"
            if not mcp_dir.exists():
                response_time = time.time() - start_time
                return self.add_result(
                    "MCP_Services", "critical", response_time,
                    "MCP services directory not found", f"{mcp_dir} does not exist"
                )

            # 重要なMCPモジュールの確認
            critical_modules = [
                "core.py", "mcp_enhanced.py", "llm_investigator.py",
                "cmd_exec.py", "ai_prj_coding.py"
            ]

            available_modules = []
            missing_modules = []

            for module in critical_modules:
                module_path = mcp_dir / module
                if module_path.exists():
                    available_modules.append(module)
                else:
                    missing_modules.append(module)

            response_time = time.time() - start_time

            if missing_modules:
                return self.add_result(
                    "MCP_Services", "warning", response_time,
                    f"Available: {len(available_modules)}/{len(critical_modules)} modules. Missing: {', '.join(missing_modules)}",
                    f"Missing modules: {missing_modules}"
                )
            else:
                return self.add_result(
                    "MCP_Services", "healthy", response_time,
                    f"All {len(critical_modules)} critical MCP modules available"
                )

        except Exception as e:
            response_time = time.time() - start_time
            return self.add_result(
                "MCP_Services", "error", response_time,
                f"MCP services check failed: {str(e)}", str(e)
            )

    async def run_all_checks(self) -> Dict[str, Any]:
        """全ヘルスチェック実行"""
        print("🔍 MCPシステムヘルスチェック開始...")
        start_time = time.time()

        # 各チェックを並行実行
        check_tasks = [
            self.check_filesystem_access(),
            self.check_mcp_services(),
            self.check_database_connection(),
            self.check_llm_agent_connection(),
        ]

        await asyncio.gather(*check_tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # 結果集計
        status_counts = {"healthy": 0, "warning": 0, "critical": 0, "error": 0}
        for result in self.results:
            status_counts[result.status] += 1

        # 全体的なシステム状態判定
        overall_status = "healthy"
        if status_counts["critical"] > 0 or status_counts["error"] > 0:
            overall_status = "critical"
        elif status_counts["warning"] > 0:
            overall_status = "warning"

        summary = {
            "overall_status": overall_status,
            "total_checks": len(self.results),
            "status_breakdown": status_counts,
            "total_time_ms": round(total_time * 1000, 2),
            "timestamp": datetime.now().isoformat(),
            "details": [asdict(result) for result in self.results]
        }

        return summary

    def print_results(self, summary: Dict[str, Any]):
        """結果をコンソールに表示"""
        print("\n" + "="*60)
        print("🏥 MCPシステムヘルスチェック結果")
        print("="*60)

        # 全体状況
        status_icon = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "🔴",
            "error": "💥"
        }

        overall_icon = status_icon.get(summary["overall_status"], "❓")
        print(f"\n{overall_icon} 全体状況: {summary['overall_status'].upper()}")
        print(f"⏱️  総実行時間: {summary['total_time_ms']}ms")
        print(f"🔢 チェック数: {summary['total_checks']}")

        # 状態別集計
        print(f"\n📊 状態別集計:")
        for status, count in summary["status_breakdown"].items():
            icon = status_icon.get(status, "❓")
            print(f"   {icon} {status.capitalize()}: {count}")

        # 詳細結果
        print(f"\n📋 詳細結果:")
        for result in self.results:
            icon = status_icon.get(result.status, "❓")
            print(f"\n  {icon} {result.component}")
            print(f"     ⏱️  応答時間: {result.response_time_ms}ms")
            print(f"     📝 詳細: {result.details}")
            if result.error_message:
                print(f"     ❌ エラー: {result.error_message}")

        print("\n" + "="*60)

async def main():
    """メイン実行関数"""
    try:
        checker = MCPHealthChecker()
        summary = await checker.run_all_checks()

        # 結果表示
        checker.print_results(summary)

        # ログファイルに保存
        log_dir = ROOT / "logs" / "challenges"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with log_file.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n📄 詳細ログ保存先: {log_file}")

        # システム終了コード
        exit_code = 0 if summary["overall_status"] == "healthy" else 1
        return exit_code

    except Exception as e:
        print(f"\n💥 ヘルスチェック実行エラー: {e}")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
