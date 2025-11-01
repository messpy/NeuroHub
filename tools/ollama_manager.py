#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama サーバー監視・自動起動パッチ
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional

# プロジェクトパスを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class OllamaServerManager:
    """Ollamaサーバー監視・管理クラス"""

    def __init__(self, host: str = "127.0.0.1", port: int = 11434):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.process = None
        self.monitoring = False
        self.monitor_thread = None

    def is_server_running(self) -> bool:
        """サーバーが起動しているかチェック"""
        try:
            import urllib.request
            import urllib.error

            # ヘルスチェックエンドポイント
            response = urllib.request.urlopen(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status == 200
        except Exception:
            return False

    def start_server(self) -> bool:
        """Ollamaサーバーを起動"""
        try:
            print("🚀 Ollamaサーバーを起動中...")

            # Windows環境での起動
            if os.name == 'nt':
                # Ollamaがインストールされているかチェック
                ollama_exe = self._find_ollama_executable()
                if not ollama_exe:
                    print("❌ Ollama実行ファイルが見つかりません")
                    return False

                # サーバー起動
                self.process = subprocess.Popen(
                    [ollama_exe, "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux/Mac環境
                self.process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            # 起動待機
            for i in range(30):  # 30秒待機
                if self.is_server_running():
                    print("✅ Ollamaサーバー起動成功")
                    return True
                time.sleep(1)
                print(f"⏳ サーバー起動確認中... ({i+1}/30)")

            print("❌ Ollamaサーバー起動タイムアウト")
            return False

        except Exception as e:
            print(f"❌ Ollamaサーバー起動エラー: {e}")
            return False

    def _find_ollama_executable(self) -> Optional[str]:
        """Ollama実行ファイルを検索"""
        possible_paths = [
            "ollama",  # PATH環境変数
            "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Ollama\\ollama.exe",
            "C:\\Program Files\\Ollama\\ollama.exe",
            "C:\\Program Files (x86)\\Ollama\\ollama.exe",
        ]

        for path in possible_paths:
            try:
                # PATHからの検索
                if path == "ollama":
                    result = subprocess.run(
                        ["where", "ollama"],
                        capture_output=True,
                        text=True,
                        shell=True
                    )
                    if result.returncode == 0:
                        return "ollama"
                else:
                    # 展開して確認
                    expanded_path = os.path.expandvars(path)
                    if os.path.exists(expanded_path):
                        return expanded_path
            except Exception:
                continue

        return None

    def stop_server(self):
        """サーバーを停止"""
        if self.process:
            self.process.terminate()
            self.process = None
            print("🛑 Ollamaサーバーを停止しました")

    def start_monitoring(self):
        """サーバー監視を開始"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("👁️ Ollamaサーバー監視を開始しました")

    def stop_monitoring(self):
        """サーバー監視を停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("⏹️ Ollamaサーバー監視を停止しました")

    def _monitor_loop(self):
        """監視ループ"""
        while self.monitoring:
            try:
                if not self.is_server_running():
                    print("⚠️ Ollamaサーバーが停止していることを検出")
                    print("🔄 サーバーを再起動中...")
                    if self.start_server():
                        print("✅ サーバー再起動成功")
                    else:
                        print("❌ サーバー再起動失敗")

                time.sleep(10)  # 10秒間隔でチェック
            except Exception as e:
                print(f"❌ 監視エラー: {e}")
                time.sleep(5)

    def ensure_server_running(self) -> bool:
        """サーバーが確実に起動していることを保証"""
        if self.is_server_running():
            print("✅ Ollamaサーバーは既に起動中")
            return True

        print("⚠️ Ollamaサーバーが停止中 - 起動します")
        return self.start_server()

# グローバルインスタンス
ollama_manager = OllamaServerManager()

def ensure_ollama_running() -> bool:
    """Ollamaサーバーが起動していることを保証する関数"""
    return ollama_manager.ensure_server_running()

def start_ollama_monitoring():
    """Ollama監視を開始する関数"""
    ollama_manager.start_monitoring()

def stop_ollama_monitoring():
    """Ollama監視を停止する関数"""
    ollama_manager.stop_monitoring()

if __name__ == "__main__":
    # テスト実行
    print("🧪 Ollamaサーバー管理テスト")

    # サーバー起動確認
    if ensure_ollama_running():
        print("✅ サーバー起動確認完了")

        # 監視開始
        start_ollama_monitoring()

        try:
            print("💡 10秒間監視テスト中...")
            time.sleep(10)
        except KeyboardInterrupt:
            pass
        finally:
            stop_ollama_monitoring()
    else:
        print("❌ サーバー起動失敗")
