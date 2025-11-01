#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Manager - 統一データベース操作インターフェース
NeuroHubプロジェクトの全テーブルに対する統一CRUD操作を提供
"""

import os
import json
import sqlite3
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """統一データベース管理クラス"""

    def __init__(self, db_path: str = None):
        """
        データベースマネージャー初期化

        Args:
            db_path: データベースファイルパス（Noneの場合はデフォルト）
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "neurohub.db"

        self.db_path = str(db_path)
        self.connection = None
        logger.info(f"データベース初期化: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続取得"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
        return self.connection

    def _execute_sql(self, sql: str, params: tuple = None) -> sqlite3.Cursor:
        """SQL実行（基本メソッド）"""
        try:
            conn = self._get_connection()
            if params:
                cursor = conn.execute(sql, params)
            else:
                cursor = conn.execute(sql)
            conn.commit()
            return cursor
        except Exception as e:
            logger.error(f"SQL実行エラー: {sql[:100]}... - {e}")
            raise

    # ============================================================================
    # テーブル操作メソッド
    # ============================================================================

    def create_table(self, table_name: str, schema: str) -> bool:
        """
        テーブル作成

        Args:
            table_name: テーブル名
            schema: CREATE TABLE文

        Returns:
            bool: 成功/失敗
        """
        try:
            self._execute_sql(schema)
            logger.info(f"テーブル作成成功: {table_name}")
            return True
        except Exception as e:
            logger.error(f"テーブル作成失敗: {table_name} - {e}")
            return False

    def drop_table(self, table_name: str) -> bool:
        """テーブル削除"""
        try:
            sql = f"DROP TABLE IF EXISTS {table_name}"
            self._execute_sql(sql)
            logger.info(f"テーブル削除成功: {table_name}")
            return True
        except Exception as e:
            logger.error(f"テーブル削除失敗: {table_name} - {e}")
            return False

    def get_tables(self) -> List[str]:
        """テーブル一覧取得"""
        try:
            sql = "SELECT name FROM sqlite_master WHERE type='table'"
            cursor = self._execute_sql(sql)
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"テーブル一覧取得失敗: {e}")
            return []

    def get_schema(self, table_name: str) -> Dict[str, Any]:
        """テーブル構造取得"""
        try:
            # PRAGMA table_info を使用
            sql = f"PRAGMA table_info({table_name})"
            cursor = self._execute_sql(sql)
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "name": row[1],
                    "type": row[2],
                    "not_null": bool(row[3]),
                    "default_value": row[4],
                    "primary_key": bool(row[5])
                })

            return {
                "table_name": table_name,
                "columns": columns,
                "column_count": len(columns)
            }
        except Exception as e:
            logger.error(f"スキーマ取得失敗: {table_name} - {e}")
            return {}

    def get_columns(self, table_name: str) -> List[str]:
        """カラム名一覧取得"""
        try:
            sql = f"PRAGMA table_info({table_name})"
            cursor = self._execute_sql(sql)
            return [row[1] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"カラム一覧取得失敗: {table_name} - {e}")
            return []

    # ============================================================================
    # データ操作メソッド（CRUD）
    # ============================================================================

    def insert_data(self, table_name: str, data: Dict[str, Any]) -> int:
        """
        データ挿入

        Args:
            table_name: テーブル名
            data: 挿入データ（辞書形式）

        Returns:
            int: 挿入されたレコードのID（失敗時は-1）
        """
        try:
            columns = list(data.keys())
            placeholders = ["?" for _ in columns]
            values = list(data.values())

            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor = self._execute_sql(sql, tuple(values))

            record_id = cursor.lastrowid
            logger.info(f"データ挿入成功: {table_name} (ID: {record_id})")
            return record_id
        except Exception as e:
            logger.error(f"データ挿入失敗: {table_name} - {e}")
            return -1

    def get_data(self, table_name: str, conditions: Union[Dict[str, Any], str] = None,
                 limit: int = None, order_by: str = None) -> List[Dict[str, Any]]:
        """
        データ取得

        Args:
            table_name: テーブル名
            conditions: 検索条件（辞書または文字列形式）
            limit: 取得件数制限
            order_by: ソート条件

        Returns:
            List[Dict]: 取得データ一覧
        """
        try:
            sql = f"SELECT * FROM {table_name}"
            params = []

            # WHERE句の構築
            if conditions:
                if isinstance(conditions, str):
                    sql += f" WHERE {conditions}"
                else:
                    where_clauses = []
                    for key, value in conditions.items():
                        where_clauses.append(f"{key} = ?")
                        params.append(value)
                    sql += f" WHERE {' AND '.join(where_clauses)}"

            # ORDER BY句の追加
            if order_by:
                sql += f" ORDER BY {order_by}"

            # LIMIT句の追加
            if limit:
                sql += f" LIMIT {limit}"

            cursor = self._execute_sql(sql, tuple(params))
            rows = cursor.fetchall()

            # sqlite3.Rowを辞書に変換
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"データ取得失敗: {table_name} - {e}")
            return []

    def update_data(self, table_name: str, data: Dict[str, Any],
                   conditions: Union[Dict[str, Any], str]) -> int:
        """
        データ更新

        Args:
            table_name: テーブル名
            data: 更新データ
            conditions: 更新条件（辞書または文字列）

        Returns:
            int: 更新件数
        """
        try:
            # SET句の構築
            set_clauses = []
            params = []
            for key, value in data.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)

            # WHERE句の構築
            if isinstance(conditions, str):
                where_clause = conditions
            else:
                where_clauses = []
                for key, value in conditions.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                where_clause = ' AND '.join(where_clauses)

            sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
            cursor = self._execute_sql(sql, tuple(params))

            updated_count = cursor.rowcount
            logger.info(f"データ更新成功: {table_name} ({updated_count}件)")
            return updated_count

        except Exception as e:
            logger.error(f"データ更新失敗: {table_name} - {e}")
            return 0

    def delete_data(self, table_name: str, conditions: Union[Dict[str, Any], str]) -> int:
        """
        データ削除

        Args:
            table_name: テーブル名
            conditions: 削除条件（辞書または文字列）

        Returns:
            int: 削除件数
        """
        try:
            # WHERE句の構築
            if isinstance(conditions, str):
                where_clause = conditions
                params = []
            else:
                where_clauses = []
                params = []
                for key, value in conditions.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                where_clause = ' AND '.join(where_clauses)

            sql = f"DELETE FROM {table_name} WHERE {where_clause}"
            cursor = self._execute_sql(sql, tuple(params))

            deleted_count = cursor.rowcount
            logger.info(f"データ削除成功: {table_name} ({deleted_count}件)")
            return deleted_count

        except Exception as e:
            logger.error(f"データ削除失敗: {table_name} - {e}")
            return 0

    # ============================================================================
    # 検索・集計メソッド
    # ============================================================================

    def search_data(self, table_name: str, query: str,
                   columns: List[str] = None) -> List[Dict[str, Any]]:
        """
        全文検索（FTS使用）

        Args:
            table_name: テーブル名
            query: 検索クエリ
            columns: 検索対象カラム（Noneの場合は全カラム）

        Returns:
            List[Dict]: 検索結果
        """
        try:
            # FTSテーブル名を構築
            fts_table = f"{table_name}_fts"

            # FTSテーブルの存在確認
            tables = self.get_tables()
            if fts_table not in tables:
                logger.warning(f"FTSテーブルが存在しません: {fts_table}")
                return []

            sql = f"SELECT * FROM {fts_table} WHERE {fts_table} MATCH ?"
            cursor = self._execute_sql(sql, (query,))
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"全文検索失敗: {table_name} - {e}")
            return []

    def count_data(self, table_name: str, conditions: Dict[str, Any] = None) -> int:
        """レコード数カウント"""
        try:
            sql = f"SELECT COUNT(*) FROM {table_name}"
            params = []

            if conditions:
                where_clauses = []
                for key, value in conditions.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                sql += f" WHERE {' AND '.join(where_clauses)}"

            cursor = self._execute_sql(sql, tuple(params))
            return cursor.fetchone()[0]

        except Exception as e:
            logger.error(f"カウント失敗: {table_name} - {e}")
            return 0

    def aggregate_data(self, table_name: str, func: str, column: str,
                      conditions: Dict[str, Any] = None) -> Any:
        """
        集計関数実行

        Args:
            table_name: テーブル名
            func: 集計関数（SUM, AVG, MAX, MIN など）
            column: 対象カラム
            conditions: 集計条件

        Returns:
            Any: 集計結果
        """
        try:
            sql = f"SELECT {func}({column}) FROM {table_name}"
            params = []

            if conditions:
                where_clauses = []
                for key, value in conditions.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                sql += f" WHERE {' AND '.join(where_clauses)}"

            cursor = self._execute_sql(sql, tuple(params))
            return cursor.fetchone()[0]

        except Exception as e:
            logger.error(f"集計失敗: {table_name} - {e}")
            return None

    # ============================================================================
    # カラム操作メソッド
    # ============================================================================

    def add_column(self, table_name: str, column_name: str,
                  column_type: str, default_value: Any = None) -> bool:
        """カラム追加"""
        try:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_value is not None:
                sql += f" DEFAULT {default_value}"

            self._execute_sql(sql)
            logger.info(f"カラム追加成功: {table_name}.{column_name}")
            return True

        except Exception as e:
            logger.error(f"カラム追加失敗: {table_name}.{column_name} - {e}")
            return False

    # ============================================================================
    # インデックス操作メソッド
    # ============================================================================

    def create_index(self, table_name: str, column_names: List[str],
                    index_name: str = None) -> bool:
        """インデックス作成"""
        try:
            if index_name is None:
                index_name = f"idx_{table_name}_{'_'.join(column_names)}"

            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({', '.join(column_names)})"
            self._execute_sql(sql)
            logger.info(f"インデックス作成成功: {index_name}")
            return True

        except Exception as e:
            logger.error(f"インデックス作成失敗: {index_name} - {e}")
            return False

    def get_indexes(self, table_name: str) -> List[str]:
        """テーブルのインデックス一覧取得"""
        try:
            sql = f"PRAGMA index_list({table_name})"
            cursor = self._execute_sql(sql)
            return [row[1] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"インデックス一覧取得失敗: {table_name} - {e}")
            return []

    # ============================================================================
    # 統計・情報取得メソッド
    # ============================================================================

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """テーブル情報取得"""
        try:
            # 基本情報
            record_count = self.count_data(table_name)
            schema = self.get_schema(table_name)
            indexes = self.get_indexes(table_name)

            # サイズ情報（概算）
            sql = f"SELECT COUNT(*) * LENGTH(GROUP_CONCAT(*)) as size_estimate FROM {table_name}"
            try:
                cursor = self._execute_sql(sql)
                size_estimate = cursor.fetchone()[0] or 0
            except:
                size_estimate = 0

            return {
                "table_name": table_name,
                "record_count": record_count,
                "column_count": len(schema.get("columns", [])),
                "indexes": indexes,
                "size_estimate_bytes": size_estimate,
                "schema": schema
            }

        except Exception as e:
            logger.error(f"テーブル情報取得失敗: {table_name} - {e}")
            return {}

    def get_all_tables(self) -> List[str]:
        """すべてのテーブル名を取得（MCPシステム互換）"""
        return self.get_tables()

    def execute_sql(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        SQLを実行して結果を返す（読み取り専用推奨）

        Args:
            sql: 実行するSQL文
            params: SQLパラメータ

        Returns:
            List[Dict]: クエリ結果（辞書のリスト）
        """
        try:
            cursor = self._execute_sql(sql, params)

            # SELECT文の場合は結果を返す
            if sql.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                # 辞書形式に変換
                columns = [description[0] for description in cursor.description] if cursor.description else []
                return [dict(zip(columns, row)) for row in rows]

            # その他の文の場合は空リストを返す
            return []

        except Exception as e:
            logger.error(f"SQL実行エラー: {sql[:100]}... - {e}")
            raise

    def close(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("データベース接続を閉じました")

    def __enter__(self):
        """withステートメント対応"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """withステートメント対応"""
        self.close()


# ============================================================================
# 便利関数
# ============================================================================

def get_default_db_manager() -> DatabaseManager:
    """デフォルトのDatabaseManagerインスタンスを取得"""
    return DatabaseManager()


if __name__ == "__main__":
    # テスト実行
    with DatabaseManager() as db:
        # テーブル一覧表示
        tables = db.get_tables()
        print(f"テーブル一覧: {tables}")

        # 各テーブルの情報表示
        for table in tables:
            info = db.get_table_info(table)
            print(f"\n{table}: {info.get('record_count', 0)}件")
