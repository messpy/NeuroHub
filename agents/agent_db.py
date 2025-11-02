#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Agent - データベース操作エージェント

SQLiteデータベースの操作を統一的に管理するエージェント
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.common import BaseAgent
from services.db.sqlite_craud import SQLiteCRAUD
from services.db.llm_history_manager import LLMHistoryManager


@dataclass
class DBQueryResult:
    """データベースクエリ結果"""
    success: bool
    data: Optional[List[Dict]] = None
    row_count: int = 0
    error: Optional[str] = None
    query: str = ""

    def to_dict(self) -> Dict:
        """辞書に変換"""
        return asdict(self)


class DatabaseAgent(BaseAgent):
    """
    データベース操作エージェント

    機能:
    - SQLiteデータベースの接続・操作
    - CRUD操作（Create, Read, Update, Delete）
    - スキーマ管理
    - データインポート/エクスポート
    - MCP用ヒントデータベース管理
    """

    def __init__(self, default_db: str = None):
        """
        初期化

        Args:
            default_db: デフォルトで使用するデータベースパス
        """
        super().__init__(name="database")
        self.project_root = project_root
        self.default_db = default_db or str(self.project_root / "neurohub.db")
        self.history_manager = LLMHistoryManager()

        # データベース接続キャッシュ
        self._db_connections: Dict[str, SQLiteCRAUD] = {}

        # MCP用ヒントDB
        self.mcp_hints_db = str(self.project_root / "data" / "mcp_hints.db")
        self._init_mcp_hints_db()

    def _init_mcp_hints_db(self):
        """MCP用ヒントデータベース初期化"""
        db = self.get_db(self.mcp_hints_db)

        schema = {
            "hints": """
                CREATE TABLE IF NOT EXISTS hints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    hint_text TEXT NOT NULL,
                    example_code TEXT,
                    tags TEXT,
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "code_snippets": """
                CREATE TABLE IF NOT EXISTS code_snippets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    language TEXT DEFAULT 'python',
                    code TEXT NOT NULL,
                    category TEXT,
                    tags TEXT,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "db_schemas": """
                CREATE TABLE IF NOT EXISTS db_schemas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    db_path TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    schema_sql TEXT NOT NULL,
                    columns_json TEXT,
                    sample_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(db_path, table_name)
                )
            """
        }

        indices = {
            "hints": [
                "CREATE INDEX IF NOT EXISTS idx_hints_category ON hints(category)",
                "CREATE INDEX IF NOT EXISTS idx_hints_keyword ON hints(keyword)",
                "CREATE INDEX IF NOT EXISTS idx_hints_priority ON hints(priority DESC)"
            ],
            "code_snippets": [
                "CREATE INDEX IF NOT EXISTS idx_snippets_category ON code_snippets(category)",
                "CREATE INDEX IF NOT EXISTS idx_snippets_usage ON code_snippets(usage_count DESC)"
            ],
            "db_schemas": [
                "CREATE INDEX IF NOT EXISTS idx_schemas_db_path ON db_schemas(db_path)"
            ]
        }

        db.create_tables(schema, indices)

    def get_db(self, db_path: str = None) -> SQLiteCRAUD:
        """
        データベース接続取得（キャッシュ付き）

        Args:
            db_path: データベースパス（Noneの場合はデフォルト）

        Returns:
            SQLiteCRAUDインスタンス
        """
        if db_path is None:
            db_path = self.default_db

        # 絶対パスに変換
        db_path = str(Path(db_path).resolve())

        if db_path not in self._db_connections:
            self._db_connections[db_path] = SQLiteCRAUD(db_path)

        return self._db_connections[db_path]

    def execute_query(self, db_path: str, query: str, params: Tuple = ()) -> DBQueryResult:
        """
        SQLクエリ実行

        Args:
            db_path: データベースパス
            query: SQLクエリ
            params: パラメータ

        Returns:
            DBQueryResult
        """
        try:
            db = self.get_db(db_path)
            results = db.execute_sql(query, params)  # すでに List[Dict[str, Any]]

            return DBQueryResult(
                success=True,
                data=results,
                row_count=len(results) if results else 0,
                query=query
            )
        except Exception as e:
            self.logger.error(f"クエリ実行エラー: {e}")
            return DBQueryResult(
                success=False,
                error=str(e),
                query=query
            )

    def get_table_schema(self, db_path: str, table_name: str) -> Optional[Dict]:
        """
        テーブルスキーマ取得

        Args:
            db_path: データベースパス
            table_name: テーブル名

        Returns:
            スキーマ情報辞書
        """
        try:
            db = self.get_db(db_path)

            # スキーマ取得
            schema_result = db.execute_sql(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )

            if not schema_result:
                return None

            schema_sql = schema_result[0]['sql']

            # カラム情報取得
            columns_result = db.execute_sql(f"PRAGMA table_info({table_name})")
            columns = [
                {
                    'cid': row['cid'],
                    'name': row['name'],
                    'type': row['type'],
                    'notnull': row['notnull'],
                    'default_value': row['dflt_value'],
                    'pk': row['pk']
                }
                for row in columns_result
            ]

            # サンプルデータ取得（最新5件）
            sample_data = db.select_where(table_name, limit=5)

            return {
                'table_name': table_name,
                'schema_sql': schema_sql,
                'columns': columns,
                'sample_data': sample_data[:3] if sample_data else []
            }
        except Exception as e:
            self.logger.error(f"スキーマ取得エラー: {e}")
            return None

    def list_tables(self, db_path: str) -> List[str]:
        """
        テーブル一覧取得

        Args:
            db_path: データベースパス

        Returns:
            テーブル名リスト
        """
        try:
            db = self.get_db(db_path)
            result = db.execute_sql(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row['name'] for row in result]
        except Exception as e:
            self.logger.error(f"テーブル一覧取得エラー: {e}")
            return []

    def add_mcp_hint(self, category: str, keyword: str, hint_text: str,
                     example_code: str = None, tags: str = None, priority: int = 0) -> bool:
        """
        MCPヒント追加

        Args:
            category: カテゴリ（'database', 'cli', 'web', 'api'等）
            keyword: キーワード
            hint_text: ヒント本文
            example_code: サンプルコード
            tags: タグ（カンマ区切り）
            priority: 優先度（高いほど優先）

        Returns:
            成功フラグ
        """
        try:
            db = self.get_db(self.mcp_hints_db)
            db.insert("hints", {
                "category": category,
                "keyword": keyword,
                "hint_text": hint_text,
                "example_code": example_code,
                "tags": tags,
                "priority": priority
            })
            return True
        except Exception as e:
            self.logger.error(f"ヒント追加エラー: {e}")
            return False

    def search_hints(self, keyword: str = None, category: str = None, limit: int = 10) -> List[Dict]:
        """
        ヒント検索

        Args:
            keyword: キーワード
            category: カテゴリ
            limit: 取得件数

        Returns:
            ヒントリスト
        """
        try:
            db = self.get_db(self.mcp_hints_db)

            where = {}
            if keyword:
                # キーワード部分一致
                results = db.execute_sql(
                    "SELECT * FROM hints WHERE keyword LIKE ? OR hint_text LIKE ? ORDER BY priority DESC LIMIT ?",
                    (f"%{keyword}%", f"%{keyword}%", limit)
                )
            elif category:
                results = db.execute_sql(
                    "SELECT * FROM hints WHERE category = ? ORDER BY priority DESC LIMIT ?",
                    (category, limit)
                )
            else:
                results = db.execute_sql(
                    "SELECT * FROM hints ORDER BY priority DESC LIMIT ?",
                    (limit,)
                )

            return results  # すでにList[Dict]
        except Exception as e:
            self.logger.error(f"ヒント検索エラー: {e}")
            return []

    def add_code_snippet(self, name: str, code: str, description: str = None,
                         language: str = 'python', category: str = None, tags: str = None) -> bool:
        """
        コードスニペット追加

        Args:
            name: スニペット名
            code: コード
            description: 説明
            language: 言語
            category: カテゴリ
            tags: タグ

        Returns:
            成功フラグ
        """
        try:
            db = self.get_db(self.mcp_hints_db)
            db.upsert("code_snippets", {
                "name": name,
                "description": description,
                "language": language,
                "code": code,
                "category": category,
                "tags": tags
            }, conflict_cols=["name"])
            return True
        except Exception as e:
            self.logger.error(f"スニペット追加エラー: {e}")
            return False

    def get_code_snippet(self, name: str) -> Optional[Dict]:
        """
        コードスニペット取得

        Args:
            name: スニペット名

        Returns:
            スニペット辞書
        """
        try:
            db = self.get_db(self.mcp_hints_db)
            result = db.select_where("code_snippets", where={"name": name})

            if not result:
                return None

            # 使用回数更新
            db.update_where(
                "code_snippets",
                {"usage_count": result[0]['usage_count'] + 1},
                {"name": name}
            )

            # 更新後のデータを再取得
            updated_result = db.select_where("code_snippets", where={"name": name})
            return dict(updated_result[0]) if updated_result else None
        except Exception as e:
            self.logger.error(f"スニペット取得エラー: {e}")
            return None

    def register_db_schema(self, db_path: str, table_name: str) -> bool:
        """
        データベーススキーマ登録（MCPヒント用）

        Args:
            db_path: データベースパス
            table_name: テーブル名

        Returns:
            成功フラグ
        """
        try:
            schema_info = self.get_table_schema(db_path, table_name)
            if not schema_info:
                return False

            db = self.get_db(self.mcp_hints_db)
            db.upsert("db_schemas", {
                "db_path": db_path,
                "table_name": table_name,
                "schema_sql": schema_info['schema_sql'],
                "columns_json": json.dumps(schema_info['columns'], ensure_ascii=False),
                "sample_data": json.dumps(schema_info['sample_data'], ensure_ascii=False)
            }, conflict_cols=["db_path", "table_name"])

            return True
        except Exception as e:
            self.logger.error(f"スキーマ登録エラー: {e}")
            return False

    def get_registered_schemas(self, db_path: str = None) -> List[Dict]:
        """
        登録済みスキーマ一覧取得

        Args:
            db_path: データベースパス（Noneの場合は全て）

        Returns:
            スキーマリスト
        """
        try:
            db = self.get_db(self.mcp_hints_db)

            if db_path:
                results = db.select_where("db_schemas", where={"db_path": db_path})
            else:
                results = db.execute_sql("SELECT * FROM db_schemas")

            if not results:
                return []

            return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"スキーマ一覧取得エラー: {e}")
            return []


