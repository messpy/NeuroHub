"""
パスワードマネージャーのメイン機能テスト
"""
import pytest
import os
import sys

# パッケージパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.password_manager import PasswordManager
from src.encryption import PasswordCrypto

class TestPasswordManager:
    """パスワードマネージャーのテストクラス"""

    def test_create_user_success(self, password_manager, test_user_data):
        """ユーザー作成成功テスト"""
        success = password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        assert success is True

    def test_create_duplicate_user(self, password_manager, test_user_data):
        """重複ユーザー作成テスト"""
        # 最初のユーザー作成
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # 同じユーザー名で再作成（失敗するはず）
        success = password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        assert success is False

    def test_login_success(self, password_manager, test_user_data):
        """ログイン成功テスト"""
        # ユーザー作成
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # ログイン
        success = password_manager.login(
            test_user_data['username'],
            test_user_data['master_password']
        )
        assert success is True
        assert password_manager.is_logged_in() is True

    def test_login_failure(self, password_manager, test_user_data):
        """ログイン失敗テスト"""
        # ユーザー作成
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # 間違ったパスワードでログイン
        success = password_manager.login(
            test_user_data['username'],
            'WrongPassword'
        )
        assert success is False
        assert password_manager.is_logged_in() is False

    def test_logout(self, password_manager, test_user_data):
        """ログアウトテスト"""
        # ユーザー作成・ログイン
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        password_manager.login(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # ログアウト
        password_manager.logout()
        assert password_manager.is_logged_in() is False

    def test_add_password_success(self, password_manager, test_user_data, test_password_data):
        """パスワード追加成功テスト"""
        # ユーザー作成・ログイン
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        password_manager.login(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # パスワード追加
        entry_id = password_manager.add_password(**test_password_data)
        assert entry_id is not None
        assert isinstance(entry_id, int)

    def test_add_password_without_login(self, password_manager, test_password_data):
        """ログインなしでのパスワード追加テスト"""
        entry_id = password_manager.add_password(**test_password_data)
        assert entry_id is None

    def test_get_passwords(self, password_manager, test_user_data, test_password_data):
        """パスワード取得テスト"""
        # ユーザー作成・ログイン
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        password_manager.login(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # パスワード追加
        entry_id = password_manager.add_password(**test_password_data)

        # パスワード取得
        passwords = password_manager.get_passwords()
        assert len(passwords) == 1
        assert passwords[0]['id'] == entry_id
        assert passwords[0]['service_name'] == test_password_data['service_name']
        assert passwords[0]['password'] == test_password_data['password']

    def test_get_password_by_id(self, password_manager, test_user_data, test_password_data):
        """ID指定パスワード取得テスト"""
        # ユーザー作成・ログイン
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        password_manager.login(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # パスワード追加
        entry_id = password_manager.add_password(**test_password_data)

        # ID指定で取得
        entry = password_manager.get_password(entry_id)
        assert entry is not None
        assert entry['id'] == entry_id
        assert entry['password'] == test_password_data['password']

    def test_update_password(self, password_manager, test_user_data, test_password_data):
        """パスワード更新テスト"""
        # ユーザー作成・ログイン
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        password_manager.login(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # パスワード追加
        entry_id = password_manager.add_password(**test_password_data)

        # パスワード更新
        new_password = "NewPassword456!"
        success = password_manager.update_password(
            entry_id,
            password=new_password,
            notes="Updated notes"
        )
        assert success is True

        # 更新を確認
        entry = password_manager.get_password(entry_id)
        assert entry['password'] == new_password
        assert entry['notes'] == "Updated notes"

    def test_delete_password(self, password_manager, test_user_data, test_password_data):
        """パスワード削除テスト"""
        # ユーザー作成・ログイン
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        password_manager.login(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # パスワード追加
        entry_id = password_manager.add_password(**test_password_data)

        # パスワード削除
        success = password_manager.delete_password(entry_id)
        assert success is True

        # 削除確認
        entry = password_manager.get_password(entry_id)
        assert entry is None

    def test_generate_password(self, password_manager):
        """パスワード生成テスト"""
        password = password_manager.generate_password(length=12)
        assert len(password) == 12
        assert isinstance(password, str)

        # 別の設定でテスト
        password = password_manager.generate_password(
            length=20,
            include_special=False
        )
        assert len(password) == 20
        # 特殊文字が含まれていないことを確認
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert not any(c in special_chars for c in password)

    def test_search_passwords(self, password_manager, test_user_data):
        """パスワード検索テスト"""
        # ユーザー作成・ログイン
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        password_manager.login(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # 複数のパスワード追加
        password_manager.add_password(
            service_name="Gmail",
            username="user@gmail.com",
            password="password1"
        )
        password_manager.add_password(
            service_name="Facebook",
            username="user@fb.com",
            password="password2"
        )
        password_manager.add_password(
            service_name="Google Drive",
            username="user@google.com",
            password="password3"
        )

        # 検索テスト
        results = password_manager.get_passwords(search="Gmail")
        assert len(results) == 1
        assert results[0]['service_name'] == "Gmail"

        # 部分一致検索
        results = password_manager.get_passwords(search="Goo")
        assert len(results) == 1
        assert results[0]['service_name'] == "Google Drive"

    def test_get_stats(self, password_manager, test_user_data, test_password_data):
        """統計情報取得テスト"""
        # ユーザー作成・ログイン
        password_manager.create_user(
            test_user_data['username'],
            test_user_data['master_password']
        )
        password_manager.login(
            test_user_data['username'],
            test_user_data['master_password']
        )

        # パスワード追加
        password_manager.add_password(**test_password_data)

        # 統計情報取得
        stats = password_manager.get_stats()
        assert stats['total_entries'] == 1
        assert len(stats['services']) == 1
        assert stats['services'][0] == test_password_data['service_name']

class TestPasswordCrypto:
    """暗号化機能のテストクラス"""

    def setup_method(self):
        """テストメソッド実行前の設定"""
        self.crypto = PasswordCrypto()

    def test_generate_salt(self):
        """ソルト生成テスト"""
        salt1 = self.crypto.generate_salt()
        salt2 = self.crypto.generate_salt()

        assert len(salt1) == 16
        assert len(salt2) == 16
        assert salt1 != salt2  # 異なるソルトが生成される

    def test_derive_key(self):
        """キー導出テスト"""
        password = "TestPassword123"
        salt = self.crypto.generate_salt()

        key1 = self.crypto.derive_key(password, salt)
        key2 = self.crypto.derive_key(password, salt)

        assert len(key1) == 32  # AES-256用
        assert key1 == key2  # 同じパスワード・ソルトから同じキーが導出される

    def test_hash_master_password(self):
        """マスターパスワードハッシュ化テスト"""
        password = "MasterPassword123"

        hashed, salt = self.crypto.hash_master_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert isinstance(salt, bytes)
        assert len(salt) > 0

    def test_verify_master_password(self):
        """マスターパスワード検証テスト"""
        password = "MasterPassword123"
        wrong_password = "WrongPassword"

        hashed, _ = self.crypto.hash_master_password(password)

        # 正しいパスワードの検証
        assert self.crypto.verify_master_password(password, hashed) is True

        # 間違ったパスワードの検証
        assert self.crypto.verify_master_password(wrong_password, hashed) is False

    def test_encrypt_decrypt_password(self):
        """パスワード暗号化・復号化テスト"""
        password = "SecretPassword123!"
        master_key = self.crypto.derive_key("MasterPassword", self.crypto.generate_salt())

        # 暗号化
        ciphertext, nonce = self.crypto.encrypt_password(password, master_key)

        assert isinstance(ciphertext, bytes)
        assert isinstance(nonce, bytes)
        assert len(nonce) == 12  # AES-GCM用

        # 復号化
        decrypted = self.crypto.decrypt_password(ciphertext, nonce, master_key)

        assert decrypted == password

    def test_generate_password_default(self):
        """デフォルト設定でのパスワード生成テスト"""
        password = self.crypto.generate_password()

        assert len(password) == 16  # デフォルト長
        assert isinstance(password, str)

        # 文字種チェック
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        assert has_upper is True
        assert has_lower is True
        assert has_digit is True

    def test_generate_password_custom(self):
        """カスタム設定でのパスワード生成テスト"""
        password = self.crypto.generate_password(
            length=24,
            include_uppercase=False,
            include_special=False
        )

        assert len(password) == 24
        assert not any(c.isupper() for c in password)  # 大文字なし

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert not any(c in special_chars for c in password)  # 特殊文字なし

    def test_generate_password_invalid_options(self):
        """無効な設定でのパスワード生成テスト"""
        with pytest.raises(ValueError):
            self.crypto.generate_password(
                include_uppercase=False,
                include_lowercase=False,
                include_numbers=False,
                include_special=False
            )
