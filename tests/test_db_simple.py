#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡易データベーステスト - 基本CRUD操作のテスト
"""

import sys
import os

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.db.database_manager import DatabaseManager

def test_basic_operations():
    """基本操作テスト"""
    print("🧪 データベース基本操作テスト")
    print("=" * 50)

    db = DatabaseManager()

    try:
        # 1. ユーザー情報確認
        print("\n1️⃣ ユーザー情報確認")
        users = db.get_data("users")
        print(f"   👥 登録ユーザー数: {len(users)}")

        # 2. ナレッジベース確認
        print("\n2️⃣ ナレッジベース確認")
        knowledge = db.get_data("knowledge_base")
        print(f"   📚 ナレッジベース件数: {len(knowledge)}")

        # 3. テストデータ挿入
        print("\n3️⃣ テストデータ挿入")
        test_data = {
            'title': '簡易テスト',
            'content': 'これはテストです',
            'category': 'test',
            'tags': 'test',
            'source_type': 'manual',
            'source_file': '',
            'language': 'ja',
            'relevance_score': 0.8,
            'usage_count': 0,
            'user_id': 1,
            'is_public': True
        }

        new_id = db.insert_data("knowledge_base", test_data)
        print(f"   ✅ 新規データ挿入: ID {new_id}")

        # 4. データ検索
        print("\n4️⃣ データ検索")
        test_kb = db.get_data("knowledge_base", f"id = {new_id}")
        if test_kb:
            print(f"   📄 検索結果: {test_kb[0]['title']}")

        # 5. データ更新
        print("\n5️⃣ データ更新")
        update_data = {'usage_count': 5}
        updated = db.update_data("knowledge_base", update_data, f"id = {new_id}")
        print(f"   ✅ 更新完了: {updated} 件")

        # 6. データ削除
        print("\n6️⃣ データ削除")
        deleted = db.delete_data("knowledge_base", f"id = {new_id}")
        print(f"   🗑️ 削除完了: {deleted} 件")

        # 7. 全文検索テスト
        print("\n7️⃣ 全文検索テスト")
        search_results = db.search_data("knowledge_base_fts", "Python")
        print(f"   🔍 'Python'検索結果: {len(search_results)} 件")

        print("\n✅ 全テスト完了！")

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_basic_operations()
