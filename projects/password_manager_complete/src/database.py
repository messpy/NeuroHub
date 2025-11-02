#!/usr/bin/env python3
"""
データベースマネージャー

SQLite3を使用したパスワードエントリのCRUD操作
完全なエラーハンドリング、ドキュメント、型ヒントを含む

Created by Ollama MCP Agent
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from contextlib import contextmanager

# ローカルモジュールのインポート
try:
    from .models import PasswordEntry, DatabaseSchema
except ImportError:
    # 相対インポートが失敗した場合の絶対インポート
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.models import PasswordEntry, DatabaseSchema

class DatabaseManager:
    """
    パスワードデータベース管理クラス
    
    SQLite3を使用してパスワードエントリのCRUD操作を提供する
    """
    
    def __init__(self, db_path: str = "data/passwords.db"):
        """
        データベースマネージャーの初期化
        
        Args:
            db_path (str): データベースファイルのパス
            
        Raises:
            RuntimeError: データベース初期化エラー
        """
        try:
            self.logger = logging.getLogger(__name__)
            self.db_path = Path(db_path)
            
            # データディレクトリの作成
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # データベースの初期化
            self._initialize_database()
            
            self.logger.info(f"データベースマネージャー初期化完了: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"データベースマネージャー初期化エラー: {e}")
            raise RuntimeError(f"データベース初期化エラー: {e}")
    
    def _initialize_database(self) -> None:
        """
        データベースとテーブルの初期化
        
        Raises:
            sqlite3.Error: データベース初期化エラー
        """
        try:
            with self._get_connection() as conn:
                # スキーマの作成
                DatabaseSchema.create_tables(conn)
                
                # バージョン情報の記録
                self._set_schema_version(conn, DatabaseSchema.get_version())
                
                self.logger.info("データベース初期化完了")
                
        except sqlite3.Error as e:
            self.logger.error(f"データベース初期化エラー: {e}")
            raise sqlite3.Error(f"データベース初期化エラー: {e}")
    
    @contextmanager
    def _get_connection(self):
        """
        データベース接続のコンテキストマネージャー
        
        Yields:
            sqlite3.Connection: データベース接続
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # 行を辞書形式で取得
            conn.execute("PRAGMA foreign_keys = ON")  # 外部キー制約を有効化
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"データベース接続エラー: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _set_schema_version(self, conn: sqlite3.Connection, version: str) -> None:
        """
        スキーマバージョンの設定
        
        Args:
            conn (sqlite3.Connection): データベース接続
            version (str): スキーマバージョン
        """
        try:
            # バージョン管理テーブルの作成
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            """)
            
            # バージョンの記録
            conn.execute("""
                INSERT OR REPLACE INTO schema_version (version, applied_at)
                VALUES (?, ?)
            """, (version, datetime.now().isoformat()))
            
            conn.commit()
            
        except sqlite3.Error as e:
            self.logger.error(f"スキーマバージョン設定エラー: {e}")
            raise
    
    def add_entry(self, entry: PasswordEntry) -> bool:
        """
        パスワードエントリの追加
        
        Args:
            entry (PasswordEntry): 追加するエントリ
            
        Returns:
            bool: 追加成功時True
            
        Raises:
            ValueError: 無効なエントリ
        """
        try:
            # エントリの妥当性検証
            if not entry.validate():
                raise ValueError("無効なパスワードエントリです")
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 重複チェック
                existing = cursor.execute("""
                    SELECT id FROM password_entries 
                    WHERE site = ? AND username = ?
                """, (entry.site, entry.username)).fetchone()
                
                if existing:
                    self.logger.warning(f"重複エントリ: {entry.site}/{entry.username}")
                    return False
                
                # エントリの挿入
                cursor.execute("""
                    INSERT INTO password_entries 
                    (site, username, encrypted_password, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entry.site,
                    entry.username,
                    entry.encrypted_password,
                    entry.notes,
                    entry.created_at.isoformat(),
                    entry.updated_at.isoformat()
                ))
                
                # IDの設定
                entry.id = cursor.lastrowid
                
                conn.commit()
                self.logger.info(f"エントリ追加成功: {entry.site}/{entry.username}")
                return True
                
        except sqlite3.IntegrityError as e:
            self.logger.error(f"整合性エラー: {e}")
            return False
        except Exception as e:
            self.logger.error(f"エントリ追加エラー: {e}")
            return False
    
    def get_entry(self, site: str, username: str = None) -> Optional[PasswordEntry]:
        """
        パスワードエントリの取得
        
        Args:
            site (str): サイト名
            username (str, optional): ユーザー名
            
        Returns:
            Optional[PasswordEntry]: 見つかったエントリ、なければNone
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if username:
                    # サイト名とユーザー名で検索
                    row = cursor.execute("""
                        SELECT * FROM password_entries 
                        WHERE site = ? AND username = ?
                    """, (site, username)).fetchone()
                else:
                    # サイト名のみで検索（最初の1件）
                    row = cursor.execute("""
                        SELECT * FROM password_entries 
                        WHERE site = ?
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (site,)).fetchone()
                
                if row:
                    entry = PasswordEntry.from_sql_row(row)
                    self.logger.info(f"エントリ取得成功: {site}/{username or 'any'}")
                    return entry
                else:
                    self.logger.info(f"エントリが見つかりません: {site}/{username or 'any'}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"エントリ取得エラー: {e}")
            return None
    
    def update_entry(self, entry: PasswordEntry) -> bool:
        """
        パスワードエントリの更新
        
        Args:
            entry (PasswordEntry): 更新するエントリ
            
        Returns:
            bool: 更新成功時True
        """
        try:
            if not entry.id:
                self.logger.error("更新にはエントリIDが必要です")
                return False
            
            if not entry.validate():
                raise ValueError("無効なパスワードエントリです")
            
            # 更新日時の設定
            entry.update_timestamp()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # エントリの更新
                cursor.execute("""
                    UPDATE password_entries 
                    SET site = ?, username = ?, encrypted_password = ?, 
                        notes = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    entry.site,
                    entry.username,
                    entry.encrypted_password,
                    entry.notes,
                    entry.updated_at.isoformat(),
                    entry.id
                ))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"エントリ更新成功: ID {entry.id}")
                    return True
                else:
                    self.logger.warning(f"更新対象が見つかりません: ID {entry.id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"エントリ更新エラー: {e}")
            return False
    
    def delete_entry(self, site: str, username: str = None, entry_id: int = None) -> bool:
        """
        パスワードエントリの削除
        
        Args:
            site (str): サイト名
            username (str, optional): ユーザー名
            entry_id (int, optional): エントリID
            
        Returns:
            bool: 削除成功時True
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if entry_id:
                    # IDで削除
                    cursor.execute("DELETE FROM password_entries WHERE id = ?", (entry_id,))
                elif username:
                    # サイト名とユーザー名で削除
                    cursor.execute("""
                        DELETE FROM password_entries 
                        WHERE site = ? AND username = ?
                    """, (site, username))
                else:
                    # サイト名のみで削除（全ユーザー）
                    cursor.execute("DELETE FROM password_entries WHERE site = ?", (site,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"エントリ削除成功: {cursor.rowcount}件")
                    return True
                else:
                    self.logger.warning("削除対象が見つかりません")
                    return False
                    
        except Exception as e:
            self.logger.error(f"エントリ削除エラー: {e}")
            return False
    
    def list_entries(self, limit: int = 100, offset: int = 0) -> List[PasswordEntry]:
        """
        パスワードエントリの一覧取得
        
        Args:
            limit (int): 取得件数の上限
            offset (int): 取得開始位置
            
        Returns:
            List[PasswordEntry]: エントリのリスト
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                rows = cursor.execute("""
                    SELECT * FROM password_entries 
                    ORDER BY site, username
                    LIMIT ? OFFSET ?
                """, (limit, offset)).fetchall()
                
                entries = [PasswordEntry.from_sql_row(row) for row in rows]
                
                self.logger.info(f"エントリ一覧取得: {len(entries)}件")
                return entries
                
        except Exception as e:
            self.logger.error(f"エントリ一覧取得エラー: {e}")
            return []
    
    def search_entries(self, query: str) -> List[PasswordEntry]:
        """
        パスワードエントリの検索
        
        Args:
            query (str): 検索クエリ
            
        Returns:
            List[PasswordEntry]: 検索結果のリスト
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # サイト名、ユーザー名、備考で部分一致検索
                search_pattern = f"%{query}%"
                rows = cursor.execute("""
                    SELECT * FROM password_entries 
                    WHERE site LIKE ? OR username LIKE ? OR notes LIKE ?
                    ORDER BY site, username
                """, (search_pattern, search_pattern, search_pattern)).fetchall()
                
                entries = [PasswordEntry.from_sql_row(row) for row in rows]
                
                self.logger.info(f"検索結果: {len(entries)}件 (クエリ: {query})")
                return entries
                
        except Exception as e:
            self.logger.error(f"エントリ検索エラー: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        データベース統計情報の取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 基本統計
                total_entries = cursor.execute("SELECT COUNT(*) FROM password_entries").fetchone()[0]
                unique_sites = cursor.execute("SELECT COUNT(DISTINCT site) FROM password_entries").fetchone()[0]
                
                # 最新・最古のエントリ
                latest = cursor.execute("""
                    SELECT created_at FROM password_entries 
                    ORDER BY created_at DESC LIMIT 1
                """).fetchone()
                
                oldest = cursor.execute("""
                    SELECT created_at FROM password_entries 
                    ORDER BY created_at ASC LIMIT 1
                """).fetchone()
                
                stats = {
                    'total_entries': total_entries,
                    'unique_sites': unique_sites,
                    'latest_entry': latest[0] if latest else None,
                    'oldest_entry': oldest[0] if oldest else None,
                    'database_size': self.db_path.stat().st_size if self.db_path.exists() else 0
                }
                
                self.logger.info("統計情報取得完了")
                return stats
                
        except Exception as e:
            self.logger.error(f"統計情報取得エラー: {e}")
            return {}
    
    def backup_database(self, backup_path: str) -> bool:
        """
        データベースのバックアップ
        
        Args:
            backup_path (str): バックアップファイルのパス
            
        Returns:
            bool: バックアップ成功時True
        """
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self._get_connection() as source:
                backup_conn = sqlite3.connect(str(backup_path))
                source.backup(backup_conn)
                backup_conn.close()
            
            self.logger.info(f"データベースバックアップ完了: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"データベースバックアップエラー: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """
        データベースの最適化（VACUUM）
        
        Returns:
            bool: 最適化成功時True
        """
        try:
            with self._get_connection() as conn:
                conn.execute("VACUUM")
                
            self.logger.info("データベース最適化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"データベース最適化エラー: {e}")
            return False

if __name__ == "__main__":
    try:
        print("=== データベースマネージャー テスト ===")
        
        # テスト用データベース
        test_db_path = "test_passwords.db"
        
        # データベースマネージャーの初期化
        db_manager = DatabaseManager(test_db_path)
        print("✅ データベース初期化完了")
        
        # テストエントリの作成
        test_entry = PasswordEntry(
            site="test.example.com",
            username="test_user",
            encrypted_password="encrypted_test_password",
            notes="テストエントリ"
        )
        
        # エントリの追加
        if db_manager.add_entry(test_entry):
            print("✅ エントリ追加成功")
        else:
            print("❌ エントリ追加失敗")
        
        # エントリの取得
        retrieved_entry = db_manager.get_entry("test.example.com", "test_user")
        if retrieved_entry:
            print(f"✅ エントリ取得成功: {retrieved_entry.site}")
        else:
            print("❌ エントリ取得失敗")
        
        # 統計情報の取得
        stats = db_manager.get_statistics()
        print(f"✅ 統計情報: {stats}")
        
        # クリーンアップ
        os.remove(test_db_path)
        print("✅ テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        sys.exit(1)