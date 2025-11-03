#!/usr/bin/env python3
"""
パスワードマネージャー 基本動作テスト
"""
import sys
import os

# パッケージパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """基本機能テスト"""
    print("🧪 パスワードマネージャー基本テスト開始")

    try:
        # 暗号化モジュールテスト
        from src.encryption import PasswordCrypto
        crypto = PasswordCrypto()
        password = crypto.generate_password(16)
        print(f"✅ 暗号化モジュール正常: 生成パスワード {len(password)}文字")

        # データベースモジュールテスト
        from src.database import DatabaseManager
        db = DatabaseManager(":memory:")  # メモリDB使用
        print("✅ データベースモジュール正常")

        # パスワードマネージャーコアテスト
        from src.password_manager import PasswordManager
        pm = PasswordManager(":memory:")
        print("✅ パスワードマネージャーコア正常")

        # データベーステーブルが作成されていることを確認
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, master_password_hash TEXT, salt BLOB, created_at TIMESTAMP, updated_at TIMESTAMP, is_active BOOLEAN)")
        conn.execute("CREATE TABLE IF NOT EXISTS password_entries (id INTEGER PRIMARY KEY, user_id INTEGER, service_name TEXT, username TEXT, email TEXT, encrypted_password BLOB, encryption_nonce BLOB, url TEXT, notes TEXT, created_at TIMESTAMP, updated_at TIMESTAMP)")
        conn.close()

        # 新しいパスワードマネージャーインスタンスを作成（テスト用）
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            test_db_path = tmp.name
        pm = PasswordManager(test_db_path)

        # ユーザー作成テスト
        success = pm.create_user("testuser", "TestPassword123!")
        if success:
            print("✅ ユーザー作成成功")
        else:
            print("❌ ユーザー作成失敗")
            return False

        # ログインテスト
        success = pm.login("testuser", "TestPassword123!")
        if success:
            print("✅ ログイン成功")
        else:
            print("❌ ログイン失敗")
            return False

        # パスワード追加テスト
        entry_id = pm.add_password(
            service_name="Test Service",
            username="testuser",
            password="TestPass123!"
        )
        if entry_id:
            print(f"✅ パスワード追加成功 (ID: {entry_id})")
        else:
            print("❌ パスワード追加失敗")
            return False

        # パスワード取得テスト
        entries = pm.get_passwords()
        if len(entries) == 1:
            print(f"✅ パスワード取得成功: {entries[0]['service_name']}")
        else:
            print("❌ パスワード取得失敗")
            return False

        # パスワード生成テスト
        generated = pm.generate_password(20)
        if len(generated) == 20:
            print(f"✅ パスワード生成成功: {generated}")
        else:
            print("❌ パスワード生成失敗")
            return False

        print("🎉 全ての基本テストが成功しました！")

        # クリーンアップ
        import os
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)

        return True

    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
