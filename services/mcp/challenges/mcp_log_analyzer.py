#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCPログ分析ツール - レベル2: データ処理機能
ログファイルを解析して実行統計、エラーパターン、改善提案を生成
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.db.database_manager import DatabaseManager


class MCPLogAnalyzer:
    """MCPログ分析クラス"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.logs_dir = project_root / "logs"
        self.stats = {
            "total_executions": 0,
            "success_count": 0,
            "failure_count": 0,
            "error_types": defaultdict(int),
            "execution_times": [],
            "provider_stats": defaultdict(lambda: {"success": 0, "failure": 0}),
            "popular_tasks": Counter()
        }

    def analyze_logs(self) -> Dict[str, Any]:
        """ログファイルを分析"""
        print("🔍 MCPログ分析開始...")

        # データベースから履歴取得
        self._analyze_database()

        # ログファイル分析
        self._analyze_log_files()

        # 統計計算
        results = self._calculate_statistics()

        # エラーパターン分析
        error_patterns = self._analyze_error_patterns()

        # 改善提案生成
        recommendations = self._generate_recommendations()

        return {
            "statistics": results,
            "error_patterns": error_patterns,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }

    def _analyze_database(self):
        """データベースから統計情報取得"""
        try:
            # プロジェクト生成履歴
            sql = """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
                   SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure
            FROM project_generation_history
            """
            cursor = self.db_manager._execute_sql(sql)
            row = cursor.fetchone()

            if row:
                self.stats["total_executions"] += row[0] or 0
                self.stats["success_count"] += row[1] or 0
                self.stats["failure_count"] += row[2] or 0

            # LLM履歴
            sql2 = """
            SELECT provider, success, request_type, response_time_ms
            FROM llm_history
            WHERE created_at >= datetime('now', '-7 days')
            """
            cursor = self.db_manager._execute_sql(sql2)

            for row in cursor.fetchall():
                provider = row[0]
                success = row[1]
                request_type = row[2]
                exec_time = row[3]

                if success:
                    self.stats["provider_stats"][provider]["success"] += 1
                else:
                    self.stats["provider_stats"][provider]["failure"] += 1

                if exec_time:
                    self.stats["execution_times"].append(exec_time)

                if request_type:
                    self.stats["popular_tasks"][request_type] += 1

        except Exception as e:
            print(f"⚠️ DB分析エラー: {e}")

    def _analyze_log_files(self):
        """ログファイルを解析"""
        if not self.logs_dir.exists():
            return

        for log_file in self.logs_dir.glob("**/*.log"):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                    # エラーパターン検出
                    errors = re.findall(r'ERROR:(.+?)(?:\n|$)', content)
                    for error in errors:
                        error_type = error.split(':')[0].strip()
                        self.stats["error_types"][error_type] += 1

            except Exception as e:
                print(f"⚠️ ログ読み込みエラー ({log_file.name}): {e}")

    def _calculate_statistics(self) -> Dict[str, Any]:
        """統計計算"""
        total = self.stats["total_executions"]
        success = self.stats["success_count"]
        failure = self.stats["failure_count"]

        success_rate = (success / total * 100) if total > 0 else 0

        exec_times = self.stats["execution_times"]
        avg_time = sum(exec_times) / len(exec_times) if exec_times else 0
        min_time = min(exec_times) if exec_times else 0
        max_time = max(exec_times) if exec_times else 0

        return {
            "総実行数": total,
            "成功数": success,
            "失敗数": failure,
            "成功率": f"{success_rate:.2f}%",
            "平均実行時間": f"{avg_time:.2f}秒",
            "最短実行時間": f"{min_time:.2f}秒",
            "最長実行時間": f"{max_time:.2f}秒",
            "プロバイダー別統計": dict(self.stats["provider_stats"]),
            "人気タスクTOP5": dict(self.stats["popular_tasks"].most_common(5))
        }

    def _analyze_error_patterns(self) -> List[Dict[str, Any]]:
        """エラーパターン分析"""
        patterns = []

        for error_type, count in sorted(
            self.stats["error_types"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]:
            patterns.append({
                "エラータイプ": error_type,
                "発生回数": count,
                "対処法": self._get_error_solution(error_type)
            })

        return patterns

    def _get_error_solution(self, error_type: str) -> str:
        """エラー別の対処法"""
        solutions = {
            "ImportError": "モジュールのインストールまたはパス確認",
            "AttributeError": "オブジェクトの属性・メソッド名を確認",
            "SyntaxError": "コードの構文エラーを修正",
            "TypeError": "データ型の不一致を確認",
            "ValueError": "値の範囲・形式を確認",
            "KeyError": "辞書のキー存在確認",
            "FileNotFoundError": "ファイルパスを確認",
            "TimeoutError": "タイムアウト時間を延長またはネットワーク確認"
        }

        for key, solution in solutions.items():
            if key in error_type:
                return solution

        return "ログ詳細を確認して原因を特定"

    def _generate_recommendations(self) -> List[str]:
        """改善提案生成"""
        recommendations = []

        total = self.stats["total_executions"]
        success = self.stats["success_count"]
        success_rate = (success / total * 100) if total > 0 else 0

        # 成功率ベースの提案
        if success_rate < 80:
            recommendations.append(
                f"⚠️ 成功率が{success_rate:.1f}%と低いです。エラーパターンを分析して修正を推奨"
            )
        elif success_rate >= 95:
            recommendations.append(
                f"✅ 成功率{success_rate:.1f}%は優秀です！"
            )

        # 実行時間ベースの提案
        exec_times = self.stats["execution_times"]
        if exec_times:
            avg_time = sum(exec_times) / len(exec_times)
            if avg_time > 5.0:
                recommendations.append(
                    f"⏱️ 平均実行時間{avg_time:.2f}秒が長いです。パフォーマンス最適化を推奨"
                )

        # プロバイダー別提案
        for provider, stats in self.stats["provider_stats"].items():
            total_prov = stats["success"] + stats["failure"]
            if total_prov > 0:
                prov_success_rate = (stats["success"] / total_prov * 100)
                if prov_success_rate < 70:
                    recommendations.append(
                        f"🔧 {provider}の成功率が{prov_success_rate:.1f}%です。設定を見直してください"
                    )

        # エラーパターンベースの提案
        top_errors = sorted(
            self.stats["error_types"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        for error_type, count in top_errors:
            if count > 5:
                recommendations.append(
                    f"❌ {error_type}が{count}回発生。優先的に対処してください"
                )

        if not recommendations:
            recommendations.append("✨ 問題は検出されませんでした。順調です！")

        return recommendations

    def save_report(self, results: Dict[str, Any]):
        """レポート保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.logs_dir / "challenges"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_file = report_dir / f"log_analysis_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 詳細レポート保存先: {report_file}")

    def print_report(self, results: Dict[str, Any]):
        """レポート表示"""
        print("\n" + "=" * 60)
        print("📊 MCP ログ分析レポート")
        print("=" * 60)

        # 統計情報
        print("\n📈 実行統計:")
        for key, value in results["statistics"].items():
            if isinstance(value, dict):
                print(f"\n  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

        # エラーパターン
        if results["error_patterns"]:
            print("\n❌ エラーパターン TOP10:")
            for i, pattern in enumerate(results["error_patterns"], 1):
                print(f"  {i}. {pattern['エラータイプ']} ({pattern['発生回数']}回)")
                print(f"     💡 対処法: {pattern['対処法']}")

        # 改善提案
        print("\n💡 改善提案:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. {rec}")

        print("\n" + "=" * 60)


def main():
    """メイン実行"""
    analyzer = MCPLogAnalyzer()

    print("🚀 レベル2: MCPログ分析ツール")
    print("=" * 60)

    # ログ分析実行
    results = analyzer.analyze_logs()

    # レポート表示
    analyzer.print_report(results)

    # レポート保存
    analyzer.save_report(results)

    print("\n✅ ログ分析完了！")


if __name__ == "__main__":
    main()
