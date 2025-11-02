#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCPプロアクティブエージェント - レベル4: 高度なAI統合
システムを監視して自動的に改善提案・最適化を実行
"""

import os
import sys
import json
import time
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.agent_llm import LLMAgent, LLMRequest
from services.db.database_manager import DatabaseManager


@dataclass
class SystemIssue:
    """システム問題"""
    severity: str  # 'critical', 'warning', 'info'
    category: str
    description: str
    recommendation: str
    auto_fixable: bool


class MCPProactiveAgent:
    """MCPプロアクティブエージェントクラス"""

    def __init__(self, provider: str = "gemini"):
        self.db_manager = DatabaseManager()
        self.llm_agent = LLMAgent(provider=provider)
        self.issues: List[SystemIssue] = []

    def monitor_system(self) -> Dict[str, Any]:
        """システム監視"""
        print("🔍 システム監視開始...")

        monitoring_results = {
            "system_health": self._check_system_health(),
            "database_health": self._check_database_health(),
            "performance_metrics": self._check_performance(),
            "recent_errors": self._check_recent_errors(),
            "timestamp": datetime.now().isoformat()
        }

        return monitoring_results

    def _check_system_health(self) -> Dict[str, Any]:
        """システムヘルス確認"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            health = {
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory_percent}%",
                "disk_usage": f"{disk_percent}%",
                "status": "healthy"
            }

            # 問題検出
            if cpu_percent > 80:
                self.issues.append(SystemIssue(
                    severity="warning",
                    category="system",
                    description=f"CPU使用率が高い: {cpu_percent}%",
                    recommendation="プロセスを確認して不要なものを終了",
                    auto_fixable=False
                ))
                health["status"] = "warning"

            if memory_percent > 85:
                self.issues.append(SystemIssue(
                    severity="warning",
                    category="system",
                    description=f"メモリ使用率が高い: {memory_percent}%",
                    recommendation="メモリを解放するか、不要なプロセスを終了",
                    auto_fixable=False
                ))
                health["status"] = "warning"

            if disk_percent > 90:
                self.issues.append(SystemIssue(
                    severity="critical",
                    category="system",
                    description=f"ディスク容量が逼迫: {disk_percent}%",
                    recommendation="不要なファイルを削除してディスク容量を確保",
                    auto_fixable=False
                ))
                health["status"] = "critical"

            return health

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_database_health(self) -> Dict[str, Any]:
        """データベースヘルス確認"""
        try:
            # テーブル数確認
            sql = "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            cursor = self.db_manager._execute_sql(sql)
            table_count = cursor.fetchone()[0]

            # レコード数確認
            sql2 = "SELECT COUNT(*) FROM llm_history"
            cursor = self.db_manager._execute_sql(sql2)
            record_count = cursor.fetchone()[0]

            # 古いレコード確認
            sql3 = """
            SELECT COUNT(*) FROM llm_history
            WHERE created_at < datetime('now', '-30 days')
            """
            cursor = self.db_manager._execute_sql(sql3)
            old_records = cursor.fetchone()[0]

            health = {
                "table_count": table_count,
                "total_records": record_count,
                "old_records": old_records,
                "status": "healthy"
            }

            # 古いレコードが多い場合
            if old_records > 1000:
                self.issues.append(SystemIssue(
                    severity="info",
                    category="database",
                    description=f"古いレコードが{old_records}件あります",
                    recommendation="古いレコードをアーカイブまたは削除してパフォーマンスを改善",
                    auto_fixable=True
                ))

            return health

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_performance(self) -> Dict[str, Any]:
        """パフォーマンス確認"""
        try:
            # 最近の実行時間統計
            sql = """
            SELECT
                AVG(response_time_ms) as avg_time,
                MAX(response_time_ms) as max_time,
                MIN(response_time_ms) as min_time
            FROM llm_history
            WHERE created_at >= datetime('now', '-7 days')
            """
            cursor = self.db_manager._execute_sql(sql)
            row = cursor.fetchone()

            avg_time = row[0] if row[0] else 0
            max_time = row[1] if row[1] else 0
            min_time = row[2] if row[2] else 0

            metrics = {
                "avg_execution_time": f"{avg_time:.2f}秒",
                "max_execution_time": f"{max_time:.2f}秒",
                "min_execution_time": f"{min_time:.2f}秒",
                "status": "optimal"
            }

            # 遅い実行の検出
            if avg_time > 5.0:
                self.issues.append(SystemIssue(
                    severity="warning",
                    category="performance",
                    description=f"平均実行時間が遅い: {avg_time:.2f}秒",
                    recommendation="プロバイダーの最適化またはタイムアウト設定の見直し",
                    auto_fixable=False
                ))
                metrics["status"] = "slow"

            return metrics

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_recent_errors(self) -> Dict[str, Any]:
        """最近のエラー確認"""
        try:
            # 最近のエラー取得
            sql = """
            SELECT error_message, COUNT(*) as count
            FROM llm_history
            WHERE success = 0
            AND created_at >= datetime('now', '-24 hours')
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 5
            """
            cursor = self.db_manager._execute_sql(sql)
            errors = cursor.fetchall()

            error_list = []
            for error_msg, count in errors:
                error_list.append({
                    "error": error_msg[:100] if error_msg else "Unknown",
                    "count": count
                })

                if count > 5:
                    self.issues.append(SystemIssue(
                        severity="warning",
                        category="errors",
                        description=f"繰り返しエラー: {error_msg[:50]}... ({count}回)",
                        recommendation="エラーの根本原因を調査して修正",
                        auto_fixable=False
                    ))

            return {
                "error_count": len(errors),
                "errors": error_list,
                "status": "has_errors" if errors else "no_errors"
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def generate_improvements(self) -> List[Dict[str, Any]]:
        """改善提案生成"""
        print("\n💡 改善提案生成中...")

        improvements = []

        # 問題ベースの提案
        for issue in self.issues:
            improvements.append({
                "severity": issue.severity,
                "category": issue.category,
                "description": issue.description,
                "recommendation": issue.recommendation,
                "auto_fixable": issue.auto_fixable
            })

        # AI生成の追加提案
        ai_suggestions = self._generate_ai_suggestions()
        improvements.extend(ai_suggestions)

        return improvements

    def _generate_ai_suggestions(self) -> List[Dict]:
        """AI生成の改善提案"""
        suggestions = []

        # データベース統計から傾向分析
        try:
            sql = """
            SELECT provider,
                   AVG(response_time_ms) as avg_time,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM llm_history
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY provider
            """
            cursor = self.db_manager._execute_sql(sql)

            for row in cursor.fetchall():
                provider, avg_time, success_rate = row

                if success_rate and success_rate < 0.8:
                    suggestions.append({
                        "severity": "warning",
                        "category": "ai_analysis",
                        "description": f"{provider}の成功率が低い: {success_rate*100:.1f}%",
                        "recommendation": f"{provider}の設定を見直すか、別のプロバイダーを使用",
                        "auto_fixable": False
                    })

        except Exception as e:
            print(f"⚠️ AI提案生成エラー: {e}")

        return suggestions

    def auto_optimize(self) -> Dict[str, Any]:
        """自動最適化実行"""
        print("\n🔧 自動最適化開始...")

        optimizations = {
            "executed": [],
            "skipped": [],
            "failed": []
        }

        for issue in self.issues:
            if issue.auto_fixable:
                try:
                    if issue.category == "database" and "古いレコード" in issue.description:
                        # 古いレコード削除
                        sql = """
                        DELETE FROM llm_history
                        WHERE created_at < datetime('now', '-90 days')
                        """
                        self.db_manager._execute_sql(sql)

                        optimizations["executed"].append({
                            "action": "古いレコード削除",
                            "description": issue.description
                        })

                except Exception as e:
                    optimizations["failed"].append({
                        "action": issue.description,
                        "error": str(e)
                    })
            else:
                optimizations["skipped"].append({
                    "reason": "手動対応が必要",
                    "description": issue.description
                })

        return optimizations

    def print_report(self, monitoring: Dict, improvements: List[Dict], optimizations: Dict):
        """レポート表示"""
        print("\n" + "=" * 60)
        print("🤖 MCPプロアクティブエージェント レポート")
        print("=" * 60)

        # システムヘルス
        print("\n💚 システムヘルス:")
        for key, value in monitoring["system_health"].items():
            print(f"  {key}: {value}")

        # データベースヘルス
        print("\n💾 データベースヘルス:")
        for key, value in monitoring["database_health"].items():
            print(f"  {key}: {value}")

        # パフォーマンス
        print("\n⚡ パフォーマンス:")
        for key, value in monitoring["performance_metrics"].items():
            print(f"  {key}: {value}")

        # エラー
        if monitoring["recent_errors"]["error_count"] > 0:
            print("\n❌ 最近のエラー:")
            for error in monitoring["recent_errors"]["errors"]:
                print(f"  • {error['error'][:50]}... ({error['count']}回)")

        # 改善提案
        if improvements:
            print("\n💡 改善提案:")
            for i, imp in enumerate(improvements, 1):
                severity_icon = {
                    "critical": "🔴",
                    "warning": "⚠️",
                    "info": "ℹ️"
                }.get(imp["severity"], "•")

                print(f"  {severity_icon} {imp['description']}")
                print(f"     💡 {imp['recommendation']}")

        # 自動最適化結果
        if optimizations["executed"]:
            print("\n✅ 自動最適化実行:")
            for opt in optimizations["executed"]:
                print(f"  • {opt['action']}")

        print("\n" + "=" * 60)


def main():
    """メイン実行"""
    agent = MCPProactiveAgent()

    print("🚀 レベル4: MCPプロアクティブエージェント")
    print("=" * 60)

    # システム監視
    monitoring_results = agent.monitor_system()

    # 改善提案生成
    improvements = agent.generate_improvements()

    # 自動最適化
    optimizations = agent.auto_optimize()

    # レポート表示
    agent.print_report(monitoring_results, improvements, optimizations)

    print("\n✅ プロアクティブエージェント実行完了！")


if __name__ == "__main__":
    main()
