#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベース初期化スクリプト
LLM履歴とコマンド履歴用のデータベースを自動作成
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.db.llm_history_manager import LLMHistoryManager


def main():
    """メイン関数"""
    db_path = project_root / "neurohub_llm.db"

    print(f"LLM履歴データベースを初期化しています: {db_path}")

    try:
        # データベース初期化
        manager = LLMHistoryManager(str(db_path))
        print("✅ データベース初期化完了")

        # テスト用セッション作成
        session_id = manager.start_session("initialization_test")
        print(f"✅ テストセッション作成: {session_id}")

        # テストログ記録
        log_id = manager.log_llm_request(
            provider="test",
            model="test-model",
            prompt_text="初期化テスト",
            response_text="初期化完了",
            success=True,
            request_type="initialization"
        )
        print(f"✅ テストログ記録: ID {log_id}")

        # セッション終了
        manager.end_session(session_id)
        print("✅ テストセッション終了")

        print(f"\n🎉 データベース準備完了: {db_path}")
        print("LLM履歴の自動記録が有効になります。")

    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
