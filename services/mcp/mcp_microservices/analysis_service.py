#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Analysis Service - ログ分析・レポート生成サービス
"""

import json
import time
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List
from datetime import datetime, timedelta


class AnalysisServiceHandler(BaseHTTPRequestHandler):
    """Analysisサービスハンドラー"""

    DB_PATH = "data/neurohub.db"

    def do_GET(self):
        """GETリクエスト処理"""
        if self.path == "/health":
            self._send_response(200, {
                "status": "healthy",
                "service": "analysis"
            })
        elif self.path == "/statistics":
            self._handle_statistics()
        else:
            self._send_response(404, {"error": "Not Found"})

    def do_POST(self):
        """POSTリクエスト処理"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_response(400, {"error": "Invalid JSON"})
            return

        if self.path == "/analyze":
            self._handle_analyze(data)
        elif self.path == "/report":
            self._handle_report(data)
        else:
            self._send_response(404, {"error": "Not Found"})

    def _handle_statistics(self):
        """統計情報取得"""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()

            # 総実行数
            cursor.execute("SELECT COUNT(*) FROM llm_history")
            total = cursor.fetchone()[0]

            # 成功数
            cursor.execute("SELECT COUNT(*) FROM llm_history WHERE success = 1")
            success = cursor.fetchone()[0]

            # 平均実行時間
            cursor.execute("SELECT AVG(execution_time) FROM llm_history")
            avg_time = cursor.fetchone()[0] or 0

            # プロバイダー別統計
            cursor.execute("""
                SELECT provider, COUNT(*) as count, AVG(execution_time) as avg_time
                FROM llm_history
                GROUP BY provider
            """)
            providers = [
                {
                    "provider": row[0],
                    "count": row[1],
                    "avg_time": round(row[2], 2) if row[2] else 0
                }
                for row in cursor.fetchall()
            ]

            conn.close()

            self._send_response(200, {
                "total_executions": total,
                "successful_executions": success,
                "success_rate": round(success / total * 100, 2) if total > 0 else 0,
                "average_execution_time": round(avg_time, 2),
                "providers": providers
            })
        except Exception as e:
            self._send_response(500, {"error": str(e)})

    def _handle_analyze(self, data: Dict[str, Any]):
        """ログ分析"""
        days = data.get("days", 7)

        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()

            # 期間指定
            since = datetime.now() - timedelta(days=days)
            since_str = since.strftime('%Y-%m-%d %H:%M:%S')

            # 期間内の統計
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
                    AVG(execution_time) as avg_time,
                    MIN(execution_time) as min_time,
                    MAX(execution_time) as max_time
                FROM llm_history
                WHERE timestamp >= ?
            """, (since_str,))

            row = cursor.fetchone()
            total, success, avg_time, min_time, max_time = row

            # エラーTOP5
            cursor.execute("""
                SELECT error_message, COUNT(*) as count
                FROM llm_history
                WHERE error_message IS NOT NULL
                  AND timestamp >= ?
                GROUP BY error_message
                ORDER BY count DESC
                LIMIT 5
            """, (since_str,))

            errors = [
                {"error": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]

            conn.close()

            print(f"📊 分析完了: {days}日間 ({total}件)")

            self._send_response(200, {
                "period_days": days,
                "total_executions": total,
                "successful_executions": success,
                "success_rate": round(success / total * 100, 2) if total > 0 else 0,
                "avg_execution_time": round(avg_time, 2) if avg_time else 0,
                "min_execution_time": round(min_time, 2) if min_time else 0,
                "max_execution_time": round(max_time, 2) if max_time else 0,
                "top_errors": errors
            })
        except Exception as e:
            print(f"❌ 分析失敗: {e}")
            self._send_response(500, {"error": str(e)})

    def _handle_report(self, data: Dict[str, Any]):
        """レポート生成"""
        report_type = data.get("type", "summary")

        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()

            if report_type == "summary":
                # サマリーレポート
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
                        AVG(execution_time) as avg_time
                    FROM llm_history
                """)
                row = cursor.fetchone()

                report = {
                    "type": "summary",
                    "total_requests": row[0],
                    "successful_requests": row[1],
                    "success_rate": round(row[1] / row[0] * 100, 2) if row[0] > 0 else 0,
                    "average_time": round(row[2], 2) if row[2] else 0,
                    "generated_at": datetime.now().isoformat()
                }

            elif report_type == "provider":
                # プロバイダー別レポート
                cursor.execute("""
                    SELECT
                        provider,
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
                        AVG(execution_time) as avg_time
                    FROM llm_history
                    GROUP BY provider
                """)

                providers = [
                    {
                        "provider": row[0],
                        "total": row[1],
                        "success": row[2],
                        "success_rate": round(row[2] / row[1] * 100, 2) if row[1] > 0 else 0,
                        "avg_time": round(row[3], 2) if row[3] else 0
                    }
                    for row in cursor.fetchall()
                ]

                report = {
                    "type": "provider",
                    "providers": providers,
                    "generated_at": datetime.now().isoformat()
                }

            else:
                report = {"error": f"Unknown report type: {report_type}"}

            conn.close()

            print(f"📄 レポート生成: {report_type}")

            self._send_response(200, report)
        except Exception as e:
            print(f"❌ レポート生成失敗: {e}")
            self._send_response(500, {"error": str(e)})

    def _send_response(self, status_code: int, data: Dict[str, Any]):
        """レスポンス送信"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """ログメッセージ"""
        print(f"[Analysis {time.strftime('%H:%M:%S')}] {format % args}")


def run_analysis_service(port: int = 8003):
    """Analysisサービス起動"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, AnalysisServiceHandler)

    print("=" * 60)
    print("📊 MCP Analysis Service")
    print("=" * 60)
    print(f"📡 起動: http://localhost:{port}")
    print("\nエンドポイント:")
    print(f"  GET  /health      - ヘルスチェック")
    print(f"  GET  /statistics  - 統計情報")
    print(f"  POST /analyze     - ログ分析")
    print(f"  POST /report      - レポート生成")
    print("=" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Analysisサービス停止中...")
        httpd.shutdown()
        print("✅ Analysisサービス停止完了")


if __name__ == "__main__":
    run_analysis_service()