# CLIインターフェース
def main():
    """CLI実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Database Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # list-tablesコマンド
    list_parser = subparsers.add_parser("list-tables", help="テーブル一覧表示")
    list_parser.add_argument("--db", required=True, help="データベースパス")

    # schemaコマンド
    schema_parser = subparsers.add_parser("schema", help="スキーマ表示")
    schema_parser.add_argument("--db", required=True, help="データベースパス")
    schema_parser.add_argument("--table", required=True, help="テーブル名")

    # queryコマンド
    query_parser = subparsers.add_parser("query", help="SQLクエリ実行")
    query_parser.add_argument("--db", required=True, help="データベースパス")
    query_parser.add_argument("--sql", required=True, help="SQLクエリ")

    # add-hintコマンド
    hint_parser = subparsers.add_parser("add-hint", help="MCPヒント追加")
    hint_parser.add_argument("--category", required=True, help="カテゴリ")
    hint_parser.add_argument("--keyword", required=True, help="キーワード")
    hint_parser.add_argument("--hint", required=True, help="ヒント本文")
    hint_parser.add_argument("--code", help="サンプルコード")
    hint_parser.add_argument("--priority", type=int, default=0, help="優先度")

    # search-hintsコマンド
    search_parser = subparsers.add_parser("search-hints", help="ヒント検索")
    search_parser.add_argument("--keyword", help="キーワード")
    search_parser.add_argument("--category", help="カテゴリ")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    agent = DatabaseAgent()

    if args.command == "list-tables":
        tables = agent.list_tables(args.db)
        print(f"\n=== {args.db} のテーブル一覧 ===")
        for table in tables:
            print(f"  - {table}")

    elif args.command == "schema":
        schema = agent.get_table_schema(args.db, args.table)
        if schema:
            print(f"\n=== {args.table} スキーマ ===")
            print(f"\n{schema['schema_sql']}\n")
            print("カラム:")
            for col in schema['columns']:
                print(f"  - {col['name']} ({col['type']})")
        else:
            print(f"テーブル '{args.table}' が見つかりません")

    elif args.command == "query":
        result = agent.execute_query(args.db, args.sql)
        if result.success:
            print(f"\n=== クエリ結果 ({result.row_count}件) ===")
            for row in result.data:
                print(row)
        else:
            print(f"エラー: {result.error}")

    elif args.command == "add-hint":
        success = agent.add_mcp_hint(
            args.category, args.keyword, args.hint,
            example_code=args.code, priority=args.priority
        )
        if success:
            print("✅ ヒント追加成功")
        else:
            print("❌ ヒント追加失敗")

    elif args.command == "search-hints":
        hints = agent.search_hints(keyword=args.keyword, category=args.category)
        print(f"\n=== ヒント検索結果 ({len(hints)}件) ===")
        for hint in hints:
            print(f"\n[{hint['category']}] {hint['keyword']}")
            print(f"  {hint['hint_text']}")
            if hint['example_code']:
                print(f"  例: {hint['example_code'][:100]}...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
