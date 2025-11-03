"""
データベース操作
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging
from .config import Config
from .encryption import PasswordCrypto

logger = logging.getLogger(__name__)

class DatabaseManager:
    """データベース管理クラス"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初期化

        Args:
            db_path: データベースファイルパス（Noneの場合はconfig使用）
        """
        self.db_path = db_path or str(Config.get_database_path())
        self.crypto = PasswordCrypto()
        self._ensure_database()

    def _ensure_database(self) -> None:
        """データベースファイルとテーブルを作成"""
        Config.ensure_database_dir()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    master_password_hash TEXT NOT NULL,
                    salt BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS password_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    service_name TEXT NOT NULL,
                    username TEXT,
                    email TEXT,
                    encrypted_password BLOB NOT NULL,
                    encryption_nonce BLOB NOT NULL,
                    url TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            # インデックス作成
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_password_entries_user_id ON password_entries(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_password_entries_service ON password_entries(service_name)")

            conn.commit()
            logger.info(f"データベース初期化完了: {self.db_path}")

    def create_user(self, username: str, master_password: str) -> int:
        """
        ユーザーを作成

        Args:
            username: ユーザー名
            master_password: マスターパスワード

        Returns:
            作成されたユーザーID

        Raises:
            ValueError: ユーザー名が既に存在する場合
        """
        hashed_password, salt = self.crypto.hash_master_password(master_password)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, master_password_hash, salt) VALUES (?, ?, ?)",
                    (username, hashed_password, salt)
                )
                user_id = cursor.lastrowid
                conn.commit()
                logger.info(f"ユーザー作成完了: {username} (ID: {user_id})")
                return user_id

        except sqlite3.IntegrityError:
            raise ValueError(f"ユーザー名 '{username}' は既に存在します")

    def authenticate_user(self, username: str, master_password: str) -> Optional[int]:
        """
        ユーザー認証

        Args:
            username: ユーザー名
            master_password: マスターパスワード

        Returns:
            認証成功時はユーザーID、失敗時はNone
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, master_password_hash FROM users WHERE username = ? AND is_active = 1",
                (username,)
            )
            result = cursor.fetchone()

            if result and self.crypto.verify_master_password(master_password, result[1]):
                logger.info(f"ユーザー認証成功: {username}")
                return result[0]

            logger.warning(f"ユーザー認証失敗: {username}")
            return None

    def add_password_entry(self, user_id: int, master_key: bytes,
                          service_name: str, username: Optional[str] = None,
                          email: Optional[str] = None, password: str = "",
                          url: Optional[str] = None, notes: Optional[str] = None) -> int:
        """
        パスワードエントリを追加

        Args:
            user_id: ユーザーID
            master_key: マスターキー（暗号化用）
            service_name: サービス名
            username: ユーザー名
            email: メールアドレス
            password: パスワード
            url: URL
            notes: メモ

        Returns:
            作成されたエントリID
        """
        encrypted_password, nonce = self.crypto.encrypt_password(password, master_key)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO password_entries
                (user_id, service_name, username, email, encrypted_password, encryption_nonce, url, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, service_name, username, email, encrypted_password, nonce, url, notes))

            entry_id = cursor.lastrowid
            conn.commit()
            logger.info(f"パスワードエントリ追加: {service_name} (ID: {entry_id})")
            return entry_id

    def get_password_entries(self, user_id: int, master_key: bytes,
                           search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        パスワードエントリを取得

        Args:
            user_id: ユーザーID
            master_key: マスターキー（復号化用）
            search: 検索キーワード（サービス名で部分一致）

        Returns:
            パスワードエントリのリスト
        """
        query = """
            SELECT id, service_name, username, email, encrypted_password,
                   encryption_nonce, url, notes, created_at, updated_at
            FROM password_entries
            WHERE user_id = ?
        """
        params = [user_id]

        if search:
            query += " AND service_name LIKE ?"
            params.append(f"%{search}%")

        query += " ORDER BY service_name"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            results = []

            for row in cursor.fetchall():
                try:
                    decrypted_password = self.crypto.decrypt_password(
                        row['encrypted_password'],
                        row['encryption_nonce'],
                        master_key
                    )

                    results.append({
                        'id': row['id'],
                        'service_name': row['service_name'],
                        'username': row['username'],
                        'email': row['email'],
                        'password': decrypted_password,
                        'url': row['url'],
                        'notes': row['notes'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                except Exception as e:
                    logger.error(f"パスワード復号化エラー (ID: {row['id']}): {e}")
                    continue

            return results

    def get_password_entry(self, user_id: int, entry_id: int, master_key: bytes) -> Optional[Dict[str, Any]]:
        """
        単一のパスワードエントリを取得

        Args:
            user_id: ユーザーID
            entry_id: エントリID
            master_key: マスターキー

        Returns:
            パスワードエントリまたはNone
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, service_name, username, email, encrypted_password,
                       encryption_nonce, url, notes, created_at, updated_at
                FROM password_entries
                WHERE id = ? AND user_id = ?
            """, (entry_id, user_id))

            row = cursor.fetchone()
            if not row:
                return None

            try:
                decrypted_password = self.crypto.decrypt_password(
                    row['encrypted_password'],
                    row['encryption_nonce'],
                    master_key
                )

                return {
                    'id': row['id'],
                    'service_name': row['service_name'],
                    'username': row['username'],
                    'email': row['email'],
                    'password': decrypted_password,
                    'url': row['url'],
                    'notes': row['notes'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            except Exception as e:
                logger.error(f"パスワード復号化エラー (ID: {entry_id}): {e}")
                return None

    def update_password_entry(self, user_id: int, entry_id: int, master_key: bytes,
                            **updates) -> bool:
        """
        パスワードエントリを更新

        Args:
            user_id: ユーザーID
            entry_id: エントリID
            master_key: マスターキー
            **updates: 更新フィールド

        Returns:
            更新成功時True
        """
        if not updates:
            return False

        # パスワードフィールドがある場合は暗号化
        if 'password' in updates:
            encrypted_password, nonce = self.crypto.encrypt_password(updates['password'], master_key)
            updates['encrypted_password'] = encrypted_password
            updates['encryption_nonce'] = nonce
            del updates['password']

        # 更新クエリを構築
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        set_clause += ", updated_at = CURRENT_TIMESTAMP"

        query = f"UPDATE password_entries SET {set_clause} WHERE id = ? AND user_id = ?"
        params = list(updates.values()) + [entry_id, user_id]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            updated = cursor.rowcount > 0
            conn.commit()

            if updated:
                logger.info(f"パスワードエントリ更新: ID {entry_id}")
            else:
                logger.warning(f"パスワードエントリ更新失敗: ID {entry_id}")

            return updated

    def delete_password_entry(self, user_id: int, entry_id: int) -> bool:
        """
        パスワードエントリを削除

        Args:
            user_id: ユーザーID
            entry_id: エントリID

        Returns:
            削除成功時True
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM password_entries WHERE id = ? AND user_id = ?",
                (entry_id, user_id)
            )
            deleted = cursor.rowcount > 0
            conn.commit()

            if deleted:
                logger.info(f"パスワードエントリ削除: ID {entry_id}")
            else:
                logger.warning(f"パスワードエントリ削除失敗: ID {entry_id}")

            return deleted

    def get_user_salt(self, username: str) -> Optional[bytes]:
        """
        ユーザーのソルトを取得

        Args:
            username: ユーザー名

        Returns:
            ソルトまたはNone
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT salt FROM users WHERE username = ? AND is_active = 1",
                (username,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def close(self) -> None:
        """データベース接続をクローズ（必要に応じて実装）"""
        pass
