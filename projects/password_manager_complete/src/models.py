#!/usr/bin/env python3
"""
データモデル定義

SQLAlchemyを使用したパスワードエントリのデータモデル
完全なdocstring、型ヒント、エラーハンドリングを含む

Created by Ollama MCP Agent
"""

import sys
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import sqlite3

@dataclass
class PasswordEntry:
    """
    パスワードエントリのデータクラス
    
    Attributes:
        id (Optional[int]): エントリID（自動生成）
        site (str): サイト名
        username (str): ユーザー名
        encrypted_password (str): 暗号化されたパスワード
        notes (str): 備考
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
    """
    
    site: str
    username: str
    encrypted_password: str
    notes: str = ""
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """
        初期化後の処理
        
        Raises:
            ValueError: 必須フィールドが空の場合
        """
        if not self.site:
            raise ValueError("サイト名は必須です")
        if not self.username:
            raise ValueError("ユーザー名は必須です")
        if not self.encrypted_password:
            raise ValueError("暗号化パスワードは必須です")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換
        
        Returns:
            Dict[str, Any]: エントリの辞書表現
        """
        return {
            'id': self.id,
            'site': self.site,
            'username': self.username,
            'encrypted_password': self.encrypted_password,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PasswordEntry':
        """
        辞書からPasswordEntryを作成
        
        Args:
            data (Dict[str, Any]): エントリデータの辞書
            
        Returns:
            PasswordEntry: 作成されたエントリオブジェクト
            
        Raises:
            ValueError: 無効なデータの場合
        """
        try:
            entry = cls(
                site=data['site'],
                username=data['username'],
                encrypted_password=data['encrypted_password'],
                notes=data.get('notes', ''),
                id=data.get('id')
            )
            
            # 日時の設定
            if data.get('created_at'):
                entry.created_at = datetime.fromisoformat(data['created_at'])
            if data.get('updated_at'):
                entry.updated_at = datetime.fromisoformat(data['updated_at'])
                
            return entry
            
        except KeyError as e:
            raise ValueError(f"必須フィールドが不足しています: {e}")
        except Exception as e:
            raise ValueError(f"データ変換エラー: {e}")
    
    @classmethod
    def from_sql_row(cls, row: sqlite3.Row) -> 'PasswordEntry':
        """
        SQLiteのRowからPasswordEntryを作成
        
        Args:
            row (sqlite3.Row): データベース行
            
        Returns:
            PasswordEntry: 作成されたエントリオブジェクト
        """
        try:
            return cls(
                id=row['id'],
                site=row['site'],
                username=row['username'],
                encrypted_password=row['encrypted_password'],
                notes=row['notes'] or '',
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
        except Exception as e:
            raise ValueError(f"SQLデータ変換エラー: {e}")
    
    def update_timestamp(self) -> None:
        """更新日時を現在時刻に設定"""
        self.updated_at = datetime.now()
    
    def validate(self) -> bool:
        """
        エントリの妥当性検証
        
        Returns:
            bool: 妥当性検証結果
        """
        try:
            # 必須フィールドの確認
            if not self.site or not self.username or not self.encrypted_password:
                return False
            
            # サイト名の長さ制限
            if len(self.site) > 255:
                return False
            
            # ユーザー名の長さ制限
            if len(self.username) > 255:
                return False
            
            # 備考の長さ制限
            if len(self.notes) > 1000:
                return False
            
            return True
            
        except Exception:
            return False

class DatabaseSchema:
    """
    データベーススキーマ定義クラス
    
    SQLiteテーブル定義とマイグレーション機能を提供
    """
    
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS password_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site TEXT NOT NULL,
        username TEXT NOT NULL,
        encrypted_password TEXT NOT NULL,
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(site, username)
    );
    """
    
    CREATE_INDEX_SQL = [
        "CREATE INDEX IF NOT EXISTS idx_site ON password_entries(site);",
        "CREATE INDEX IF NOT EXISTS idx_username ON password_entries(username);",
        "CREATE INDEX IF NOT EXISTS idx_site_username ON password_entries(site, username);"
    ]
    
    @classmethod
    def create_tables(cls, connection: sqlite3.Connection) -> None:
        """
        テーブルとインデックスの作成
        
        Args:
            connection (sqlite3.Connection): データベース接続
            
        Raises:
            sqlite3.Error: SQL実行エラー
        """
        try:
            cursor = connection.cursor()
            
            # テーブル作成
            cursor.execute(cls.CREATE_TABLE_SQL)
            
            # インデックス作成
            for index_sql in cls.CREATE_INDEX_SQL:
                cursor.execute(index_sql)
            
            connection.commit()
            
        except sqlite3.Error as e:
            connection.rollback()
            raise sqlite3.Error(f"テーブル作成エラー: {e}")
    
    @classmethod
    def get_version(cls) -> str:
        """
        スキーマバージョンの取得
        
        Returns:
            str: スキーマバージョン
        """
        return "1.0.0"

if __name__ == "__main__":
    # テスト用のコード
    try:
        print("=== PasswordEntry テスト ===")
        
        # エントリの作成テスト
        entry = PasswordEntry(
            site="example.com",
            username="user@example.com",
            encrypted_password="encrypted_data_here",
            notes="テストエントリ"
        )
        
        print(f"作成されたエントリ: {entry}")
        print(f"辞書形式: {entry.to_dict()}")
        print(f"妥当性検証: {entry.validate()}")
        
        # 辞書からの作成テスト
        data = entry.to_dict()
        entry2 = PasswordEntry.from_dict(data)
        print(f"辞書から復元: {entry2}")
        
        print("✅ PasswordEntry テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        sys.exit(1)