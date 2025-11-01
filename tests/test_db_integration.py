#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベース統合テスト - 一通りのDB操作をPythonコード内で実装・テスト
NeuroHubプロジェクトのDB機能の包括的動作確認
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.db.database_manager import DatabaseManager
from services.db.knowledge_manager import KnowledgeManager

# ロガー設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NeuroHubDBIntegration:
    """NeuroHub データベース統合クラス"""

    def __init__(self):
        """初期化"""
        self.db = DatabaseManager()
        self.km = KnowledgeManager()
        logger.info("🚀 NeuroHub DB統合システム初期化完了")

    def close(self):
        """リソースクリーンアップ"""
        self.km.close()
        self.db.close()
        logger.info("📝 データベース接続を閉じました")

    def run_full_integration_test(self):
        """包括的統合テスト実行"""
        print("🧪 NeuroHub データベース統合テスト")
        print("=" * 60)

        try:
            # 1. データベース初期化・構造確認
            self._test_database_structure()

            # 2. ユーザー管理テスト
            self._test_user_management()

            # 3. ナレッジベース管理テスト
            self._test_knowledge_management()

            # 4. 関連質問管理テスト
            self._test_related_questions()

            # 5. LLM履歴管理テスト
            self._test_llm_history()

            # 6. SQL実行機能テスト
            self._test_sql_execution()

            # 7. 統計・分析テスト
            self._test_analytics()

            # 8. 実際のワークフローシミュレーション
            self._test_workflow_simulation()

            print("\n✅ 全統合テスト完了！")

        except Exception as e:
            logger.error(f"❌ 統合テストエラー: {e}")
            import traceback
            traceback.print_exc()

    def _test_database_structure(self):
        """データベース構造テスト"""
        print("\n1️⃣ データベース構造確認テスト")
        print("-" * 40)

        # テーブル一覧取得
        tables = self.db.get_tables()
        print(f"   📋 総テーブル数: {len(tables)}")

        # 主要テーブルの構造確認
        main_tables = ['users', 'knowledge_base', 'related_questions', 'llm_history']
        for table in main_tables:
            if table in tables:
                schema = self.db.get_schema(table)
                columns = schema.get('columns', [])
                print(f"   📊 {table}: {len(columns)} カラム")

                # 重要カラムの確認
                col_names = [col['name'] for col in columns]
                if table == 'knowledge_base' and 'title' in col_names and 'content' in col_names:
                    print(f"     ✅ {table} 基本構造OK")
                elif table == 'users' and 'username' in col_names:
                    print(f"     ✅ {table} 基本構造OK")
                else:
                    print(f"     ⚠️ {table} 構造要確認")
            else:
                print(f"   ❌ {table} テーブルが存在しません")

    def _test_user_management(self):
        """ユーザー管理テスト"""
        print("\n2️⃣ ユーザー管理テスト")
        print("-" * 40)

        # 既存ユーザー確認
        users = self.db.get_data("users")
        print(f"   👥 登録ユーザー数: {len(users)}")

        if users:
            user = users[0]
            print(f"   👤 サンプルユーザー: {user.get('username', 'N/A')}")

        # 新規ユーザー追加テスト
        test_user = {
            'user_id': 'test_user_001',
            'username': 'テストユーザー',
            'email': 'test@neurohub.local',
            'full_name': 'Test User',
            'preferred_provider': 'ollama',
            'provider_config': json.dumps({'model': 'llama3.2'}),
            'settings': json.dumps({'language': 'ja', 'theme': 'dark'}),
            'is_active': True
        }

        user_id = self.db.insert_data("users", test_user)
        if user_id > 0:
            print(f"   ✅ テストユーザー追加成功: ID {user_id}")

            # 追加したユーザーを削除（クリーンアップ）
            deleted = self.db.delete_data("users", f"user_id = '{test_user['user_id']}'")
            print(f"   🗑️ テストユーザー削除: {'成功' if deleted else '失敗'}")
        else:
            print("   ❌ テストユーザー追加失敗")

    def _test_knowledge_management(self):
        """ナレッジベース管理テスト"""
        print("\n3️⃣ ナレッジベース管理テスト")
        print("-" * 40)

        # 既存ナレッジ確認
        knowledge_list = self.km.search_knowledge("")
        print(f"   📚 総ナレッジ数: {len(knowledge_list)}")

        # 新規ナレッジ追加
        test_knowledge = {
            'title': 'Python リスト操作マスターガイド',
            'content': '''
# Pythonリスト操作の基本

## リストの作成
```python
# 空のリスト
empty_list = []

# 初期値付きリスト
numbers = [1, 2, 3, 4, 5]
fruits = ['apple', 'banana', 'orange']
```

## 要素の追加
- append(): 末尾に追加
- insert(): 指定位置に挿入
- extend(): 複数要素を追加

## 要素の削除
- remove(): 値で削除
- pop(): インデックスで削除
- del: スライスで削除
            ''',
            'category': 'programming',
            'tags': 'python,list,programming,basic,sql_id=list_ops',
            'language': 'ja',
            'source_type': 'manual',
            'source_file': '',
            'user_id': 1,
            'is_public': True
        }

        knowledge_id = self.km.add_knowledge(**test_knowledge)
        if knowledge_id > 0:
            print(f"   ✅ ナレッジ追加成功: ID {knowledge_id}")

            # 検索テスト
            search_results = self.km.search_knowledge("Python リスト")
            print(f"   🔍 'Python リスト'検索結果: {len(search_results)} 件")

            # ID指定取得テスト
            retrieved = self.km.get_knowledge_by_id(knowledge_id)
            if retrieved:
                print(f"   📄 ID指定取得成功: {retrieved['title']}")
                print(f"   📊 使用回数: {retrieved.get('usage_count', 0)}")

            # 更新テスト
            updated = self.km.update_knowledge(knowledge_id, relevance_score=0.9)
            print(f"   ✏️ ナレッジ更新: {'成功' if updated else '失敗'}")

            # クリーンアップ
            deleted = self.km.delete_knowledge(knowledge_id)
            print(f"   🗑️ テストナレッジ削除: {'成功' if deleted else '失敗'}")
        else:
            print("   ❌ ナレッジ追加失敗")

    def _test_related_questions(self):
        """関連質問管理テスト"""
        print("\n4️⃣ 関連質問管理テスト")
        print("-" * 40)

        # 関連質問取得（実際のテーブル構造に合わせて直接取得）
        questions = self.db.get_data("related_questions", limit=5)
        print(f"   ❓ 既存関連質問数: {len(questions)}")

        # 新規関連質問追加（実際のテーブル構造に合わせて）
        question_data = {
            'knowledge_id': 1,  # 既存のナレッジIDを想定
            'question': 'Pythonでリストに要素を追加するにはどうすればいいですか？',
            'answer': 'append()メソッドを使用します。例: my_list.append(new_item)',
            'question_type': 'howto',
            'difficulty_level': 1,
            'tags': 'python,list,append',
            'usage_count': 0,
            'user_id': 'default_user'
        }

        question_id = self.db.insert_data("related_questions", question_data)

        if question_id > 0:
            print(f"   ✅ 関連質問追加成功: ID {question_id}")

            # 検索テスト（実際のカラム名を使用）
            python_qs = self.db.get_data("related_questions", f"tags LIKE '%python%'")
            print(f"   🔍 Python関連質問: {len(python_qs)} 件")
            if python_qs:
                print(f"   📋 質問: {python_qs[0].get('question')}")
                print(f"   💡 回答: {python_qs[0].get('answer')[:50]}...")
                print(f"   🏷️ タグ: {python_qs[0].get('tags')}")

            # クリーンアップ
            deleted = self.db.delete_data("related_questions", f"id = {question_id}")
            print(f"   🗑️ テスト関連質問削除: {'成功' if deleted else '失敗'}")
        else:
            print("   ❌ 関連質問追加失敗")

    def _test_llm_history(self):
        """LLM履歴管理テスト"""
        print("\n5️⃣ LLM履歴管理テスト")
        print("-" * 40)

        # 既存履歴確認
        history = self.db.get_data("llm_history", limit=5)
        print(f"   📜 LLM履歴件数: {len(history)}")

        # 新規履歴追加テスト（実際のテーブル構造に合わせて）
        test_history = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'session_id': f'test_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'provider': 'test_provider',
            'model': 'test-model-v1',
            'request_type': 'query',
            'prompt_text': 'Pythonでリストを操作する方法を教えて',
            'response_text': 'Pythonのリスト操作には、append()で要素追加、remove()で要素削除...',
            'status_code': 200,
            'success': True,
            'response_time_ms': 2500,
            'token_count_input': 25,
            'token_count_output': 150,
            'token_count_total': 175
        }

        history_id = self.db.insert_data("llm_history", test_history)
        if history_id > 0:
            print(f"   ✅ LLM履歴追加成功: ID {history_id}")

            # 検索テスト
            recent_history = self.db.get_data("llm_history",
                                            f"session_id = '{test_history['session_id']}'")
            if recent_history:
                print(f"   📊 セッション検索成功: {len(recent_history)} 件")
                print(f"   🤖 プロバイダー: {recent_history[0].get('provider')}")
                print(f"   📈 入力トークン: {recent_history[0].get('token_count_input')}")
                print(f"   📊 出力トークン: {recent_history[0].get('token_count_output')}")
                print(f"   ⏱️ 応答時間: {recent_history[0].get('response_time_ms')}ms")

            # クリーンアップ
            deleted = self.db.delete_data("llm_history", f"id = {history_id}")
            print(f"   🗑️ テスト履歴削除: {'成功' if deleted else '失敗'}")
        else:
            print("   ❌ LLM履歴追加失敗")

    def _test_sql_execution(self):
        """SQL実行機能テスト"""
        print("\n6️⃣ SQL実行機能テスト")
        print("-" * 40)

        # SQL指令一覧確認
        sql_commands = self.km.get_sql_commands()
        print(f"   🔍 利用可能SQL指令: {len(sql_commands)} 件")

        for cmd in sql_commands:
            print(f"     - {cmd['sql_id']}: {cmd['title']}")

        # 安全性チェックテスト
        safe_sql = "SELECT COUNT(*) FROM knowledge_base"
        unsafe_sql = "DROP TABLE users"

        print(f"   ✅ 安全なSQL判定: {self.km._is_safe_sql(safe_sql)}")
        print(f"   ❌ 危険なSQL判定: {self.km._is_safe_sql(unsafe_sql)}")

        # 実際のSQL実行テスト（安全なクエリのみ）
        if self.km._is_safe_sql(safe_sql):
            try:
                result = self.db._execute_sql(safe_sql).fetchall()
                print(f"   📊 ナレッジベース件数: {result[0][0] if result else 0}")
            except Exception as e:
                print(f"   ⚠️ SQL実行エラー: {e}")

    def _test_analytics(self):
        """統計・分析テスト"""
        print("\n7️⃣ 統計・分析テスト")
        print("-" * 40)

        # ナレッジベース統計
        stats = self.km.get_knowledge_stats()
        print(f"   📊 総ナレッジ数: {stats.get('total_count', 0)}")
        print(f"   📂 カテゴリ数: {len(stats.get('categories', {}))}")
        print(f"   🌐 言語数: {len(stats.get('languages', {}))}")

        # カテゴリ別詳細
        categories = stats.get('categories', {})
        for category, count in categories.items():
            print(f"     - {category}: {count} 件")

        # 人気ナレッジ
        top_used = stats.get('top_used', [])
        if top_used:
            print(f"   🔥 人気ナレッジTOP {len(top_used)}:")
            for kb in top_used:
                print(f"     - {kb['title']} (使用回数: {kb.get('usage_count', 0)})")

    def _test_workflow_simulation(self):
        """実際のワークフローシミュレーション"""
        print("\n8️⃣ ワークフローシミュレーション")
        print("-" * 40)

        # シナリオ: LLMエージェントからの問い合わせ処理
        print("   🎬 シナリオ: LLMエージェントからの問い合わせ処理")

        # 1. 質問受信
        user_query = "Gitコミットメッセージの書き方のベストプラクティスは？"
        print(f"   📥 ユーザー質問: {user_query}")

        # 2. ナレッジベース検索
        search_results = self.km.search_knowledge("Git コミット")
        print(f"   🔍 ナレッジ検索結果: {len(search_results)} 件")

        # 3. 関連質問検索（実際のテーブル構造を使用）
        related_qs = self.db.get_data("related_questions", f"tags LIKE '%git%'")
        print(f"   ❓ 関連質問: {len(related_qs)} 件")

        # 4. 総合的な推奨取得（簡略化）
        recommendations = {'search_results': search_results, 'suggested_category': 'git'}
        print(f"   🎯 推奨コンテンツ: {len(recommendations['search_results'])} 件")
        print(f"   💡 推奨カテゴリ: {recommendations.get('suggested_category', 'なし')}")

        # 5. セッション記録（模擬）- 実際のテーブル構造に合わせて
        session_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'session_id': f'workflow_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'provider': 'neurohub_kb_search',
            'model': 'knowledge_manager_v1',
            'request_type': 'knowledge_search',
            'prompt_text': user_query,
            'response_text': f'検索結果: {len(search_results)}件のナレッジを発見。推奨カテゴリ: {recommendations.get("suggested_category")}',
            'status_code': 200,
            'success': True,
            'response_time_ms': 1200,
            'token_count_input': len(user_query.split()),
            'token_count_output': 50,
            'token_count_total': len(user_query.split()) + 50
        }

        session_id = self.db.insert_data("llm_history", session_data)
        print(f"   📝 セッション記録: ID {session_id}")

        # 6. クリーンアップ
        if session_id > 0:
            deleted = self.db.delete_data("llm_history", f"session_id = '{session_data['session_id']}'")
            print(f"   🗑️ テストセッション削除: {'成功' if deleted else '失敗'}")

def main():
    """メイン実行関数"""
    integration = NeuroHubDBIntegration()

    try:
        integration.run_full_integration_test()
    finally:
        integration.close()

if __name__ == "__main__":
    main()
