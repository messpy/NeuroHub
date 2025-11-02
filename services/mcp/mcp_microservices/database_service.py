#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Database Service - データベース操作サービス
"""

import json
import time
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List


class DatabaseServiceHandler(BaseHTTPRequestHandler):
    """Databaseサービスハンドラー"""

    DB_PATH = "data/neurohub.db"

    def do_GET(self):
        """GETリクエスト処理"""
        if self.path == "/health":
            self._send_response(200, {
                "status": "healthy",
                "service": "database",
                "db_path": self.DB_PATH
            })
        elif self.path == "/tables":
            self._handle_list_tables()
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

        if self.path == "/query":
            self._handle_query(data)
        elif self.path == "/execute":
            self._handle_execute(data)
        else:
            self._send_response(404, {"error": "Not Found"})

    def _handle_list_tables(self):
        """テーブル一覧取得"""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            conn.close()

            self._send_response(200, {
                "tables": tables,
                "count": len(tables)
            })
        except Exception as e:
            self._send_response(500, {"error": str(e)})

    def _handle_query(self, data: Dict[str, Any]):
        """クエリ実行"""
        sql = data.get("sql", "")
        params = data.get("params", [])

        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # 辞書形式に変換
            results = [dict(row) for row in rows]

            conn.close()

            print(f"📊 Query実行: {sql[:50]}... ({len(results)}件)")

            self._send_response(200, {
                "results": results,
                "count": len(results),
                "sql": sql
            })
        except Exception as e:
            print(f"❌ Query失敗: {e}")
            self._send_response(500, {"error": str(e)})

    def _handle_execute(self, data: Dict[str, Any]):
        """SQL実行（INSERT/UPDATE/DELETE）"""
        sql = data.get("sql", "")
        params = data.get("params", [])

        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()

            cursor.execute(sql, params)
            conn.commit()

            affected = cursor.rowcount
            last_id = cursor.lastrowid

            conn.close()

            print(f"✅ Execute実行: {sql[:50]}... ({affected}件)")

            self._send_response(200, {
                "affected": affected,
                "last_id": last_id,
                "sql": sql
            })
        except Exception as e:
            print(f"❌ Execute失敗: {e}")
            self._send_response(500, {"error": str(e)})

    def _send_response(self, status_code: int, data: Dict[str, Any]):
        """レスポンス送信"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """ログメッセージ"""
        print(f"[DB {time.strftime('%H:%M:%S')}] {format % args}")


def run_database_service(port: int = 8002):
    """Databaseサービス起動"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DatabaseServiceHandler)

    print("=" * 60)
    print("💾 MCP Database Service")
    print("=" * 60)
    print(f"📡 起動: http://localhost:{port}")
    print(f"📂 DB: {DatabaseServiceHandler.DB_PATH}")
    print("\nエンドポイント:")
    print(f"  GET  /health - ヘルスチェック")
    print(f"  GET  /tables - テーブル一覧")
    print(f"  POST /query  - SELECT実行")
    print(f"  POST /execute - INSERT/UPDATE/DELETE実行")
    print("=" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Databaseサービス停止中...")
        httpd.shutdown()
        print("✅ Databaseサービス停止完了")


if __name__ == "__main__":
    run_database_service()
