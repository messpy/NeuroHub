#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroHub データベース初期化スクリプト
Docker起動時およびローカル環境で使用
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.db.db_initializer import DatabaseInitializer


def main():
    """データベース初期化メイン処理"""
    print("🔧 NeuroHub データベース初期化開始...")
    print("=" * 60)

    try:
        # データベース初期化
        initializer = DatabaseInitializer()

        print("\n📋 全テーブル作成中...")
        initializer.initialize_all_tables()

        print("\n✅ データベース初期化完了！")
        print("=" * 60)
        print("\n📊 作成されたテーブル:")
        print("  - users: ユーザー管理")
        print("  - user_settings: ユーザー設定")
        print("  - knowledge_base: ナレッジベース")
        print("  - related_questions: 関連質問")
        print("  - llm_logs: LLM実行ログ")
        print("  - provider_status: プロバイダー状態")
        print("  - command_history: コマンド履歴")
        print("  - sql_commands: SQLコマンドライブラリ")
        print("  - git_commits: Gitコミット履歴")
        print("  - mcp_projects: MCPプロジェクト")
        print("  - mcp_hints: MCP開発ヒント")
        print("  - error_patterns: エラーパターン")
        print("  - その他システムテーブル...")
        print("\n🎉 NeuroHubの準備が整いました！")

        return 0

    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
