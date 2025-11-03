"""
pytest設定
"""
import pytest
import tempfile
import os
import sys
from pathlib import Path

# パッケージパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def temp_db():
    """テスト用の一時データベースファイル"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    yield db_path

    # クリーンアップ
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def password_manager(temp_db):
    """テスト用パスワードマネージャー"""
    from src.password_manager import PasswordManager
    return PasswordManager(temp_db)

@pytest.fixture
def test_user_data():
    """テスト用ユーザーデータ"""
    return {
        'username': 'testuser',
        'master_password': 'Test123!@#'
    }

@pytest.fixture
def test_password_data():
    """テスト用パスワードデータ"""
    return {
        'service_name': 'Gmail',
        'username': 'test@gmail.com',
        'email': 'test@gmail.com',
        'password': 'SecurePassword123!',
        'url': 'https://gmail.com',
        'notes': 'Personal email account'
    }
