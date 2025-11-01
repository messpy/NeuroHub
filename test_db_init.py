#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Initialization and Test
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.db.user_manager import UserManager
from services.db.knowledge_manager import KnowledgeBaseManager

def test_database_creation():
    """データベース作成とテスト"""
    print("=== NeuroHub データベース初期化テスト ===")

    try:
        # ユーザー管理テスト
        print("\n--- ユーザー管理テスト ---")
        user_mgr = UserManager()

        # デフォルトユーザー作成
        current_user = user_mgr.get_current_user()
        print(f"✅ 現在ユーザー: {current_user['username']} (ID: {current_user['user_id']})")

        # 設定更新テスト
        success = user_mgr.update_user_settings(current_user['user_id'], {
            "debug_mode": True,
            "auto_commit": False
        })
        print(f"✅ ユーザー設定更新: {success}")

        # 知識ベース管理テスト
        print("\n--- 知識ベース管理テスト ---")
        kb_mgr = KnowledgeBaseManager()

        # サンプル知識項目追加
        knowledge_id = kb_mgr.add_knowledge(
            title="Git コミットメッセージ作成",
            content="""
良いGitコミットメッセージの書き方:

1. 最初の行は50文字以内で要約
2. プレフィックスを使用: :add:, :fix:, :update:, :refactor:
3. 変更の理由を明確に
4. 現在形で記述

例:
:fix: ユーザー認証エラーを修正
:add: レスポンス時間ログ機能を追加
:update: データベーススキーマを更新
            """,
            category="git",
            tags=["git", "commit", "best-practice"],
            language="text",
            user_id=current_user['user_id'],
            is_public=True
        )

        # 関連質問追加
        question_id = kb_mgr.add_related_question(
            knowledge_id=knowledge_id,
            question="コミットメッセージが長すぎる場合はどうすれば良いですか？",
            answer="最初の行は50文字以内で要約し、詳細は空行を挟んで2行目以降に記述してください。",
            question_type="common",
            difficulty_level=2,
            tags=["git", "commit", "length"],
            user_id=current_user['user_id']
        )

        print(f"✅ 知識項目追加: ID {knowledge_id}")
        print(f"✅ 関連質問追加: ID {question_id}")

        # 検索テスト
        print("\n--- 検索テスト ---")
        results = kb_mgr.search_knowledge("コミット")
        print(f"✅ 'コミット' 検索結果: {len(results)}件")

        questions = kb_mgr.search_questions("長すぎる")
        print(f"✅ '長すぎる' 質問検索結果: {len(questions)}件")

        # 統計情報
        stats = kb_mgr.get_statistics()
        print(f"\n--- 統計情報 ---")
        print(f"知識項目数: {stats['total_knowledge']}")
        print(f"質問数: {stats['total_questions']}")

        print("\n🎉 データベース初期化テスト完了!")
        return True

    except Exception as e:
        print(f"❌ データベーステストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database_creation()
