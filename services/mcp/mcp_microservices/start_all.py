#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Microservices - 全サービス起動スクリプト
"""

import subprocess
import time
import sys
import os
from typing import List


class MicroservicesManager:
    """マイクロサービスマネージャー"""

    SERVICES = [
        {"name": "API Gateway", "script": "api_gateway.py", "port": 8000},
        {"name": "LLM Service", "script": "llm_service.py", "port": 8001},
        {"name": "Database Service", "script": "database_service.py", "port": 8002},
        {"name": "Analysis Service", "script": "analysis_service.py", "port": 8003},
        {"name": "Monitoring Service", "script": "monitoring_service.py", "port": 8004},
    ]

    def __init__(self):
        self.processes = []
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def start_all(self):
        """全サービス起動"""
        print("=" * 70)
        print("🚀 MCP Microservices - 起動開始")
        print("=" * 70)

        for service in self.SERVICES:
            self._start_service(service)
            time.sleep(1)  # サービス間の起動待機

        print("\n" + "=" * 70)
        print("✅ 全サービス起動完了")
        print("=" * 70)
        print("\n📡 アクセス情報:")
        for service in self.SERVICES:
            print(f"  {service['name']:20} http://localhost:{service['port']}")

        print("\n" + "=" * 70)
        print("Press Ctrl+C to stop all services")
        print("=" * 70 + "\n")

        try:
            # 全サービスを監視
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._stop_all()

    def _start_service(self, service: dict):
        """個別サービス起動"""
        script_path = os.path.join(self.base_dir, service['script'])

        try:
            print(f"🔄 起動中: {service['name']} (:{service['port']})...")

            # Pythonプロセスとして起動
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )

            self.processes.append({
                "name": service['name'],
                "process": process,
                "port": service['port']
            })

            print(f"✅ 起動: {service['name']}")

        except Exception as e:
            print(f"❌ 失敗: {service['name']} - {e}")

    def _stop_all(self):
        """全サービス停止"""
        print("\n" + "=" * 70)
        print("🛑 全サービス停止中...")
        print("=" * 70)

        for item in self.processes:
            try:
                print(f"🔄 停止中: {item['name']}...")
                item['process'].terminate()
                item['process'].wait(timeout=5)
                print(f"✅ 停止: {item['name']}")
            except Exception as e:
                print(f"⚠️ 強制停止: {item['name']} - {e}")
                try:
                    item['process'].kill()
                except:
                    pass

        print("\n" + "=" * 70)
        print("✅ 全サービス停止完了")
        print("=" * 70)

    def check_health(self):
        """全サービスのヘルスチェック"""
        print("=" * 70)
        print("🏥 ヘルスチェック実行中...")
        print("=" * 70)

        import requests

        for service in self.SERVICES:
            url = f"http://localhost:{service['port']}/health"
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ {service['name']:20} - Healthy")
                else:
                    print(f"⚠️ {service['name']:20} - Status {response.status_code}")
            except Exception as e:
                print(f"❌ {service['name']:20} - {e}")

        print("=" * 70)


def main():
    """メイン処理"""
    manager = MicroservicesManager()

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # ヘルスチェックのみ
        manager.check_health()
    else:
        # 全サービス起動
        manager.start_all()


if __name__ == "__main__":
    main()
