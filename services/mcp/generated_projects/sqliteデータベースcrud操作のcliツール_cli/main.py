#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sqliteデータベースcrud操作のcliツール_cli - SQLiteデータベース操作プロジェクト
"""

import sqlite3
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path


class DatabaseManager:
    """データベース管理クラス"""

    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """データベース初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        value TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print(f"✅ データベース初期化完了: {self.db_path}")
        except Exception as e:
            print(f"❌ データベース初期化失敗: {e}")
            sys.exit(1)

    def insert_record(self, name: str, value: str = None) -> dict:
        """レコード挿入"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO records (name, value) VALUES (?, ?)",
                    (name, value)
                )
                record_id = cursor.lastrowid
                conn.commit()

                return {
                    "success": True,
                    "id": record_id,
                    "name": name,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_all_records(self) -> list:
        """全レコード取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM records ORDER BY created_at DESC")
                records = cursor.fetchall()

                return [{
                    "id": record[0],
                    "name": record[1],
                    "value": record[2],
                    "created_at": record[3]
                } for record in records]
        except Exception as e:
            print(f"❌ レコード取得失敗: {e}")
            return []


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="SQLiteデータベースCRUD操作のCLIツールを実現するmediumレベルのPythonプロジェクト")
    parser.add_argument("--name", "-n", required=True, help="レコード名")
    parser.add_argument("--value", "-v", help="レコード値")
    parser.add_argument("--list", "-l", action="store_true", help="全レコード表示")
    parser.add_argument("--db", "-d", default="app.db", help="データベースファイル")

    args = parser.parse_args()

    # データベース管理開始
    db_manager = DatabaseManager(args.db)

    if args.list:
        records = db_manager.get_all_records()
        print(f"\n📋 全レコード ({len(records)} 件):")
        for record in records:
            print(f"  ID: {record['id']} | 名前: {record['name']} | 値: {record['value']} | 作成日時: {record['created_at']}")
    else:
        result = db_manager.insert_record(args.name, args.value)
        if result["success"]:
            print(f"✅ レコード挿入成功: ID={result['id']}, 名前={result['name']}, 値={result['value']}")
        else:
            print(f"❌ レコード挿入失敗: {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
