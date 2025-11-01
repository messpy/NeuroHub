#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ナレッジマネージャーテストスクリプト
"""

import sys
import os

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.db.knowledge_manager import KnowledgeManager

def test_knowledge_manager():
    """ナレッジマネージャーのテスト"""
    print("🧪 ナレッジマネージャーテスト開始")
    print("=" * 50)

    km = KnowledgeManager()

    try:
        # 1. 基本検索テスト
        print("\n1️⃣ 基本検索テスト")
        results = km.search_knowledge("Python")
        print(f"   📚 Python検索結果: {len(results)} 件")
        for result in results[:3]:  # 最初の3件だけ表示
            print(f"     - {result['title']} (使用回数: {result.get('usage_count', 0)})")

        # 2. 関連質問テスト
        print("\n2️⃣ 関連質問テスト")
        questions = km.get_related_questions(category="programming")
        print(f"   ❓ プログラミング関連質問: {len(questions)} 件")
        for q in questions:
            print(f"     - {q['main_question']}")

        # 3. 統計情報テスト
        print("\n3️⃣ 統計情報テスト")
        stats = km.get_knowledge_stats()
        print(f"   📊 総ナレッジ数: {stats.get('total_count', 0)} 件")
        print(f"   📂 カテゴリ数: {len(stats.get('categories', {}))}")
        print(f"   🌐 言語数: {len(stats.get('languages', {}))}")

        # 4. 新規ナレッジ追加テスト
        print("\n4️⃣ 新規ナレッジ追加テスト")
        new_id = km.add_knowledge(
            title="テスト用ナレッジ",
            content="これはテスト用のナレッジです。",
            category="test",
            tags="test,demo,sample"
        )
        print(f"   ✅ 新規ナレッジ追加: ID {new_id}")

        # 5. SQL指令一覧テスト
        print("\n5️⃣ SQL指令一覧テスト")
        sql_commands = km.get_sql_commands()
        print(f"   🔍 利用可能SQL指令: {len(sql_commands)} 件")
        for cmd in sql_commands:
            print(f"     - {cmd['sql_id']}: {cmd['title']}")

        # 6. 検索・推奨機能テスト
        print("\n6️⃣ 検索・推奨機能テスト")
        recommendations = km.search_and_recommend("Git")
        print(f"   🎯 Git検索結果: {len(recommendations['search_results'])} 件")
        print(f"   🤔 関連質問: {len(recommendations['related_questions'])} 件")
        if recommendations['suggested_category']:
            print(f"   📂 推奨カテゴリ: {recommendations['suggested_category']}")

        # 7. クリーンアップ（テストデータ削除）
        print("\n7️⃣ クリーンアップ")
        if new_id > 0:
            deleted = km.delete_knowledge(new_id)
            print(f"   🗑️ テストデータ削除: {'成功' if deleted else '失敗'}")

        print("\n✅ 全テスト完了！")

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

    finally:
        km.close()

if __name__ == "__main__":
    test_knowledge_manager()
