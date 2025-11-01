#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
データベースマネージャーのテストスクリプト
"""

import sys
import os
import json
from datetime import datetime

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.db.database_manager import DatabaseManager

def test_crud_operations():
    """CRUD操作のテスト"""
    print("🧪 データベースマネージャーのCRUD操作テスト")
    print("=" * 60)

    # データベースマネージャー初期化
    db = DatabaseManager()

    try:
        # 1. スキーマ取得テスト
        print("\n1️⃣ スキーマ取得テスト")
        schema = db.get_schema("users")
        print(f"   📋 usersテーブルスキーマ: {schema.get('column_count', 0)} カラム")
        columns = schema.get('columns', [])
        for col in columns[:3]:  # 最初の3カラムだけ表示
            print(f"     - {col['name']}: {col['type']}")

        # 2. カラム取得テスト
        print("\n2️⃣ カラム取得テスト")
        columns = db.get_columns("knowledge_base")
        print(f"   📋 knowledge_baseテーブルカラム: {columns}")

        # 3. データ検索テスト（既存データ）
        print("\n3️⃣ 既存データ検索テスト")
        users = db.get_data("users")
        print(f"   👥 ユーザー数: {len(users)}")
        if users:
            user = users[0]
            print(f"     - ID: {user['id']}, 名前: {user['username']}")

        # 4. ナレッジベース検索テスト
        print("\n4️⃣ ナレッジベース検索テスト")
        knowledge = db.get_data("knowledge_base")
        print(f"   📚 ナレッジベース件数: {len(knowledge)}")
        for kb in knowledge:
            print(f"     - タイトル: {kb['title']}")
            print(f"       タグ: {kb['tags']}")

        # 5. 全文検索テスト
        print("\n5️⃣ 全文検索テスト")
        search_results = db.search_data("knowledge_base_fts", "Python")
        print(f"   🔍 'Python'検索結果: {len(search_results)} 件")
        for result in search_results:
            print(f"     - マッチ: {result['title']}")

        # 6. 新規データ挿入テスト
        print("\n6️⃣ 新規データ挿入テスト")
        test_kb = {
            'title': 'テストナレッジ',
            'content': 'これはテスト用のナレッジです。',
            'category': 'test',
            'tags': 'test,demo',
            'source_type': 'manual',
            'source_file': '',
            'language': 'ja',
            'relevance_score': 0.8,
            'usage_count': 0,
            'user_id': 1,
            'is_public': True
        }

        insert_id = db.insert_data("knowledge_base", test_kb)
        print(f"   ✅ 新規ナレッジ挿入成功: ID {insert_id}")

        # 7. データ更新テスト
        print("\n7️⃣ データ更新テスト")
        update_data = {
            'usage_count': 1,
            'updated_at': datetime.now().isoformat()
        }
        updated_rows = db.update_data("knowledge_base", update_data, f"id = {insert_id}")
        print(f"   ✅ データ更新成功: {updated_rows} 行更新")

        # 8. 更新確認
        print("\n8️⃣ 更新確認テスト")
        updated_kb = db.get_data("knowledge_base", f"id = {insert_id}")
        if updated_kb:
            print(f"   📊 使用回数: {updated_kb[0]['usage_count']}")

        # 9. データ削除テスト
        print("\n9️⃣ データ削除テスト")
        deleted_rows = db.delete_data("knowledge_base", f"id = {insert_id}")
        print(f"   🗑️ データ削除成功: {deleted_rows} 行削除")

        # 10. 関連質問テスト
        print("\n🔟 関連質問検索テスト")
        related_q = db.get_data("related_questions", "category = 'programming'")
        print(f"   ❓ プログラミング関連質問: {len(related_q)} 件")
        for q in related_q:
            print(f"     - {q['main_question']}")

        print("\n✅ 全テスト完了！")

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

def test_performance():
    """パフォーマンステスト"""
    print("\n⚡ パフォーマンステスト")
    print("=" * 40)

    db = DatabaseManager()

    try:
        import time

        # 大量データ挿入テスト
        print("📊 大量データ挿入テスト（100件）")
        start_time = time.time()

        for i in range(100):
            test_data = {
                'title': f'パフォーマンステスト{i}',
                'content': f'これは{i}番目のテストデータです。' * 10,  # 長いコンテンツ
                'category': 'performance_test',
                'tags': f'test,performance,{i}',
                'source_type': 'automated',
                'source_file': '',
                'language': 'ja',
                'relevance_score': 0.5,
                'usage_count': 0,
                'user_id': 1,
                'is_public': True
            }
            db.insert_data("knowledge_base", test_data)

        insert_time = time.time() - start_time
        print(f"   ⏱️ 挿入時間: {insert_time:.2f}秒")

        # 検索パフォーマンステスト
        print("🔍 検索パフォーマンステスト")
        start_time = time.time()

        results = db.get_data("knowledge_base", "category = 'performance_test'")
        search_time = time.time() - start_time
        print(f"   ⏱️ 検索時間: {search_time:.2f}秒")
        print(f"   📊 検索結果: {len(results)} 件")

        # 全文検索パフォーマンス
        print("🔎 全文検索パフォーマンステスト")
        start_time = time.time()

        fts_results = db.search_data("knowledge_base_fts", "テスト")
        fts_time = time.time() - start_time
        print(f"   ⏱️ 全文検索時間: {fts_time:.2f}秒")
        print(f"   📊 全文検索結果: {len(fts_results)} 件")

        # クリーンアップ
        print("🧹 テストデータクリーンアップ")
        deleted = db.delete_data("knowledge_base", "category = 'performance_test'")
        print(f"   🗑️ 削除件数: {deleted}")

    except Exception as e:
        print(f"❌ パフォーマンステストエラー: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    test_crud_operations()
    test_performance()
