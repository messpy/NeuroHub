"""
パスワードマネージャーのコア機能
"""
import logging
from typing import List, Optional, Dict, Any
from .database import DatabaseManager
from .encryption import PasswordCrypto
from .config import Config

logger = logging.getLogger(__name__)

class PasswordManager:
    """パスワードマネージャーのメインクラス"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初期化

        Args:
            db_path: データベースファイルパス
        """
        self.db = DatabaseManager(db_path)
        self.crypto = PasswordCrypto()
        self._current_user_id: Optional[int] = None
        self._master_key: Optional[bytes] = None

    def create_user(self, username: str, master_password: str) -> bool:
        """
        新しいユーザーを作成

        Args:
            username: ユーザー名
            master_password: マスターパスワード

        Returns:
            作成成功時True
        """
        try:
            user_id = self.db.create_user(username, master_password)
            logger.info(f"ユーザー作成成功: {username}")
            return True
        except ValueError as e:
            logger.error(f"ユーザー作成失敗: {e}")
            return False
        except Exception as e:
            logger.error(f"ユーザー作成エラー: {e}")
            return False

    def login(self, username: str, master_password: str) -> bool:
        """
        ユーザーログイン

        Args:
            username: ユーザー名
            master_password: マスターパスワード

        Returns:
            ログイン成功時True
        """
        try:
            # ユーザー認証
            user_id = self.db.authenticate_user(username, master_password)
            if not user_id:
                return False

            # マスターキーを導出
            salt = self.db.get_user_salt(username)
            if not salt:
                logger.error("ソルト取得失敗")
                return False

            master_key = self.crypto.derive_key(master_password, salt)

            # セッション情報を保存
            self._current_user_id = user_id
            self._master_key = master_key

            logger.info(f"ログイン成功: {username}")
            return True

        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            return False

    def logout(self) -> None:
        """ログアウト"""
        self._current_user_id = None
        if self._master_key:
            # メモリクリア（ベストエフォート）
            self.crypto.clear_memory(str(self._master_key))
            self._master_key = None
        logger.info("ログアウト完了")

    def is_logged_in(self) -> bool:
        """ログイン状態確認"""
        return self._current_user_id is not None and self._master_key is not None

    def add_password(self, service_name: str, username: Optional[str] = None,
                    email: Optional[str] = None, password: str = "",
                    url: Optional[str] = None, notes: Optional[str] = None) -> Optional[int]:
        """
        パスワードを追加

        Args:
            service_name: サービス名
            username: ユーザー名
            email: メールアドレス
            password: パスワード
            url: URL
            notes: メモ

        Returns:
            作成されたエントリID（失敗時はNone）
        """
        if not self.is_logged_in():
            logger.error("ログインが必要です")
            return None

        try:
            entry_id = self.db.add_password_entry(
                self._current_user_id, self._master_key,
                service_name, username, email, password, url, notes
            )
            logger.info(f"パスワード追加成功: {service_name}")
            return entry_id
        except Exception as e:
            logger.error(f"パスワード追加エラー: {e}")
            return None

    def get_passwords(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        パスワード一覧を取得

        Args:
            search: 検索キーワード

        Returns:
            パスワードエントリのリスト
        """
        if not self.is_logged_in():
            logger.error("ログインが必要です")
            return []

        try:
            entries = self.db.get_password_entries(
                self._current_user_id, self._master_key, search
            )
            logger.info(f"パスワード取得: {len(entries)}件")
            return entries
        except Exception as e:
            logger.error(f"パスワード取得エラー: {e}")
            return []

    def get_password(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """
        単一のパスワードを取得

        Args:
            entry_id: エントリID

        Returns:
            パスワードエントリ（失敗時はNone）
        """
        if not self.is_logged_in():
            logger.error("ログインが必要です")
            return None

        try:
            entry = self.db.get_password_entry(
                self._current_user_id, entry_id, self._master_key
            )
            if entry:
                logger.info(f"パスワード取得成功: ID {entry_id}")
            else:
                logger.warning(f"パスワード見つからず: ID {entry_id}")
            return entry
        except Exception as e:
            logger.error(f"パスワード取得エラー: {e}")
            return None

    def update_password(self, entry_id: int, **updates) -> bool:
        """
        パスワードを更新

        Args:
            entry_id: エントリID
            **updates: 更新フィールド

        Returns:
            更新成功時True
        """
        if not self.is_logged_in():
            logger.error("ログインが必要です")
            return False

        try:
            success = self.db.update_password_entry(
                self._current_user_id, entry_id, self._master_key, **updates
            )
            if success:
                logger.info(f"パスワード更新成功: ID {entry_id}")
            else:
                logger.warning(f"パスワード更新失敗: ID {entry_id}")
            return success
        except Exception as e:
            logger.error(f"パスワード更新エラー: {e}")
            return False

    def delete_password(self, entry_id: int) -> bool:
        """
        パスワードを削除

        Args:
            entry_id: エントリID

        Returns:
            削除成功時True
        """
        if not self.is_logged_in():
            logger.error("ログインが必要です")
            return False

        try:
            success = self.db.delete_password_entry(self._current_user_id, entry_id)
            if success:
                logger.info(f"パスワード削除成功: ID {entry_id}")
            else:
                logger.warning(f"パスワード削除失敗: ID {entry_id}")
            return success
        except Exception as e:
            logger.error(f"パスワード削除エラー: {e}")
            return False

    def generate_password(self, length: int = 16,
                         include_uppercase: bool = True,
                         include_lowercase: bool = True,
                         include_numbers: bool = True,
                         include_special: bool = True,
                         exclude_ambiguous: bool = True) -> str:
        """
        セキュアなパスワードを生成

        Args:
            length: パスワード長
            include_uppercase: 大文字を含む
            include_lowercase: 小文字を含む
            include_numbers: 数字を含む
            include_special: 特殊文字を含む
            exclude_ambiguous: 紛らわしい文字を除外

        Returns:
            生成されたパスワード
        """
        try:
            password = self.crypto.generate_password(
                length, include_uppercase, include_lowercase,
                include_numbers, include_special, exclude_ambiguous
            )
            logger.info(f"パスワード生成成功: 長さ{length}")
            return password
        except Exception as e:
            logger.error(f"パスワード生成エラー: {e}")
            return ""

    def export_passwords(self) -> Optional[List[Dict[str, Any]]]:
        """
        パスワードをエクスポート

        Returns:
            パスワードエントリのリスト（失敗時はNone）
        """
        if not self.is_logged_in():
            logger.error("ログインが必要です")
            return None

        try:
            entries = self.get_passwords()
            logger.info(f"パスワードエクスポート: {len(entries)}件")
            return entries
        except Exception as e:
            logger.error(f"パスワードエクスポートエラー: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得

        Returns:
            統計情報辞書
        """
        if not self.is_logged_in():
            return {"error": "ログインが必要です"}

        try:
            entries = self.get_passwords()
            return {
                "total_entries": len(entries),
                "services": [entry["service_name"] for entry in entries],
                "last_updated": max(
                    [entry["updated_at"] for entry in entries], default="N/A"
                ) if entries else "N/A"
            }
        except Exception as e:
            logger.error(f"統計情報取得エラー: {e}")
            return {"error": str(e)}
