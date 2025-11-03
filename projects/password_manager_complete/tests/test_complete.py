#!/usr/bin/env python3
"""
パスワードマネージャー 包括的テスト

全機能の統合テスト、ユニットテスト
完全なエラーハンドリング、ドキュメント、型ヒントを含む

Created by Ollama MCP Agent
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

# プロジェクトルートをpathに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import pytest
except ImportError:
    print("pytest が見つかりません。基本的なunittestで実行します")

# ローカルモジュールのインポート
try:
    from src.main import PasswordManager
    from src.models import PasswordEntry, DatabaseSchema
    from src.database import DatabaseManager
    from src.encryption import EncryptionManager
except ImportError as e:
    print(f"ローカルモジュール インポートエラー: {e}")
    print("src/ ディレクトリのモジュールが見つかりません")
    sys.exit(1)

class TestPasswordEntry(unittest.TestCase):
    """PasswordEntry データモデルのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.valid_entry_data = {
            'site': 'test.example.com',
            'username': 'test_user',
            'encrypted_password': 'encrypted_test_password',
            'notes': 'テストエントリ'
        }

    def test_create_valid_entry(self):
        """有効なエントリの作成テスト"""
        entry = PasswordEntry(**self.valid_entry_data)

        self.assertEqual(entry.site, 'test.example.com')
        self.assertEqual(entry.username, 'test_user')
        self.assertEqual(entry.encrypted_password, 'encrypted_test_password')
        self.assertEqual(entry.notes, 'テストエントリ')
        self.assertIsNotNone(entry.created_at)
        self.assertIsNotNone(entry.updated_at)

    def test_entry_validation(self):
        """エントリの妥当性検証テスト"""
        entry = PasswordEntry(**self.valid_entry_data)
        self.assertTrue(entry.validate())

        # 無効なエントリ（空サイト名でValueErrorが発生することを期待）
        with self.assertRaises(ValueError):
            invalid_entry = PasswordEntry(
                site='',
                username='user',
                encrypted_password='password'
            )

    def test_entry_to_dict(self):
        """辞書変換テスト"""
        entry = PasswordEntry(**self.valid_entry_data)
        entry_dict = entry.to_dict()

        self.assertIsInstance(entry_dict, dict)
        self.assertEqual(entry_dict['site'], 'test.example.com')
        self.assertEqual(entry_dict['username'], 'test_user')

    def test_entry_from_dict(self):
        """辞書からの作成テスト"""
        entry = PasswordEntry(**self.valid_entry_data)
        entry_dict = entry.to_dict()

        recreated_entry = PasswordEntry.from_dict(entry_dict)

        self.assertEqual(recreated_entry.site, entry.site)
        self.assertEqual(recreated_entry.username, entry.username)
        self.assertEqual(recreated_entry.encrypted_password, entry.encrypted_password)

