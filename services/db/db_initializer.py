#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Initializer - データベース初期化とテーブル作成
統一されたDatabaseManagerを使用してNeuroHubのデータベースを初期化
"""

import os
import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.db.database_manager import DatabaseManager
from services.db.llm_history_schema import LLM_HISTORY_SCHEMA, LLM_HISTORY_INDICES, LLM_FTS_SCHEMA


class DatabaseInitializer:
    """データベース初期化クラス"""

    def __init__(self, db_path: str = None):
        self.db_manager = DatabaseManager(db_path)

    def initialize_all_tables(self) -> bool:
        """全テーブルの初期化"""
        print("🚀 NeuroHub データベース初期化開始")

        success = True

        # 1. 基本テーブル作成
        success &= self._create_basic_tables()

        # 2. インデックス作成
        success &= self._create_indexes()

        # 3. FTS（全文検索）テーブル作成
        success &= self._create_fts_tables()

        # 4. デフォルトデータ挿入
        success &= self._insert_default_data()

        if success:
            print("✅ データベース初期化完了")
            self._show_database_summary()
        else:
            print("❌ データベース初期化でエラーが発生しました")

        return success

    def _create_basic_tables(self) -> bool:
        """基本テーブル作成"""
        print("\n📋 基本テーブル作成中...")

        success = True
        for table_name, schema in LLM_HISTORY_SCHEMA.items():
            print(f"  テーブル作成: {table_name}")
            if not self.db_manager.create_table(table_name, schema):
                success = False

        return success

    def _create_indexes(self) -> bool:
        """インデックス作成"""
        print("\n🔍 インデックス作成中...")

        success = True
        for table_name, indexes in LLM_HISTORY_INDICES.items():
            print(f"  インデックス作成: {table_name}")
            for index_sql in indexes:
                try:
                    self.db_manager._execute_sql(index_sql)
                except Exception as e:
                    print(f"    ⚠️ インデックス作成失敗: {e}")
                    success = False

        return success

    def _create_fts_tables(self) -> bool:
        """FTS（全文検索）テーブル作成"""
        print("\n🔍 FTS（全文検索）テーブル作成中...")

        success = True
        for fts_name, fts_schema in LLM_FTS_SCHEMA.items():
            print(f"  FTSテーブル作成: {fts_name}")
            if not self.db_manager.create_table(fts_name, fts_schema):
                success = False

        return success

    def _insert_default_data(self) -> bool:
        """デフォルトデータ挿入"""
        print("\n📊 デフォルトデータ挿入中...")

        try:
            # デフォルトユーザー作成
            default_user = {
                "user_id": "default_user_001",
                "username": "default_user",
                "email": "default@neurohub.local",
                "full_name": "Default User",
                "preferred_provider": "ollama",
                "provider_config": "{}",
                "settings": '{"theme": "dark", "language": "ja"}',
                "api_keys": "{}",
                "usage_stats": '{"requests": 0, "tokens": 0}',
                "is_active": 1
            }

            # 既存ユーザーチェック
            existing_users = self.db_manager.get_data("users", {"username": "default_user"})
            if not existing_users:
                user_id = self.db_manager.insert_data("users", default_user)
                print(f"  デフォルトユーザー作成: ID {user_id}")
            else:
                print("  デフォルトユーザーは既に存在します")

            # サンプル知識ベース追加
            sample_knowledge = [
                {
                    "title": "Python基礎: リスト操作",
                    "content": "Pythonのリスト操作について\n\n# 基本操作\n- append(): 要素追加\n- remove(): 要素削除\n- sort(): ソート\n\n# 例\nmy_list = [1, 2, 3]\nmy_list.append(4)  # [1, 2, 3, 4]",
                    "category": "programming",
                    "tags": "python,list,tutorial",
                    "source_type": "manual",
                    "language": "python",
                    "relevance_score": 0.9,
                    "user_id": "default_user_001",
                    "is_public": 1
                },
                {
                    "title": "Git基礎: コミットメッセージ",
                    "content": "良いコミットメッセージの書き方\n\n# フォーマット\n:prefix: 簡潔な説明\n\n# プレフィックス例\n- :add: 新機能追加\n- :fix: バグ修正\n- :update: 既存機能更新\n- :docs: ドキュメント更新",
                    "category": "git",
                    "tags": "git,commit,best-practice",
                    "source_type": "manual",
                    "language": "markdown",
                    "relevance_score": 0.8,
                    "user_id": "default_user_001",
                    "is_public": 1
                }
            ]

            for knowledge in sample_knowledge:
                existing = self.db_manager.get_data("knowledge_base", {"title": knowledge["title"]})
                if not existing:
                    kb_id = self.db_manager.insert_data("knowledge_base", knowledge)
                    print(f"  サンプル知識追加: {knowledge['title']} (ID: {kb_id})")

            # 関連質問追加
            sample_questions = [
                {
                    "knowledge_id": 1,  # Python基礎の質問
                    "question": "Pythonでリストの最後に要素を追加するにはどうすればいいですか？",
                    "answer": "append()メソッドを使用します。例: my_list.append(新しい要素)",
                    "question_type": "howto",
                    "difficulty_level": 1,
                    "tags": "python,list,append",
                    "user_id": "default_user_001"
                },
                {
                    "knowledge_id": 2,  # Git基礎の質問
                    "question": "コミットメッセージにはどのようなプレフィックスを使えばいいですか？",
                    "answer": ":add:（新機能）、:fix:（バグ修正）、:update:（更新）、:docs:（ドキュメント）などを使用します。",
                    "question_type": "common",
                    "difficulty_level": 1,
                    "tags": "git,commit,prefix",
                    "user_id": "default_user_001"
                }
            ]

            for question in sample_questions:
                q_id = self.db_manager.insert_data("related_questions", question)
                print(f"  関連質問追加: ID {q_id}")

            return True

        except Exception as e:
            print(f"❌ デフォルトデータ挿入エラー: {e}")
            return False

    def _show_database_summary(self):
        """データベース概要表示"""
        print("\n📊 データベース概要:")
        print("=" * 50)

        tables = self.db_manager.get_tables()
        total_records = 0

        for table in sorted(tables):
            if table.endswith('_fts'):  # FTSテーブルはスキップ
                continue

            info = self.db_manager.get_table_info(table)
            record_count = info.get('record_count', 0)
            column_count = info.get('column_count', 0)
            indexes = info.get('indexes', [])

            total_records += record_count

            print(f"📋 {table}")
            print(f"   レコード数: {record_count}")
            print(f"   カラム数: {column_count}")
            print(f"   インデックス数: {len(indexes)}")

        print("=" * 50)
        print(f"総テーブル数: {len([t for t in tables if not t.endswith('_fts')])}")
        print(f"総レコード数: {total_records}")
        print(f"データベースファイル: {self.db_manager.db_path}")

    def reset_database(self) -> bool:
        """データベースリセット（全テーブル削除後再作成）"""
        print("⚠️ データベースリセット開始")

        # 全テーブル削除
        tables = self.db_manager.get_tables()
        for table in tables:
            if not table.startswith('sqlite_'):  # システムテーブル以外
                self.db_manager.drop_table(table)
                print(f"  テーブル削除: {table}")

        # 再初期化
        return self.initialize_all_tables()

    def close(self):
        """データベース接続を閉じる"""
        self.db_manager.close()


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description='NeuroHub データベース初期化')
    parser.add_argument('--reset', action='store_true', help='データベースをリセット')
    parser.add_argument('--db-path', type=str, help='データベースファイルパス')

    args = parser.parse_args()

    try:
        initializer = DatabaseInitializer(args.db_path)

        if args.reset:
            success = initializer.reset_database()
        else:
            success = initializer.initialize_all_tables()

        initializer.close()

        return 0 if success else 1

    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
