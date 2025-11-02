#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP API Gateway - マイクロサービスのエントリーポイント
すべてのリクエストをルーティング
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any


class APIGatewayHandler(BaseHTTPRequestHandler):
    """API Gatewayハンドラー"""

    # サービスエンドポイント
    SERVICES = {
        "llm": "http://localhost:8001",
        "database": "http://localhost:8002",
        "analysis": "http://localhost:8003",
        "monitoring": "http://localhost:8004"
    }

    def do_GET(self):
        """GETリクエスト処理"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/":
            self._send_response(200, {
                "message": "MCP API Gateway",
                "version": "1.0.0",
                "services": list(self.SERVICES.keys()),
                "status": "running"
            })

        elif path == "/health":
            self._send_response(200, {
                "status": "healthy",
                "timestamp": time.time()
            })

        elif path.startswith("/llm"):
            self._route_to_service("llm", path, parsed_path.query)

        elif path.startswith("/database"):
            self._route_to_service("database", path, parsed_path.query)

        elif path.startswith("/analysis"):
            self._route_to_service("analysis", path, parsed_path.query)

        elif path.startswith("/monitoring"):
            self._route_to_service("monitoring", path, parsed_path.query)

        else:
            self._send_response(404, {"error": "Not Found"})

    def do_POST(self):
        """POSTリクエスト処理"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_response(400, {"error": "Invalid JSON"})
            return

        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path.startswith("/llm"):
            self._route_post_to_service("llm", path, data)
        elif path.startswith("/database"):
            self._route_post_to_service("database", path, data)
        elif path.startswith("/analysis"):
            self._route_post_to_service("analysis", path, data)
        else:
            self._send_response(404, {"error": "Not Found"})

    def _route_to_service(self, service: str, path: str, query: str):
        """サービスにルーティング（GET）"""
        # 実際の実装ではHTTPクライアントでサービスに転送
        # ここでは簡易実装
        self._send_response(200, {
            "message": f"Routed to {service} service",
            "path": path,
            "query": query,
            "service_url": self.SERVICES[service]
        })

    def _route_post_to_service(self, service: str, path: str, data: Dict):
        """サービスにルーティング（POST）"""
        # 実際の実装ではHTTPクライアントでサービスに転送
        self._send_response(200, {
            "message": f"Routed to {service} service",
            "path": path,
            "data_received": True,
            "service_url": self.SERVICES[service]
        })

    def _send_response(self, status_code: int, data: Dict[str, Any]):
        """レスポンス送信"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """ログメッセージ（カスタマイズ）"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")


def run_gateway(port: int = 8000):
    """API Gateway起動"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIGatewayHandler)

    print("=" * 60)
    print("🌐 MCP API Gateway")
    print("=" * 60)
    print(f"📡 起動: http://localhost:{port}")
    print(f"📊 サービス数: {len(APIGatewayHandler.SERVICES)}")
    print("\n利用可能なエンドポイント:")
    print(f"  GET  /             - Gateway情報")
    print(f"  GET  /health       - ヘルスチェック")
    print(f"  GET  /llm/*        - LLMサービス")
    print(f"  GET  /database/*   - Databaseサービス")
    print(f"  GET  /analysis/*   - Analysisサービス")
    print(f"  GET  /monitoring/* - Monitoringサービス")
    print("\n" + "=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Gateway停止中...")
        httpd.shutdown()
        print("✅ Gateway停止完了")


if __name__ == "__main__":
    run_gateway()
