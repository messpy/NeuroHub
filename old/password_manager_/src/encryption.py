"""
暗号化・復号化機能
"""
import os
import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets
from typing import Tuple

class PasswordCrypto:
    """パスワード暗号化・復号化クラス"""

    def __init__(self):
        self.key_length = 32  # AES-256用
        self.iterations = 100000  # PBKDF2反復回数

    def generate_salt(self) -> bytes:
        """ソルトを生成"""
        return os.urandom(16)

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """パスワードから暗号化キーを導出"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=salt,
            iterations=self.iterations,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))

    def hash_master_password(self, password: str) -> Tuple[str, bytes]:
        """マスターパスワードをハッシュ化"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8'), salt

    def verify_master_password(self, password: str, hashed: str) -> bool:
        """マスターパスワードを検証"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def encrypt_password(self, password: str, master_key: bytes) -> Tuple[bytes, bytes]:
        """パスワードを暗号化"""
        aesgcm = AESGCM(master_key)
        nonce = os.urandom(12)  # AES-GCM用96ビットnonce
        ciphertext = aesgcm.encrypt(nonce, password.encode('utf-8'), None)
        return ciphertext, nonce

    def decrypt_password(self, ciphertext: bytes, nonce: bytes, master_key: bytes) -> str:
        """パスワードを復号化"""
        aesgcm = AESGCM(master_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')

    def generate_password(self,
                         length: int = 16,
                         include_uppercase: bool = True,
                         include_lowercase: bool = True,
                         include_numbers: bool = True,
                         include_special: bool = True,
                         exclude_ambiguous: bool = True) -> str:
        """セキュアなパスワードを生成"""

        characters = ""

        if include_lowercase:
            chars = "abcdefghijklmnopqrstuvwxyz"
            if exclude_ambiguous:
                chars = chars.replace("l", "").replace("o", "")
            characters += chars

        if include_uppercase:
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if exclude_ambiguous:
                chars = chars.replace("I", "").replace("O", "")
            characters += chars

        if include_numbers:
            chars = "0123456789"
            if exclude_ambiguous:
                chars = chars.replace("0", "").replace("1", "")
            characters += chars

        if include_special:
            chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            characters += chars

        if not characters:
            raise ValueError("少なくとも1つの文字タイプを選択してください")

        # セキュアな乱数生成
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password

    def clear_memory(self, data: str) -> None:
        """メモリ内の機密データをクリア（ベストエフォート）"""
        # Pythonでは完全なメモリクリアは困難だが、参照を削除
        if hasattr(data, '__del__'):
            del data
