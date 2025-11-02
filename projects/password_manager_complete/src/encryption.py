#!/usr/bin/env python3
"""
暗号化マネージャー

cryptography.fernet を使用したパスワード暗号化・復号化機能
完全なエラーハンドリング、ドキュメント、型ヒントを含む

Created by Ollama MCP Agent
"""

import os
import sys
import base64
import hashlib
import logging
from typing import Union, Optional
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError as e:
    print(f"暗号化ライブラリのインポートエラー: {e}")
    print("pip install cryptography を実行してください")
    sys.exit(1)

class EncryptionManager:
    """
    パスワード暗号化・復号化マネージャー
    
    Fernet対称暗号化を使用してパスワードを安全に暗号化・復号化する
    """
    
    def __init__(self, master_password: str, salt: Optional[bytes] = None):
        """
        暗号化マネージャーの初期化
        
        Args:
            master_password (str): マスターパスワード
            salt (Optional[bytes]): ソルト（指定しない場合は生成）
            
        Raises:
            ValueError: マスターパスワードが無効な場合
            RuntimeError: 暗号化初期化エラー
        """
        try:
            self.logger = logging.getLogger(__name__)
            
            if not master_password:
                raise ValueError("マスターパスワードは必須です")
            
            # ソルトの設定
            if salt is None:
                self.salt = self._generate_salt()
            else:
                self.salt = salt
            
            # 暗号化キーの生成
            self.key = self._derive_key(master_password, self.salt)
            self.fernet = Fernet(self.key)
            
            self.logger.info("暗号化マネージャー初期化完了")
            
        except Exception as e:
            self.logger.error(f"暗号化マネージャー初期化エラー: {e}")
            raise RuntimeError(f"暗号化初期化エラー: {e}")
    
    def _generate_salt(self) -> bytes:
        """
        ランダムソルトの生成
        
        Returns:
            bytes: 16バイトのランダムソルト
        """
        try:
            return os.urandom(16)
        except Exception as e:
            self.logger.error(f"ソルト生成エラー: {e}")
            # フォールバック：固定ソルト（本番環境では推奨されない）
            return b'fixed_salt_16byt'
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        パスワードから暗号化キーを導出
        
        Args:
            password (str): マスターパスワード
            salt (bytes): ソルト
            
        Returns:
            bytes: 導出された32バイトの暗号化キー
            
        Raises:
            ValueError: キー導出エラー
        """
        try:
            # PBKDF2を使用してキーを導出
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,  # 十分な反復回数
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
            return key
            
        except Exception as e:
            self.logger.error(f"キー導出エラー: {e}")
            raise ValueError(f"キー導出エラー: {e}")
    
    def encrypt(self, plaintext: str) -> str:
        """
        文字列の暗号化
        
        Args:
            plaintext (str): 暗号化する平文
            
        Returns:
            str: Base64エンコードされた暗号化データ
            
        Raises:
            ValueError: 暗号化エラー
        """
        try:
            if not isinstance(plaintext, str):
                raise ValueError("暗号化データは文字列である必要があります")
            
            if not plaintext:
                raise ValueError("暗号化データが空です")
            
            # 文字列をバイトに変換
            plaintext_bytes = plaintext.encode('utf-8')
            
            # 暗号化
            encrypted_bytes = self.fernet.encrypt(plaintext_bytes)
            
            # Base64エンコード
            encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
            
            self.logger.debug(f"暗号化成功: {len(plaintext)} -> {len(encrypted_str)} 文字")
            return encrypted_str
            
        except Exception as e:
            self.logger.error(f"暗号化エラー: {e}")
            raise ValueError(f"暗号化エラー: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        暗号化データの復号化
        
        Args:
            encrypted_data (str): Base64エンコードされた暗号化データ
            
        Returns:
            str: 復号化された平文
            
        Raises:
            ValueError: 復号化エラー
        """
        try:
            if not isinstance(encrypted_data, str):
                raise ValueError("復号化データは文字列である必要があります")
            
            if not encrypted_data:
                raise ValueError("復号化データが空です")
            
            # Base64デコード
            try:
                encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            except Exception as e:
                raise ValueError(f"Base64デコードエラー: {e}")
            
            # 復号化
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            
            # バイトを文字列に変換
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            self.logger.debug(f"復号化成功: {len(encrypted_data)} -> {len(decrypted_str)} 文字")
            return decrypted_str
            
        except Exception as e:
            self.logger.error(f"復号化エラー: {e}")
            raise ValueError(f"復号化エラー: {e}")
    
    def encrypt_file(self, file_path: str, output_path: str = None) -> str:
        """
        ファイルの暗号化
        
        Args:
            file_path (str): 暗号化するファイルのパス
            output_path (str, optional): 出力ファイルのパス
            
        Returns:
            str: 暗号化されたファイルのパス
            
        Raises:
            FileNotFoundError: ファイルが見つからない場合
            ValueError: 暗号化エラー
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
            
            # 出力パスの設定
            if output_path is None:
                output_path = file_path.with_suffix(file_path.suffix + '.enc')
            else:
                output_path = Path(output_path)
            
            # ファイル読み込み
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 暗号化
            encrypted_data = self.fernet.encrypt(file_data)
            
            # 暗号化ファイル書き込み
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            self.logger.info(f"ファイル暗号化完了: {file_path} -> {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"ファイル暗号化エラー: {e}")
            raise ValueError(f"ファイル暗号化エラー: {e}")
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str = None) -> str:
        """
        暗号化ファイルの復号化
        
        Args:
            encrypted_file_path (str): 暗号化ファイルのパス
            output_path (str, optional): 出力ファイルのパス
            
        Returns:
            str: 復号化されたファイルのパス
            
        Raises:
            FileNotFoundError: ファイルが見つからない場合
            ValueError: 復号化エラー
        """
        try:
            encrypted_file_path = Path(encrypted_file_path)
            
            if not encrypted_file_path.exists():
                raise FileNotFoundError(f"暗号化ファイルが見つかりません: {encrypted_file_path}")
            
            # 出力パスの設定
            if output_path is None:
                if encrypted_file_path.suffix == '.enc':
                    output_path = encrypted_file_path.with_suffix('')
                else:
                    output_path = encrypted_file_path.with_suffix('.dec')
            else:
                output_path = Path(output_path)
            
            # 暗号化ファイル読み込み
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # 復号化
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            # 復号化ファイル書き込み
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            self.logger.info(f"ファイル復号化完了: {encrypted_file_path} -> {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"ファイル復号化エラー: {e}")
            raise ValueError(f"ファイル復号化エラー: {e}")
    
    def get_salt(self) -> str:
        """
        ソルトの取得（Base64エンコード）
        
        Returns:
            str: Base64エンコードされたソルト
        """
        return base64.urlsafe_b64encode(self.salt).decode('utf-8')
    
    def test_encryption(self) -> bool:
        """
        暗号化・復号化のテスト
        
        Returns:
            bool: テスト結果
        """
        try:
            test_data = "暗号化テストデータ 12345"
            
            # 暗号化
            encrypted = self.encrypt(test_data)
            
            # 復号化
            decrypted = self.decrypt(encrypted)
            
            # 一致確認
            result = test_data == decrypted
            
            self.logger.info(f"暗号化テスト結果: {'成功' if result else '失敗'}")
            return result
            
        except Exception as e:
            self.logger.error(f"暗号化テストエラー: {e}")
            return False

def generate_master_password() -> str:
    """
    安全なマスターパスワードの生成
    
    Returns:
        str: 生成されたマスターパスワード
    """
    try:
        import secrets
        import string
        
        # 文字セットの定義
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        
        # 32文字のランダムパスワード生成
        password = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        return password
        
    except Exception as e:
        print(f"マスターパスワード生成エラー: {e}")
        # フォールバック
        return "fallback_master_password_123"

if __name__ == "__main__":
    try:
        print("=== 暗号化マネージャー テスト ===")
        
        # マスターパスワードの生成
        master_password = "test_master_password"
        print(f"マスターパスワード: {master_password}")
        
        # 暗号化マネージャーの初期化
        encryption_manager = EncryptionManager(master_password)
        print(f"ソルト: {encryption_manager.get_salt()}")
        
        # 暗号化・復号化テスト
        test_password = "my_secret_password_123"
        print(f"元のパスワード: {test_password}")
        
        encrypted = encryption_manager.encrypt(test_password)
        print(f"暗号化済み: {encrypted}")
        
        decrypted = encryption_manager.decrypt(encrypted)
        print(f"復号化済み: {decrypted}")
        
        # テスト結果
        if test_password == decrypted:
            print("✅ 暗号化・復号化テスト成功")
        else:
            print("❌ 暗号化・復号化テスト失敗")
        
        # 自動テスト実行
        test_result = encryption_manager.test_encryption()
        print(f"自動テスト結果: {'✅ 成功' if test_result else '❌ 失敗'}")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        sys.exit(1)