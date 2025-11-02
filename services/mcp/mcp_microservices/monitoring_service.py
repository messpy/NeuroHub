#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Monitoring Service - システム監視・ヘルスチェックサービス
"""

import json
import time
import psutil
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any
from datetime import datetime


class MonitoringServiceHandler(BaseHTTPRequestHandler):
    """Monitoringサービスハンドラー"""

    DB_PATH = "data/neurohub.db"

    def do_GET(self):
        """GETリクエスト処理"""
        if self.path == "/health":
            self._send_response(200, {
                "status": "healthy",
                "service": "monitoring"
            })
        elif self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/system":
            self._handle_system()
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

        if self.path == "/check":
            self._handle_check(data)
        else:
            self._send_response(404, {"error": "Not Found"})

    def _handle_metrics(self):
        """メトリクス取得"""
        try:
            # システムメトリクス
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                }
            }

            self._send_response(200, metrics)
        except Exception as e:
            self._send_response(500, {"error": str(e)})

    def _handle_system(self):
        """システム情報取得"""
        try:
            # プロセス情報
            process = psutil.Process()

            system_info = {
                "timestamp": datetime.now().isoformat(),
                "process": {
                    "pid": process.pid,
                    "cpu_percent": process.cpu_percent(),
                    "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                    "threads": process.num_threads(),
                    "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
                },
                "system": {
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                    "cpu_count": psutil.cpu_count(),
                    "total_memory_gb": round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2)
                }
            }

            self._send_response(200, system_info)
        except Exception as e:
            self._send_response(500, {"error": str(e)})

    def _handle_check(self, data: Dict[str, Any]):
        """ヘルスチェック実行"""
        components = data.get("components", ["database", "system"])

        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }

        # データベースチェック
        if "database" in components:
            try:
                conn = sqlite3.connect(self.DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()

                results["checks"]["database"] = {
                    "status": "healthy",
                    "message": "Database connection successful"
                }
            except Exception as e:
                results["checks"]["database"] = {
                    "status": "unhealthy",
                    "message": str(e)
                }
                results["overall_status"] = "unhealthy"

        # システムチェック
        if "system" in components:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent

            # しきい値チェック
            issues = []
            if cpu_percent > 80:
                issues.append(f"CPU使用率高: {cpu_percent}%")
            if memory_percent > 85:
                issues.append(f"メモリ使用率高: {memory_percent}%")
            if disk_percent > 90:
                issues.append(f"ディスク使用率高: {disk_percent}%")

            if issues:
                results["checks"]["system"] = {
                    "status": "warning",
                    "message": ", ".join(issues),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent
                }
                if results["overall_status"] == "healthy":
                    results["overall_status"] = "warning"
            else:
                results["checks"]["system"] = {
                    "status": "healthy",
                    "message": "All system metrics within normal range",
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent
                }

        print(f"🏥 ヘルスチェック: {results['overall_status']}")

        self._send_response(200, results)

    def _send_response(self, status_code: int, data: Dict[str, Any]):
        """レスポンス送信"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """ログメッセージ"""
        print(f"[Monitor {time.strftime('%H:%M:%S')}] {format % args}")


def run_monitoring_service(port: int = 8004):
    """Monitoringサービス起動"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MonitoringServiceHandler)

    print("=" * 60)
    print("🏥 MCP Monitoring Service")
    print("=" * 60)
    print(f"📡 起動: http://localhost:{port}")
    print("\nエンドポイント:")
    print(f"  GET  /health  - ヘルスチェック")
    print(f"  GET  /metrics - メトリクス取得")
    print(f"  GET  /system  - システム情報")
    print(f"  POST /check   - カスタムチェック")
    print("=" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Monitoringサービス停止中...")
        httpd.shutdown()
        print("✅ Monitoringサービス停止完了")


if __name__ == "__main__":
    run_monitoring_service()
