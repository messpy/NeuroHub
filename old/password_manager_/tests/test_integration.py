"""
統合テスト
"""
import pytest
import os
import sys
import tempfile
import threading
import time
import requests
from multiprocessing import Process

# パッケージパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.password_manager import PasswordManager

class TestIntegration:
    """統合テストクラス"""

    def test_full_workflow(self, temp_db):
        """完全なワークフローテスト"""
        pm = PasswordManager(temp_db)

        # 1. ユーザー作成
        assert pm.create_user("testuser", "TestPassword123!") is True

        # 2. ログイン
        assert pm.login("testuser", "TestPassword123!") is True
        assert pm.is_logged_in() is True

        # 3. パスワード追加
        entry_id1 = pm.add_password(
            service_name="Gmail",
            username="test@gmail.com",
            password="GmailPassword123!"
        )
        assert entry_id1 is not None

        entry_id2 = pm.add_password(
            service_name="Facebook",
            username="testuser",
            password="FbPassword123!"
        )
        assert entry_id2 is not None

        # 4. パスワード一覧取得
        passwords = pm.get_passwords()
        assert len(passwords) == 2

        # 5. 検索テスト
        gmail_results = pm.get_passwords(search="Gmail")
        assert len(gmail_results) == 1
        assert gmail_results[0]['service_name'] == "Gmail"

        # 6. パスワード更新
        assert pm.update_password(
            entry_id1,
            password="NewGmailPassword123!",
            notes="Updated password"
        ) is True

        # 7. 更新確認
        updated_entry = pm.get_password(entry_id1)
        assert updated_entry['password'] == "NewGmailPassword123!"
        assert updated_entry['notes'] == "Updated password"

        # 8. パスワード生成
        generated_password = pm.generate_password(length=20)
        assert len(generated_password) == 20

        # 9. 統計情報
        stats = pm.get_stats()
        assert stats['total_entries'] == 2

        # 10. パスワード削除
        assert pm.delete_password(entry_id2) is True

        # 11. 削除確認
        remaining_passwords = pm.get_passwords()
        assert len(remaining_passwords) == 1
        assert remaining_passwords[0]['id'] == entry_id1

        # 12. ログアウト
        pm.logout()
        assert pm.is_logged_in() is False

        # 13. ログアウト後の操作（失敗するはず）
        assert pm.add_password("Test", password="test") is None
        assert pm.get_passwords() == []

    def test_multiple_users(self, temp_db):
        """複数ユーザーテスト"""
        pm1 = PasswordManager(temp_db)
        pm2 = PasswordManager(temp_db)

        # ユーザー1作成・ログイン
        assert pm1.create_user("user1", "Password1!") is True
        assert pm1.login("user1", "Password1!") is True

        # ユーザー2作成・ログイン
        assert pm2.create_user("user2", "Password2!") is True
        assert pm2.login("user2", "Password2!") is True

        # ユーザー1のパスワード追加
        entry_id1 = pm1.add_password(
            service_name="Gmail",
            password="User1GmailPassword"
        )

        # ユーザー2のパスワード追加
        entry_id2 = pm2.add_password(
            service_name="Gmail",
            password="User2GmailPassword"
        )

        # ユーザー1のパスワード確認
        user1_passwords = pm1.get_passwords()
        assert len(user1_passwords) == 1
        assert user1_passwords[0]['password'] == "User1GmailPassword"

        # ユーザー2のパスワード確認
        user2_passwords = pm2.get_passwords()
        assert len(user2_passwords) == 1
        assert user2_passwords[0]['password'] == "User2GmailPassword"

        # ユーザー間でパスワードが混在しないことを確認
        assert user1_passwords[0]['id'] != user2_passwords[0]['id']

    def test_encryption_integrity(self, temp_db):
        """暗号化の整合性テスト"""
        pm = PasswordManager(temp_db)

        # ユーザー作成・ログイン
        assert pm.create_user("cryptouser", "CryptoPassword123!") is True
        assert pm.login("cryptouser", "CryptoPassword123!") is True

        # 様々なパスワードパターンをテスト
        test_passwords = [
            "SimplePassword",
            "P@ssw0rd!",
            "🔐🗝️🔑",  # 絵文字
            "日本語パスワード",  # 日本語
            "Very Long Password With Spaces And Numbers 123456",
            "!@#$%^&*()_+-=[]{}|;:,.<>?",  # 特殊文字のみ
            "",  # 空文字列
        ]

        entry_ids = []
        for i, password in enumerate(test_passwords):
            entry_id = pm.add_password(
                service_name=f"Service{i}",
                password=password
            )
            entry_ids.append(entry_id)

        # すべてのパスワードが正しく復号化されることを確認
        for i, (entry_id, original_password) in enumerate(zip(entry_ids, test_passwords)):
            entry = pm.get_password(entry_id)
            assert entry is not None
            assert entry['password'] == original_password
            assert entry['service_name'] == f"Service{i}"

    def test_data_persistence(self, temp_db):
        """データ永続化テスト"""
        # 最初のセッション
        pm1 = PasswordManager(temp_db)
        assert pm1.create_user("persistuser", "PersistPassword123!") is True
        assert pm1.login("persistuser", "PersistPassword123!") is True

        entry_id = pm1.add_password(
            service_name="Persistent Service",
            username="persist@example.com",
            password="PersistentPassword123!"
        )
        pm1.logout()

        # 新しいセッション（同じDB）
        pm2 = PasswordManager(temp_db)
        assert pm2.login("persistuser", "PersistPassword123!") is True

        # データが永続化されていることを確認
        passwords = pm2.get_passwords()
        assert len(passwords) == 1
        assert passwords[0]['id'] == entry_id
        assert passwords[0]['service_name'] == "Persistent Service"
        assert passwords[0]['password'] == "PersistentPassword123!"

    def test_error_handling(self, temp_db):
        """エラーハンドリングテスト"""
        pm = PasswordManager(temp_db)

        # 存在しないユーザーでログイン
        assert pm.login("nonexistent", "password") is False

        # ログインなしでの操作
        assert pm.add_password("Test", password="test") is None
        assert pm.get_passwords() == []
        assert pm.get_password(1) is None
        assert pm.update_password(1, password="new") is False
        assert pm.delete_password(1) is False

        # ユーザー作成・ログイン
        assert pm.create_user("erroruser", "ErrorPassword123!") is True
        assert pm.login("erroruser", "ErrorPassword123!") is True

        # 存在しないエントリの操作
        assert pm.get_password(999) is None
        assert pm.update_password(999, password="new") is False
        assert pm.delete_password(999) is False

    def test_concurrent_access(self, temp_db):
        """同時アクセステスト"""
        def user_workflow(username, password):
            """ユーザーのワークフロー"""
            pm = PasswordManager(temp_db)
            assert pm.create_user(username, password) is True
            assert pm.login(username, password) is True

            # 複数のパスワードを追加
            for i in range(5):
                entry_id = pm.add_password(
                    service_name=f"{username}_Service{i}",
                    password=f"{username}_Password{i}"
                )
                assert entry_id is not None

            # パスワード取得
            passwords = pm.get_passwords()
            assert len(passwords) == 5

            pm.logout()

        # 複数のスレッドで同時実行
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=user_workflow,
                args=(f"user{i}", f"Password{i}!")
            )
            threads.append(thread)
            thread.start()

        # すべてのスレッドの完了を待機
        for thread in threads:
            thread.join()

        # 最終確認：3ユーザー × 5パスワード = 15エントリが存在するはず
        pm = PasswordManager(temp_db)
        for i in range(3):
            assert pm.login(f"user{i}", f"Password{i}!") is True
            passwords = pm.get_passwords()
            assert len(passwords) == 5
            pm.logout()

    def test_import_export_consistency(self, temp_db):
        """インポート・エクスポート整合性テスト"""
        pm = PasswordManager(temp_db)

        # テストデータ準備
        assert pm.create_user("exportuser", "ExportPassword123!") is True
        assert pm.login("exportuser", "ExportPassword123!") is True

        # 複数のパスワード追加
        test_data = [
            ("Gmail", "gmail@example.com", "GmailPass123!"),
            ("Facebook", "fb_user", "FbPass123!"),
            ("Twitter", "twitter_user", "TwitterPass123!"),
        ]

        for service, username, password in test_data:
            pm.add_password(
                service_name=service,
                username=username,
                password=password
            )

        # エクスポート
        exported_data = pm.export_passwords()
        assert exported_data is not None
        assert len(exported_data) == 3

        # エクスポートされたデータの検証
        for i, (service, username, password) in enumerate(test_data):
            entry = exported_data[i]
            assert entry['service_name'] == service
            assert entry['username'] == username
            assert entry['password'] == password

        # 統計情報も正しいことを確認
        stats = pm.get_stats()
        assert stats['total_entries'] == 3
