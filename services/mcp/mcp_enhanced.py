#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_enhanced.py

NeuroHub強化版MCPシステム
- データベース統合機能
- LLM自発調査機能
- 標準フロー準拠
- ナレッジベース活用
- エージェント連携
"""

from __future__ import annotations
import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.db.database_manager import DatabaseManager
from services.db.knowledge_manager import KnowledgeManager
from services.llm.llm_common import load_env_from_config, DebugLogger

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MCPRequest:
    """標準MCP request format"""
    id: str
    method: str
    params: Dict[str, Any]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class MCPResponse:
    """標準MCP response format"""
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class MCPError:
    """標準MCP error format"""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None

class EnhancedMCPServer:
    """
    NeuroHub強化版MCPサーバー

    機能:
    - データベース統合 (users, knowledge_base, llm_history)
    - LLM自発調査機能
    - エージェント連携 (git, web, weather, command)
    - ナレッジベース検索・管理
    - セッション管理とLLM履歴追跡
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.km = KnowledgeManager(self.db)
        self.session_id = f"mcp_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.debug_logger = DebugLogger()

        # 利用可能なエージェント
        self.available_agents = {
            'git': 'Git操作・コミット管理',
            'web': 'Web情報収集・検索',
            'weather': '天気情報取得',
            'command': 'システムコマンド実行',
            'knowledge': 'ナレッジベース検索・管理',
            'llm': 'LLM推論・質問応答'
        }

        # メソッドハンドラーマッピング
        self.handlers = {
            'initialize': self._handle_initialize,
            'knowledge.search': self._handle_knowledge_search,
            'knowledge.add': self._handle_knowledge_add,
            'knowledge.update': self._handle_knowledge_update,
            'knowledge.delete': self._handle_knowledge_delete,
            'questions.search': self._handle_questions_search,
            'questions.add': self._handle_questions_add,
            'llm.investigate': self._handle_llm_investigate,
            'agents.list': self._handle_agents_list,
            'agents.call': self._handle_agents_call,
            'session.info': self._handle_session_info,
            'session.history': self._handle_session_history,
            'database.stats': self._handle_database_stats,
            'database.query': self._handle_database_query
        }

        logger.info(f"🚀 Enhanced MCP Server 初期化完了 - Session: {self.session_id}")

    async def process_request(self, request_data: Dict[str, Any]) -> MCPResponse:
        """
        MCPリクエストを処理

        Args:
            request_data: リクエストデータ

        Returns:
            MCPResponse: 処理結果
        """
        try:
            # リクエスト解析
            request = MCPRequest(**request_data)

            # LLM履歴に記録
            await self._log_llm_interaction(
                request_type='mcp_request',
                prompt_text=f"Method: {request.method}, Params: {json.dumps(request.params, ensure_ascii=False)}",
                metadata={'request_id': request.id, 'method': request.method}
            )

            # ハンドラー実行
            if request.method not in self.handlers:
                return MCPResponse(
                    id=request.id,
                    error=asdict(MCPError(
                        code=404,
                        message=f"Unknown method: {request.method}",
                        data={'available_methods': list(self.handlers.keys())}
                    ))
                )

            handler = self.handlers[request.method]
            result = await handler(request.params)

            response = MCPResponse(
                id=request.id,
                result=result,
                metadata={
                    'session_id': self.session_id,
                    'handler': request.method,
                    'execution_time': datetime.now().isoformat()
                }
            )

            # 成功した場合もLLM履歴に記録
            await self._log_llm_interaction(
                request_type='mcp_response',
                prompt_text=f"Method: {request.method}",
                response_text=json.dumps(result, ensure_ascii=False)[:500] + "..." if len(json.dumps(result, ensure_ascii=False)) > 500 else json.dumps(result, ensure_ascii=False),
                status_code=200,
                success=True,
                metadata={'request_id': request.id, 'method': request.method}
            )

            return response

        except Exception as e:
            logger.error(f"Request processing error: {e}")

            # エラーもLLM履歴に記録
            await self._log_llm_interaction(
                request_type='mcp_error',
                prompt_text=f"Error processing: {request_data}",
                response_text=str(e),
                status_code=500,
                success=False,
                error_message=str(e)
            )

            return MCPResponse(
                id=request_data.get('id', 'unknown'),
                error=asdict(MCPError(
                    code=500,
                    message=f"Internal server error: {str(e)}"
                ))
            )

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """MCP初期化ハンドラー"""
        return {
            'status': 'initialized',
            'server_info': {
                'name': 'NeuroHub Enhanced MCP Server',
                'version': '1.0.0',
                'capabilities': list(self.handlers.keys()),
                'session_id': self.session_id,
                'database': {
                    'tables': len(self.db.get_all_tables()),
                    'knowledge_count': len(self.km.search_knowledge('', limit=1000)),
                    'available_agents': self.available_agents
                }
            }
        }

    async def _handle_knowledge_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ナレッジベース検索"""
        query = params.get('query', '')
        category = params.get('category')
        limit = params.get('limit', 10)

        results = self.km.search_knowledge(query, category=category, limit=limit)

        return {
            'query': query,
            'category': category,
            'results_count': len(results),
            'results': results,
            'suggestions': await self._get_related_suggestions(query)
        }

    async def _handle_knowledge_add(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ナレッジベース追加"""
        title = params.get('title', '')
        content = params.get('content', '')
        category = params.get('category', 'general')
        tags = params.get('tags', '')

        knowledge_id = self.km.add_knowledge(
            title=title,
            content=content,
            category=category,
            tags=tags,
            user_id=params.get('user_id', 'mcp_user')
        )

        return {
            'status': 'success' if knowledge_id > 0 else 'failed',
            'knowledge_id': knowledge_id,
            'title': title,
            'category': category
        }

    async def _handle_knowledge_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ナレッジベース更新"""
        knowledge_id = params.get('knowledge_id')
        updates = {k: v for k, v in params.items() if k != 'knowledge_id'}

        success = self.db.update_data('knowledge_base', updates, f"id = {knowledge_id}")

        return {
            'status': 'success' if success else 'failed',
            'knowledge_id': knowledge_id,
            'updated_fields': list(updates.keys())
        }

    async def _handle_knowledge_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ナレッジベース削除"""
        knowledge_id = params.get('knowledge_id')

        success = self.db.delete_data('knowledge_base', f"id = {knowledge_id}")

        return {
            'status': 'success' if success else 'failed',
            'knowledge_id': knowledge_id
        }

    async def _handle_questions_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """関連質問検索"""
        query = params.get('query', '')
        limit = params.get('limit', 5)

        # タグベースで検索
        questions = self.db.get_data('related_questions', f"tags LIKE '%{query}%'", limit=limit)

        return {
            'query': query,
            'results_count': len(questions),
            'questions': questions
        }

    async def _handle_questions_add(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """関連質問追加"""
        question_data = {
            'knowledge_id': params.get('knowledge_id', 1),
            'question': params.get('question', ''),
            'answer': params.get('answer', ''),
            'question_type': params.get('question_type', 'general'),
            'difficulty_level': params.get('difficulty_level', 1),
            'tags': params.get('tags', ''),
            'usage_count': 0,
            'user_id': params.get('user_id', 'mcp_user')
        }

        question_id = self.db.insert_data('related_questions', question_data)

        return {
            'status': 'success' if question_id > 0 else 'failed',
            'question_id': question_id,
            'question': question_data['question']
        }

    async def _handle_llm_investigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM自発調査機能

        TASK_MANAGEMENT.md要件:
        - LLMがDBを参照して各エージェントを呼び出し
        - 自発的に調査を行う
        - 調査時は明確に通知
        """
        query = params.get('query', '')
        max_agents = params.get('max_agents', 3)

        investigation_results = {
            'query': query,
            'investigation_start': datetime.now().isoformat(),
            'agents_used': [],
            'findings': [],
            'knowledge_found': [],
            'recommendations': []
        }

        # 1. ナレッジベース検索
        logger.info(f"🔍 LLM自発調査開始: {query}")
        knowledge_results = self.km.search_knowledge(query, limit=5)
        investigation_results['knowledge_found'] = knowledge_results

        # 2. 関連質問検索
        related_questions = self.db.get_data('related_questions', f"tags LIKE '%{query}%'", limit=3)

        # 3. 利用可能エージェントの判定
        relevant_agents = await self._determine_relevant_agents(query)

        # 4. エージェント呼び出し（シミュレーション）
        for agent_name in relevant_agents[:max_agents]:
            agent_result = await self._simulate_agent_call(agent_name, query)
            investigation_results['agents_used'].append(agent_name)
            investigation_results['findings'].append({
                'agent': agent_name,
                'result': agent_result,
                'timestamp': datetime.now().isoformat()
            })

        # 5. 推奨アクション生成
        recommendations = await self._generate_recommendations(query, knowledge_results, investigation_results['findings'])
        investigation_results['recommendations'] = recommendations

        investigation_results['investigation_end'] = datetime.now().isoformat()

        return investigation_results

    async def _handle_agents_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """利用可能エージェント一覧"""
        return {
            'available_agents': self.available_agents,
            'total_count': len(self.available_agents)
        }

    async def _handle_agents_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """エージェント呼び出し"""
        agent_name = params.get('agent', '')
        query = params.get('query', '')

        if agent_name not in self.available_agents:
            return {
                'status': 'error',
                'message': f'Unknown agent: {agent_name}',
                'available_agents': list(self.available_agents.keys())
            }

        result = await self._simulate_agent_call(agent_name, query)

        return {
            'status': 'success',
            'agent': agent_name,
            'query': query,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }

    async def _handle_session_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セッション情報"""
        return {
            'session_id': self.session_id,
            'start_time': self.session_id.split('_')[-1],
            'database_status': 'connected',
            'knowledge_manager_status': 'active',
            'available_methods': list(self.handlers.keys())
        }

    async def _handle_session_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セッション履歴"""
        limit = params.get('limit', 10)

        history = self.db.get_data(
            'llm_history',
            f"session_id = '{self.session_id}'",
            limit=limit
        )

        return {
            'session_id': self.session_id,
            'history_count': len(history),
            'history': history
        }

    async def _handle_database_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """データベース統計"""
        tables = self.db.get_all_tables()
        stats = {}

        for table in tables:
            try:
                count = len(self.db.get_data(table, limit=10000))  # 概算
                stats[table] = count
            except:
                stats[table] = 'N/A'

        return {
            'total_tables': len(tables),
            'table_stats': stats,
            'database_path': str(self.db.db_path)
        }

    async def _handle_database_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """データベースクエリ実行（安全性チェック付き）"""
        query = params.get('query', '')

        # 安全性チェック
        if not self._is_safe_query(query):
            return {
                'status': 'error',
                'message': 'Unsafe query detected',
                'query': query
            }

        try:
            results = self.db.execute_sql(query)
            return {
                'status': 'success',
                'query': query,
                'results_count': len(results) if results else 0,
                'results': results[:100] if results else []  # 最大100件
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'query': query
            }

    async def _log_llm_interaction(self, request_type: str, prompt_text: str,
                                 response_text: str = '', status_code: int = 200,
                                 success: bool = True, error_message: str = '',
                                 metadata: Dict[str, Any] = None):
        """LLM履歴ログ記録"""
        try:
            llm_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'session_id': self.session_id,
                'provider': 'neurohub_mcp',
                'model': 'enhanced_mcp_v1',
                'request_type': request_type,
                'prompt_text': prompt_text,
                'response_text': response_text,
                'status_code': status_code,
                'success': success,
                'error_message': error_message,
                'response_time_ms': 100,  # 固定値（実際は計測）
                'token_count_input': len(prompt_text.split()),
                'token_count_output': len(response_text.split()),
                'token_count_total': len(prompt_text.split()) + len(response_text.split()),
                'metadata': json.dumps(metadata or {}, ensure_ascii=False)
            }

            self.db.insert_data('llm_history', llm_data)
        except Exception as e:
            logger.warning(f"Failed to log LLM interaction: {e}")

    async def _get_related_suggestions(self, query: str) -> List[str]:
        """関連する提案を生成"""
        suggestions = []

        # ナレッジベースから関連キーワード抽出
        knowledge = self.km.search_knowledge(query, limit=3)
        for k in knowledge:
            tags = k.get('tags', '').split(',')
            suggestions.extend([tag.strip() for tag in tags if tag.strip() and tag.strip() != query])

        return list(set(suggestions))[:5]  # ユニークな提案を最大5個

    async def _determine_relevant_agents(self, query: str) -> List[str]:
        """クエリに関連するエージェントを判定"""
        query_lower = query.lower()
        relevant = []

        # キーワードベースの簡易判定
        if any(word in query_lower for word in ['git', 'commit', 'リポジトリ', 'コミット']):
            relevant.append('git')

        if any(word in query_lower for word in ['web', 'サイト', '検索', 'ウェブ']):
            relevant.append('web')

        if any(word in query_lower for word in ['weather', '天気', '気温', '天候']):
            relevant.append('weather')

        if any(word in query_lower for word in ['command', 'コマンド', '実行', 'システム']):
            relevant.append('command')

        # 常にknowledgeエージェントを含める
        if 'knowledge' not in relevant:
            relevant.append('knowledge')

        return relevant

    async def _simulate_agent_call(self, agent_name: str, query: str) -> Dict[str, Any]:
        """エージェント呼び出しのシミュレーション"""
        # 実際の実装では各エージェントの実際のAPIを呼び出す
        simulations = {
            'git': {
                'status': 'success',
                'message': f'Git操作に関する情報: {query}',
                'data': {'commits': 3, 'branches': 2, 'status': 'clean'}
            },
            'web': {
                'status': 'success',
                'message': f'Web検索結果: {query}',
                'data': {'results_count': 5, 'top_result': f'{query}に関する情報'}
            },
            'weather': {
                'status': 'success',
                'message': f'天気情報: {query}',
                'data': {'temperature': '25°C', 'condition': '晴れ', 'humidity': '60%'}
            },
            'command': {
                'status': 'success',
                'message': f'コマンド実行結果: {query}',
                'data': {'exit_code': 0, 'output': 'Command executed successfully'}
            },
            'knowledge': {
                'status': 'success',
                'message': f'ナレッジベース検索: {query}',
                'data': {'knowledge_count': len(self.km.search_knowledge(query, limit=5))}
            },
            'llm': {
                'status': 'success',
                'message': f'LLM推論結果: {query}',
                'data': {'confidence': 0.85, 'reasoning': f'{query}について分析しました'}
            }
        }

        return simulations.get(agent_name, {
            'status': 'error',
            'message': f'Unknown agent: {agent_name}'
        })

    async def _generate_recommendations(self, query: str, knowledge_results: List[Dict],
                                      findings: List[Dict]) -> List[str]:
        """推奨アクションを生成"""
        recommendations = []

        if knowledge_results:
            recommendations.append(f"既存ナレッジを参考に{query}について詳しく調べることをお勧めします")

        if findings:
            agents_used = [f['agent'] for f in findings]
            recommendations.append(f"使用したエージェント({', '.join(agents_used)})の結果を総合的に分析することをお勧めします")

        recommendations.append(f"{query}に関する新しいナレッジを作成して将来の参考にすることをお勧めします")

        return recommendations

    def _is_safe_query(self, query: str) -> bool:
        """SQLクエリの安全性チェック"""
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = query.upper()

        # 危険なキーワードが含まれている場合は拒否
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False

        # SELECT文のみ許可
        return query_upper.strip().startswith('SELECT')


# CLIインターフェース
async def main():
    """MCPサーバーのCLI実行"""
    import argparse

    parser = argparse.ArgumentParser(description="NeuroHub Enhanced MCP Server")
    parser.add_argument('--method', required=True, help='MCP method to call')
    parser.add_argument('--params', default='{}', help='JSON parameters')
    parser.add_argument('--request-id', default='cli_request', help='Request ID')

    args = parser.parse_args()

    try:
        params = json.loads(args.params)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON parameters: {args.params}")
        return 1

    server = EnhancedMCPServer()

    request_data = {
        'id': args.request_id,
        'method': args.method,
        'params': params
    }

    response = await server.process_request(request_data)

    print(json.dumps(asdict(response), ensure_ascii=False, indent=2))

    return 0

if __name__ == "__main__":
    asyncio.run(main())