class TestEncryptionManager(unittest.TestCase):
    """暗号化マネージャーのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.master_password = "test_master_password_123"
        self.test_data = "test_password_to_encrypt"

    def test_encryption_initialization(self):
        """暗号化マネージャーの初期化テスト"""
        try:
            manager = EncryptionManager(self.master_password)
            self.assertIsNotNone(manager)
            self.assertIsNotNone(manager.key)
            self.assertIsNotNone(manager.fernet)
        except ImportError:
            self.skipTest("cryptography ライブラリが利用できません")

    def test_encrypt_decrypt_cycle(self):
        """暗号化・復号化サイクルテスト"""
        try:
            manager = EncryptionManager(self.master_password)

            # 暗号化
            encrypted = manager.encrypt(self.test_data)
            self.assertIsNotNone(encrypted)
            self.assertNotEqual(encrypted, self.test_data)

            # 復号化
            decrypted = manager.decrypt(encrypted)
            self.assertEqual(decrypted, self.test_data)

        except ImportError:
            self.skipTest("cryptography ライブラリが利用できません")

    def test_encryption_test_method(self):
        """暗号化テストメソッドのテスト"""
        try:
            manager = EncryptionManager(self.master_password)
            result = manager.test_encryption()
            self.assertTrue(result)
        except ImportError:
            self.skipTest("cryptography ライブラリが利用できません")

    def test_invalid_master_password(self):
        """無効なマスターパスワードのテスト"""
        # 空のマスターパスワードでRuntimeErrorが発生することを期待
        with self.assertRaises(RuntimeError):
            EncryptionManager("")

class TestDatabaseManager(unittest.TestCase):
    """データベースマネージャーのテスト"""

    def setUp(self):
        """テストセットアップ"""
        # 一時ファイルを使用
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name

        self.db_manager = DatabaseManager(self.db_path)

        # テストエントリ
        self.test_entry = PasswordEntry(
            site='test.example.com',
            username='test_user',
            encrypted_password='encrypted_test_password',
            notes='テストエントリ'
        )

    def tearDown(self):
        """テストクリーンアップ"""
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

    def test_database_initialization(self):
        """データベース初期化テスト"""
        self.assertIsNotNone(self.db_manager)
        self.assertTrue(Path(self.db_path).exists())

    def test_add_entry(self):
        """エントリ追加テスト"""
        result = self.db_manager.add_entry(self.test_entry)
        self.assertTrue(result)
        self.assertIsNotNone(self.test_entry.id)

    def test_get_entry(self):
        """エントリ取得テスト"""
        # エントリ追加
        self.db_manager.add_entry(self.test_entry)

        # エントリ取得
        retrieved_entry = self.db_manager.get_entry(
            self.test_entry.site,
            self.test_entry.username
        )

        self.assertIsNotNone(retrieved_entry)
        self.assertEqual(retrieved_entry.site, self.test_entry.site)
        self.assertEqual(retrieved_entry.username, self.test_entry.username)

    def test_list_entries(self):
        """エントリ一覧テスト"""
        # 複数エントリ追加
        entries = [
            PasswordEntry(
                site=f'test{i}.example.com',
                username=f'user{i}',
                encrypted_password=f'password{i}'
            )
            for i in range(3)
        ]

        for entry in entries:
            self.db_manager.add_entry(entry)

        # 一覧取得
        retrieved_entries = self.db_manager.list_entries()
        self.assertEqual(len(retrieved_entries), 3)

    def test_delete_entry(self):
        """エントリ削除テスト"""
        # エントリ追加
        self.db_manager.add_entry(self.test_entry)

        # エントリ削除
        result = self.db_manager.delete_entry(
            self.test_entry.site,
            self.test_entry.username
        )
        self.assertTrue(result)

        # 削除確認
        retrieved_entry = self.db_manager.get_entry(
            self.test_entry.site,
            self.test_entry.username
        )
        self.assertIsNone(retrieved_entry)

    def test_search_entries(self):
        """エントリ検索テスト"""
        # 検索対象エントリ追加
        search_entry = PasswordEntry(
            site='searchable.example.com',
            username='search_user',
            encrypted_password='password',
            notes='検索可能なエントリ'
        )
        self.db_manager.add_entry(search_entry)

        # 検索実行
        results = self.db_manager.search_entries('searchable')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].site, 'searchable.example.com')

class TestPasswordManager(unittest.TestCase):
    """パスワードマネージャー統合テスト"""

    def setUp(self):
        """テストセットアップ"""
        # 一時ファイルを使用
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name

        self.master_password = "test_master_password_123"

        try:
            self.password_manager = PasswordManager(
                db_path=self.db_path,
                master_password=self.master_password
            )
        except Exception as e:
            if "cryptography" in str(e):
                self.skipTest("cryptography ライブラリが利用できません")
            else:
                raise

    def tearDown(self):
        """テストクリーンアップ"""
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

    def test_add_and_get_password(self):
        """パスワード追加・取得統合テスト"""
        # パスワード追加
        result = self.password_manager.add_password(
            site='integration.test.com',
            username='integration_user',
            password='integration_password',
            notes='統合テスト用エントリ'
        )
        self.assertTrue(result)

        # パスワード取得
        entry_data = self.password_manager.get_password(
            'integration.test.com',
            'integration_user'
        )

        self.assertIsNotNone(entry_data)
        self.assertEqual(entry_data['site'], 'integration.test.com')
        self.assertEqual(entry_data['username'], 'integration_user')
        self.assertEqual(entry_data['password'], 'integration_password')
        self.assertEqual(entry_data['notes'], '統合テスト用エントリ')

    def test_list_and_delete_passwords(self):
        """パスワード一覧・削除統合テスト"""
        # 複数パスワード追加
        test_sites = ['site1.com', 'site2.com', 'site3.com']
        for site in test_sites:
            self.password_manager.add_password(
                site=site,
                username='user',
                password='password'
            )

        # 一覧取得
        entries = self.password_manager.list_entries()
        self.assertEqual(len(entries), 3)

        # 1つ削除
        delete_result = self.password_manager.delete_password('site1.com', 'user')
        self.assertTrue(delete_result)

        # 一覧再取得
        entries_after_delete = self.password_manager.list_entries()
        self.assertEqual(len(entries_after_delete), 2)

class TestIntegration(unittest.TestCase):
    """統合テスト（モジュール間の連携）"""

    def setUp(self):
        """テストセットアップ"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name

        self.master_password = "integration_test_password"

    def tearDown(self):
        """テストクリーンアップ"""
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

    def test_full_password_lifecycle(self):
        """完全なパスワードライフサイクルテスト"""
        try:
            # 1. パスワードマネージャー初期化
            manager = PasswordManager(
                db_path=self.db_path,
                master_password=self.master_password
            )

            # 2. パスワード追加
            add_result = manager.add_password(
                site='lifecycle.test.com',
                username='lifecycle_user',
                password='original_password',
                notes='ライフサイクルテスト'
            )
            self.assertTrue(add_result)

            # 3. パスワード取得・検証
            entry_data = manager.get_password('lifecycle.test.com', 'lifecycle_user')
            self.assertIsNotNone(entry_data)
            self.assertEqual(entry_data['password'], 'original_password')

            # 4. パスワード一覧に含まれることを確認
            entries = manager.list_entries()
            self.assertTrue(any(
                entry['site'] == 'lifecycle.test.com'
                for entry in entries
            ))

            # 5. パスワード削除
            delete_result = manager.delete_password('lifecycle.test.com', 'lifecycle_user')
            self.assertTrue(delete_result)

            # 6. 削除後に取得できないことを確認
            deleted_entry = manager.get_password('lifecycle.test.com', 'lifecycle_user')
            self.assertIsNone(deleted_entry)

        except ImportError:
            self.skipTest("cryptography ライブラリが利用できません")

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        try:
            manager = PasswordManager(
                db_path=self.db_path,
                master_password=self.master_password
            )

            # 存在しないエントリの取得
            non_existent = manager.get_password('non.existent.com', 'user')
            self.assertIsNone(non_existent)

            # 存在しないエントリの削除
            delete_result = manager.delete_password('non.existent.com', 'user')
            self.assertFalse(delete_result)

        except ImportError:
            self.skipTest("cryptography ライブラリが利用できません")

def run_tests():
    """テスト実行関数"""
    print("=== パスワードマネージャー 包括的テスト ===")
    print("テスト開始...")

    # テストスイートの作成
    test_suite = unittest.TestSuite()

    # テストクラスの追加
    test_classes = [
        TestPasswordEntry,
        TestEncryptionManager,
        TestDatabaseManager,
        TestPasswordManager,
        TestIntegration
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 結果表示
    print("\n" + "=" * 50)
    print("テスト結果サマリー:")
    print(f"実行テスト数: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print(f"スキップ: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\n失敗したテスト:")
        for failure in result.failures:
            print(f"  - {failure[0]}")

    if result.errors:
        print("\nエラーが発生したテスト:")
        for error in result.errors:
            print(f"  - {error[0]}")

    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n総合結果: {'✅ 成功' if success else '❌ 失敗'}")

    return success

if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nテストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        sys.exit(1)
