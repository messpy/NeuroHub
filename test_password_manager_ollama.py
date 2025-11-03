#!/usr/bin/env python3
"""
MCPパスワードマネージャーOllama版テスト
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path

# パッケージパスの追加
sys.path.append(str(Path(__file__).parent))

def test_password_manager_ollama():
    """パスワードマネージャーテスト"""
    try:
        # テスト用一時ファイル
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test_passwords.db")

        print("🔐 MCPパスワードマネージャーOllama版テスト開始")

        # ファイルをインポート
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "password_manager_ollama",
            "projects/password_manager_ollama.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 基本クラステスト
        print("✅ 1. インポート成功")

        # PasswordManagerクラステスト
        pm = module.PasswordManager(test_db)
        print("✅ 2. PasswordManagerクラス初期化成功")

        # Cryptographyクラステスト
        crypto = module.Cryptography("test_password_123")
        test_data = "sensitive_data"
        encrypted = crypto.encrypt(test_data)
        decrypted = crypto.decrypt(encrypted)
        assert test_data == decrypted, "暗号化/復号化テスト失敗"
        print("✅ 3. Cryptographyクラステスト成功")

        # DatabaseAgentクラステスト
        db_agent = module.DatabaseAgent(test_db)
        schema = db_agent.get_table_schema("passwords")
        assert 'columns' in schema, "スキーマ取得テスト失敗"
        print("✅ 4. DatabaseAgentクラステスト成功")

        # MCPPasswordManagerテスト
        mcp_manager = module.MCPPasswordManager(test_db, "master123")
        print("✅ 5. MCPPasswordManagerクラス初期化成功")

        # パスワード追加テスト
        success = mcp_manager.add_password("github.com", "testuser", "password123", "テストアカウント")
        assert success, "パスワード追加テスト失敗"
        print("✅ 6. パスワード追加テスト成功")

        # パスワード取得テスト
        entries = mcp_manager.get_password("github.com", "testuser")
        assert len(entries) == 1, "パスワード取得テスト失敗"
        assert entries[0].username == "testuser", "ユーザー名取得テスト失敗"
        assert entries[0].password == "password123", "パスワード復号化テスト失敗"
        print("✅ 7. パスワード取得テスト成功")

        # サイト一覧テスト
        sites = mcp_manager.list_sites()
        assert "github.com" in sites, "サイト一覧テスト失敗"
        print("✅ 8. サイト一覧テスト成功")

        # パスワード削除テスト
        success = mcp_manager.delete_password("github.com", "testuser")
        assert success, "パスワード削除テスト失敗"
        print("✅ 9. パスワード削除テスト成功")

        # クリーンアップ
        os.remove(test_db)
        os.rmdir(temp_dir)

        print("🎉 全テスト成功！MCPパスワードマネージャーOllama版は正常に動作します")
        return True

    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_password_manager_ollama()
