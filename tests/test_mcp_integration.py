#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mcp_integration.py

MCP強化システム統合テスト
- データベース統合MCPシステム
- LLM自発調査機能
- NatureRemo API統合
- 標準フロー準拠テスト
"""

import os
import sys
import json
import asyncio
import unittest
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.mcp.mcp_enhanced import EnhancedMCPServer, MCPRequest
from services.mcp.llm_investigator import LLMInvestigator

class TestMCPIntegration(unittest.TestCase):
    """MCP統合テストクラス"""

    def setUp(self):
        """テスト準備"""
        self.mcp_server = EnhancedMCPServer()
        self.investigator = LLMInvestigator()
        self.test_session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def test_mcp_server_initialization(self):
        """MCPサーバー初期化テスト"""
        print("\n🧪 1. MCPサーバー初期化テスト")

        # サーバーが正常に初期化されているか確認
        self.assertIsNotNone(self.mcp_server.db)
        self.assertIsNotNone(self.mcp_server.km)
        self.assertIsNotNone(self.mcp_server.session_id)

        # 利用可能なハンドラーが登録されているか確認
        expected_handlers = [
            'initialize', 'knowledge.search', 'knowledge.add',
            'llm.investigate', 'agents.list', 'session.info'
        ]
        for handler in expected_handlers:
            self.assertIn(handler, self.mcp_server.handlers)

        print("   ✅ MCPサーバー初期化成功")

    async def test_mcp_initialize_request(self):
        """MCP初期化リクエストテスト"""
        print("\n🧪 2. MCP初期化リクエストテスト")

        request_data = {
            'id': 'test_init_001',
            'method': 'initialize',
            'params': {'client_info': {'name': 'test_client', 'version': '1.0.0'}}
        }

        response = await self.mcp_server.process_request(request_data)

        # レスポンス基本構造確認
        self.assertEqual(response.id, 'test_init_001')
        self.assertIsNotNone(response.result)
        self.assertIsNone(response.error)

        # 初期化結果確認
        result = response.result
        self.assertEqual(result['status'], 'initialized')
        self.assertIn('server_info', result)
        self.assertIn('capabilities', result['server_info'])

        print("   ✅ MCP初期化成功")
        print(f"   📊 利用可能機能数: {len(result['server_info']['capabilities'])}")

    async def test_knowledge_operations(self):
        """ナレッジベース操作テスト"""
        print("\n🧪 3. ナレッジベース操作テスト")

        # ナレッジ追加テスト
        add_request = {
            'id': 'test_knowledge_add_001',
            'method': 'knowledge.add',
            'params': {
                'title': 'MCPテスト用ナレッジ',
                'content': 'これはMCPシステムのテスト用に作成されたナレッジです。',
                'category': 'test',
                'tags': 'mcp,test,integration',
                'user_id': 'test_user'
            }
        }

        add_response = await self.mcp_server.process_request(add_request)
        self.assertIsNone(add_response.error)
        self.assertEqual(add_response.result['status'], 'success')

        knowledge_id = add_response.result['knowledge_id']
        print(f"   ✅ ナレッジ追加成功: ID {knowledge_id}")

        # ナレッジ検索テスト
        search_request = {
            'id': 'test_knowledge_search_001',
            'method': 'knowledge.search',
            'params': {
                'query': 'MCP',
                'limit': 5
            }
        }

        search_response = await self.mcp_server.process_request(search_request)
        self.assertIsNone(search_response.error)
        self.assertGreaterEqual(search_response.result['results_count'], 1)

        print(f"   🔍 ナレッジ検索成功: {search_response.result['results_count']}件")

        # クリーンアップ
        self.mcp_server.db.delete_data('knowledge_base', f"id = {knowledge_id}")
        print("   🗑️ テストナレッジ削除完了")

    async def test_llm_investigation(self):
        """LLM自発調査テスト"""
        print("\n🧪 4. LLM自発調査テスト")

        request_data = {
            'id': 'test_investigation_001',
            'method': 'llm.investigate',
            'params': {
                'query': 'Pythonでファイル操作を行う方法',
                'max_agents': 2
            }
        }

        response = await self.mcp_server.process_request(request_data)

        self.assertIsNone(response.error)
        result = response.result

        # 調査結果の基本構造確認
        self.assertIn('query', result)
        self.assertIn('agents_used', result)
        self.assertIn('findings', result)
        self.assertIn('recommendations', result)

        print(f"   🤖 使用エージェント: {', '.join(result['agents_used'])}")
        print(f"   📊 調査結果: {len(result['findings'])}件")
        print(f"   💡 推奨アクション: {len(result['recommendations'])}件")
        print("   ✅ LLM自発調査成功")

    async def test_agents_list_and_call(self):
        """エージェント一覧・呼び出しテスト"""
        print("\n🧪 5. エージェント一覧・呼び出しテスト")

        # エージェント一覧取得
        list_request = {
            'id': 'test_agents_list_001',
            'method': 'agents.list',
            'params': {}
        }

        list_response = await self.mcp_server.process_request(list_request)
        self.assertIsNone(list_response.error)

        agents = list_response.result['available_agents']
        self.assertGreater(len(agents), 0)

        print(f"   📋 利用可能エージェント: {len(agents)}個")

        # エージェント呼び出しテスト
        agent_name = list(agents.keys())[0]
        call_request = {
            'id': 'test_agents_call_001',
            'method': 'agents.call',
            'params': {
                'agent': agent_name,
                'query': 'テスト呼び出し'
            }
        }

        call_response = await self.mcp_server.process_request(call_request)
        self.assertIsNone(call_response.error)
        self.assertEqual(call_response.result['status'], 'success')

        print(f"   🤖 {agent_name}エージェント呼び出し成功")
        print("   ✅ エージェント操作成功")

    async def test_session_management(self):
        """セッション管理テスト"""
        print("\n🧪 6. セッション管理テスト")

        # セッション情報取得
        info_request = {
            'id': 'test_session_info_001',
            'method': 'session.info',
            'params': {}
        }

        info_response = await self.mcp_server.process_request(info_request)
        self.assertIsNone(info_response.error)

        session_info = info_response.result
        self.assertIn('session_id', session_info)
        self.assertIn('database_status', session_info)

        print(f"   📋 セッションID: {session_info['session_id']}")
        print(f"   💾 DB状態: {session_info['database_status']}")

        # セッション履歴取得
        history_request = {
            'id': 'test_session_history_001',
            'method': 'session.history',
            'params': {'limit': 5}
        }

        history_response = await self.mcp_server.process_request(history_request)
        self.assertIsNone(history_response.error)

        print(f"   📜 履歴件数: {history_response.result['history_count']}")
        print("   ✅ セッション管理成功")

    async def test_database_operations(self):
        """データベース操作テスト"""
        print("\n🧪 7. データベース操作テスト")

        # データベース統計取得
        stats_request = {
            'id': 'test_db_stats_001',
            'method': 'database.stats',
            'params': {}
        }

        stats_response = await self.mcp_server.process_request(stats_request)
        self.assertIsNone(stats_response.error)

        stats = stats_response.result
        self.assertIn('total_tables', stats)
        self.assertIn('table_stats', stats)

        print(f"   📊 総テーブル数: {stats['total_tables']}")
        print(f"   💾 主要テーブル数: {len(stats['table_stats'])}")

        # 安全なクエリテスト
        query_request = {
            'id': 'test_db_query_001',
            'method': 'database.query',
            'params': {
                'query': 'SELECT COUNT(*) as total FROM llm_history'
            }
        }

        query_response = await self.mcp_server.process_request(query_request)
        self.assertIsNone(query_response.error)
        self.assertEqual(query_response.result['status'], 'success')

        print(f"   🔍 クエリ実行成功")
        print("   ✅ データベース操作成功")

    async def test_investigator_standalone(self):
        """調査エージェント単体テスト"""
        print("\n🧪 8. 調査エージェント単体テスト")

        result = await self.investigator.investigate(
            query="Git コミット メッセージ ベストプラクティス",
            max_agents=2,
            depth='normal'
        )

        # 結果検証
        self.assertIsNotNone(result.query)
        self.assertIsNotNone(result.start_time)
        self.assertIsNotNone(result.end_time)
        self.assertGreaterEqual(len(result.agents_used), 1)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)

        print(f"   🤖 使用エージェント: {', '.join(result.agents_used)}")
        print(f"   📚 既存知識: {len(result.knowledge_findings)}件")
        print(f"   📊 調査結果: {len(result.agent_findings)}件")
        print(f"   📈 信頼度: {result.confidence_score:.2f}")
        print("   ✅ 調査エージェント成功")

    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        print("\n🧪 9. エラーハンドリングテスト")

        # 存在しないメソッド
        invalid_request = {
            'id': 'test_error_001',
            'method': 'invalid.method',
            'params': {}
        }

        response = await self.mcp_server.process_request(invalid_request)
        self.assertIsNotNone(response.error)
        self.assertEqual(response.error['code'], 404)

        print("   ❌ 無効メソッドエラー処理成功")

        # 危険なSQLクエリ
        dangerous_query = {
            'id': 'test_error_002',
            'method': 'database.query',
            'params': {
                'query': 'DROP TABLE knowledge_base'
            }
        }

        dangerous_response = await self.mcp_server.process_request(dangerous_query)
        self.assertEqual(dangerous_response.result['status'], 'error')

        print("   🛡️ 危険クエリブロック成功")
        print("   ✅ エラーハンドリング成功")


async def run_all_tests():
    """全統合テストの実行"""
    print("[TEST] MCP強化システム統合テスト開始")
    print("=" * 60)

    test_instance = TestMCPIntegration()
    test_instance.setUp()

    try:
        # 同期テスト
        test_instance.test_mcp_server_initialization()

        # 非同期テスト
        await test_instance.test_mcp_initialize_request()
        await test_instance.test_knowledge_operations()
        await test_instance.test_llm_investigation()
        await test_instance.test_agents_list_and_call()
        await test_instance.test_session_management()
        await test_instance.test_database_operations()
        await test_instance.test_investigator_standalone()
        await test_instance.test_error_handling()

        print("\n" + "=" * 60)
        print("🎉 全統合テスト完了！")
        print("✅ MCPシステム強化が成功しました")

        return True

    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生: {e}")
        return False


# CLIインターフェース
async def main():
    """統合テストのCLI実行"""
    import argparse

    parser = argparse.ArgumentParser(description="MCP強化システム統合テスト")
    parser.add_argument('--verbose', action='store_true', help='詳細出力')
    parser.add_argument('--test', help='特定のテストのみ実行')

    args = parser.parse_args()

    if args.test:
        print(f"🧪 単体テスト実行: {args.test}")
        # 特定テストの実行ロジックをここに追加
    else:
        success = await run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    asyncio.run(main())
