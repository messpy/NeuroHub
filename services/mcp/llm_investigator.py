#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_investigator.py

LLM自発調査エージェント
TASK_MANAGEMENT.md要件対応:
- LLMがDBを参照して各エージェントを呼び出し
- Web、Weather、Commandエージェントとの連携
- 自発的調査時の明確な通知
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
from dataclasses import dataclass

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.db.database_manager import DatabaseManager
from services.db.knowledge_manager import KnowledgeManager
from services.ai.llm_common import load_env_from_config, DebugLogger

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InvestigationResult:
    """調査結果のデータクラス"""
    query: str
    start_time: str
    end_time: str
    agents_used: List[str]
    knowledge_findings: List[Dict[str, Any]]
    agent_findings: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_score: float
    metadata: Dict[str, Any]

class LLMInvestigator:
    """
    LLM自発調査エージェント

    機能:
    - 質問に基づいた自動調査
    - データベース参照による既存知識の活用
    - 複数エージェントの協調呼び出し
    - 調査結果の統合と分析
    - 推奨アクションの生成
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.km = KnowledgeManager(self.db)
        self.debug_logger = DebugLogger()

        # 利用可能なエージェント情報
        self.agent_capabilities = {
            'git': {
                'description': 'Git操作・コミット管理・リポジトリ情報',
                'keywords': ['git', 'commit', 'repository', 'コミット', 'リポジトリ', 'ブランチ'],
                'agent_path': 'agents/git_agent.py',
                'methods': ['get_status', 'get_commits', 'create_commit']
            },
            'web': {
                'description': 'Web情報収集・検索・サイト分析',
                'keywords': ['web', 'search', 'website', 'ウェブ', '検索', 'サイト', 'ホームページ'],
                'agent_path': 'agents/web_agent.py',
                'methods': ['search_web', 'analyze_site', 'get_content']
            },
            'weather': {
                'description': '天気情報取得・気象データ分析',
                'keywords': ['weather', 'temperature', 'rain', '天気', '気温', '雨', '晴れ'],
                'agent_path': 'agents/weather_agent.py',
                'methods': ['get_current_weather', 'get_forecast', 'analyze_conditions']
            },
            'command': {
                'description': 'システムコマンド実行・ファイル操作',
                'keywords': ['command', 'file', 'system', 'コマンド', 'ファイル', 'システム', '実行'],
                'agent_path': 'agents/command_agent.py',
                'methods': ['execute_command', 'file_operations', 'system_info']
            }
        }

        logger.info("🤖 LLM自発調査エージェント初期化完了")

    async def investigate(self, query: str, max_agents: int = 3,
                         depth: str = 'normal') -> InvestigationResult:
        """
        自発的調査を実行

        Args:
            query: 調査対象の質問・テーマ
            max_agents: 使用する最大エージェント数
            depth: 調査の深度 ('shallow', 'normal', 'deep')

        Returns:
            InvestigationResult: 調査結果
        """
        start_time = datetime.now().isoformat()

        # 調査開始の明確な通知
        logger.info(f"🔍 LLM自発調査開始")
        logger.info(f"   📋 調査テーマ: {query}")
        logger.info(f"   🎯 最大エージェント数: {max_agents}")
        logger.info(f"   📊 調査深度: {depth}")

        try:
            # Phase 1: データベース既存知識検索
            knowledge_findings = await self._search_existing_knowledge(query)
            logger.info(f"   📚 既存知識発見: {len(knowledge_findings)}件")

            # Phase 2: 関連エージェント特定
            relevant_agents = await self._identify_relevant_agents(query)
            logger.info(f"   🤖 関連エージェント: {', '.join(relevant_agents[:max_agents])}")

            # Phase 3: エージェント協調呼び出し
            agent_findings = await self._coordinate_agent_calls(
                query, relevant_agents[:max_agents], depth
            )
            logger.info(f"   📊 エージェント調査完了: {len(agent_findings)}件")

            # Phase 4: 結果統合・分析
            recommendations = await self._analyze_and_recommend(
                query, knowledge_findings, agent_findings
            )

            # Phase 5: 信頼度スコア計算
            confidence_score = await self._calculate_confidence(
                knowledge_findings, agent_findings
            )

            end_time = datetime.now().isoformat()

            # 調査完了通知
            logger.info(f"✅ LLM自発調査完了")
            logger.info(f"   ⏱️ 調査時間: {end_time}")
            logger.info(f"   📈 信頼度: {confidence_score:.2f}")
            logger.info(f"   💡 推奨: {len(recommendations)}件")

            # 調査結果をLLM履歴に記録
            await self._log_investigation_result(query, knowledge_findings, agent_findings, recommendations)

            return InvestigationResult(
                query=query,
                start_time=start_time,
                end_time=end_time,
                agents_used=[finding['agent'] for finding in agent_findings],
                knowledge_findings=knowledge_findings,
                agent_findings=agent_findings,
                recommendations=recommendations,
                confidence_score=confidence_score,
                metadata={
                    'max_agents': max_agents,
                    'depth': depth,
                    'total_findings': len(knowledge_findings) + len(agent_findings)
                }
            )

        except Exception as e:
            logger.error(f"❌ 調査中にエラーが発生: {e}")
            raise

    async def _search_existing_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """既存知識の検索"""
        logger.info(f"   🔍 ナレッジベース検索中...")

        # 1. ナレッジベース検索
        knowledge_results = self.km.search_knowledge(query, limit=10)

        # 2. 関連質問検索
        related_questions = self.db.get_data(
            'related_questions',
            f"question LIKE '%{query}%' OR tags LIKE '%{query}%'",
            limit=5
        )

        # 3. 過去のLLM履歴検索
        past_investigations = self.db.get_data(
            'llm_history',
            f"prompt_text LIKE '%{query}%' AND success = 1",
            limit=3
        )

        findings = []

        # ナレッジベース結果を追加
        for knowledge in knowledge_results:
            findings.append({
                'type': 'knowledge',
                'source': 'knowledge_base',
                'title': knowledge.get('title', ''),
                'content': knowledge.get('content', '')[:200] + "...",
                'category': knowledge.get('category', ''),
                'relevance_score': 0.8,  # 簡易スコア
                'data': knowledge
            })

        # 関連質問を追加
        for question in related_questions:
            findings.append({
                'type': 'question',
                'source': 'related_questions',
                'title': question.get('question', ''),
                'content': question.get('answer', ''),
                'tags': question.get('tags', ''),
                'relevance_score': 0.7,
                'data': question
            })

        # 過去の調査を追加
        for history in past_investigations:
            findings.append({
                'type': 'history',
                'source': 'llm_history',
                'title': f"過去の調査: {history.get('provider', '')}",
                'content': history.get('response_text', '')[:200] + "...",
                'timestamp': history.get('timestamp', ''),
                'relevance_score': 0.6,
                'data': history
            })

        return findings

    async def _identify_relevant_agents(self, query: str) -> List[str]:
        """関連エージェントの特定"""
        logger.info(f"   🎯 関連エージェント特定中...")

        query_lower = query.lower()
        agent_scores = {}

        for agent_name, info in self.agent_capabilities.items():
            score = 0

            # キーワードマッチング
            for keyword in info['keywords']:
                if keyword.lower() in query_lower:
                    score += 10

            # 部分マッチング
            if any(keyword.lower() in query_lower for keyword in info['keywords']):
                score += 5

            # 説明文との関連性
            if any(word in info['description'].lower() for word in query_lower.split()):
                score += 3

            agent_scores[agent_name] = score

        # スコア順でソート
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)

        # スコアが0より大きいエージェントのみ返す
        relevant = [agent for agent, score in sorted_agents if score > 0]

        # 常に最低1つのエージェントを含める（command エージェント）
        if not relevant:
            relevant = ['command']

        return relevant

    async def _coordinate_agent_calls(self, query: str, agents: List[str],
                                    depth: str) -> List[Dict[str, Any]]:
        """エージェント協調呼び出し"""
        logger.info(f"   🤖 エージェント呼び出し開始...")

        findings = []

        for agent_name in agents:
            logger.info(f"     📞 {agent_name}エージェント呼び出し中...")

            try:
                # エージェント呼び出し（シミュレーション）
                result = await self._call_agent(agent_name, query, depth)

                findings.append({
                    'agent': agent_name,
                    'query': query,
                    'depth': depth,
                    'timestamp': datetime.now().isoformat(),
                    'status': result.get('status', 'unknown'),
                    'result': result,
                    'confidence': result.get('confidence', 0.5)
                })

                logger.info(f"     ✅ {agent_name}: {result.get('status', 'completed')}")

            except Exception as e:
                logger.warning(f"     ❌ {agent_name}エラー: {e}")
                findings.append({
                    'agent': agent_name,
                    'query': query,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': str(e),
                    'confidence': 0.0
                })

        return findings

    async def _call_agent(self, agent_name: str, query: str, depth: str) -> Dict[str, Any]:
        """実際のエージェント呼び出し（現在はシミュレーション）"""

        # 実際の実装では各エージェントの実際のAPIを呼び出す
        # ここではシミュレーションを実装

        if agent_name == 'git':
            return {
                'status': 'success',
                'message': f'Git情報取得: {query}',
                'data': {
                    'repository_status': 'clean',
                    'current_branch': 'main',
                    'commit_count': 25,
                    'recent_commits': [
                        {'hash': 'abc123', 'message': 'Database integration test'},
                        {'hash': 'def456', 'message': 'MCP enhancement'}
                    ]
                },
                'confidence': 0.9
            }

        elif agent_name == 'web':
            return {
                'status': 'success',
                'message': f'Web検索結果: {query}',
                'data': {
                    'search_results': [
                        {'title': f'{query}に関する情報', 'url': 'https://example.com', 'snippet': '詳細な説明...'},
                        {'title': f'{query}のベストプラクティス', 'url': 'https://docs.example.com', 'snippet': '実践的な方法...'}
                    ],
                    'total_results': 2
                },
                'confidence': 0.8
            }

        elif agent_name == 'weather':
            return {
                'status': 'success',
                'message': f'天気情報: {query}',
                'data': {
                    'current_weather': {
                        'temperature': '22°C',
                        'condition': '晴れ',
                        'humidity': '65%',
                        'wind_speed': '5 m/s'
                    },
                    'forecast': '明日は曇り時々雨'
                },
                'confidence': 0.95
            }

        elif agent_name == 'command':
            return {
                'status': 'success',
                'message': f'システム情報取得: {query}',
                'data': {
                    'system_info': {
                        'os': 'Windows 11',
                        'python_version': '3.11',
                        'available_memory': '8GB',
                        'disk_space': '500GB'
                    },
                    'command_execution': 'safe_command_executed'
                },
                'confidence': 0.85
            }

        else:
            return {
                'status': 'error',
                'message': f'Unknown agent: {agent_name}',
                'confidence': 0.0
            }

    async def _analyze_and_recommend(self, query: str, knowledge_findings: List[Dict],
                                   agent_findings: List[Dict]) -> List[str]:
        """結果分析と推奨生成"""
        logger.info(f"   📊 結果分析・推奨生成中...")

        recommendations = []

        # 既存知識に基づく推奨
        if knowledge_findings:
            recommendations.append(
                f"既存のナレッジベースに{len(knowledge_findings)}件の関連情報があります。"
                "これらを参考にして詳細な分析を行うことをお勧めします。"
            )

        # エージェント結果に基づく推奨
        successful_agents = [f for f in agent_findings if f.get('status') == 'success']
        if successful_agents:
            agent_names = [f['agent'] for f in successful_agents]
            recommendations.append(
                f"{', '.join(agent_names)}エージェントの調査が成功しました。"
                "これらの結果を総合的に分析することをお勧めします。"
            )

        # 信頼度に基づく推奨
        high_confidence_findings = [
            f for f in agent_findings
            if f.get('confidence', 0) > 0.8
        ]
        if high_confidence_findings:
            recommendations.append(
                f"高信頼度（>0.8）の結果が{len(high_confidence_findings)}件あります。"
                "これらの情報は特に信頼性が高いと考えられます。"
            )

        # 新規ナレッジ作成の推奨
        if not knowledge_findings:
            recommendations.append(
                f"'{query}'に関する新しいナレッジを作成して、"
                "将来の調査効率を向上させることをお勧めします。"
            )

        # フォローアップ調査の推奨
        if len(agent_findings) < 3:
            recommendations.append(
                "追加のエージェントを使用してより包括的な調査を行うことをお勧めします。"
            )

        return recommendations

    async def _calculate_confidence(self, knowledge_findings: List[Dict],
                                  agent_findings: List[Dict]) -> float:
        """信頼度スコア計算"""
        total_score = 0.0
        total_weight = 0.0

        # 既存知識の信頼度
        for finding in knowledge_findings:
            score = finding.get('relevance_score', 0.5)
            weight = 1.0
            total_score += score * weight
            total_weight += weight

        # エージェント結果の信頼度
        for finding in agent_findings:
            if finding.get('status') == 'success':
                score = finding.get('confidence', 0.5)
                weight = 2.0  # エージェント結果により高い重み
                total_score += score * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return min(total_score / total_weight, 1.0)

    async def _log_investigation_result(self, query: str, knowledge_findings: List[Dict],
                                      agent_findings: List[Dict], recommendations: List[str]):
        """調査結果のLLM履歴記録"""
        try:
            result_summary = {
                'query': query,
                'knowledge_count': len(knowledge_findings),
                'agent_count': len(agent_findings),
                'recommendations_count': len(recommendations),
                'successful_agents': [f['agent'] for f in agent_findings if f.get('status') == 'success']
            }

            llm_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'session_id': f'investigation_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'provider': 'neurohub_investigator',
                'model': 'llm_investigator_v1',
                'request_type': 'investigation',
                'prompt_text': query,
                'response_text': json.dumps(result_summary, ensure_ascii=False),
                'status_code': 200,
                'success': True,
                'response_time_ms': 1000,  # 固定値（実際は計測）
                'token_count_input': len(query.split()),
                'token_count_output': len(json.dumps(result_summary).split()),
                'token_count_total': len(query.split()) + len(json.dumps(result_summary).split()),
                'metadata': json.dumps({
                    'investigation_type': 'self_directed',
                    'agents_used': [f['agent'] for f in agent_findings],
                    'knowledge_sources': len(knowledge_findings)
                }, ensure_ascii=False)
            }

            self.db.insert_data('llm_history', llm_data)
            logger.info(f"   📝 調査結果をLLM履歴に記録しました")

        except Exception as e:
            logger.warning(f"調査結果の記録に失敗: {e}")


# CLIインターフェース
async def main():
    """調査エージェントのCLI実行"""
    import argparse

    parser = argparse.ArgumentParser(description="LLM自発調査エージェント")
    parser.add_argument('query', help='調査対象の質問・テーマ')
    parser.add_argument('--max-agents', type=int, default=3, help='使用する最大エージェント数')
    parser.add_argument('--depth', choices=['shallow', 'normal', 'deep'],
                       default='normal', help='調査の深度')
    parser.add_argument('--output', choices=['json', 'summary'], default='summary',
                       help='出力形式')

    args = parser.parse_args()

    investigator = LLMInvestigator()

    try:
        result = await investigator.investigate(
            query=args.query,
            max_agents=args.max_agents,
            depth=args.depth
        )

        if args.output == 'json':
            # JSON形式で出力
            output = {
                'query': result.query,
                'start_time': result.start_time,
                'end_time': result.end_time,
                'agents_used': result.agents_used,
                'knowledge_findings_count': len(result.knowledge_findings),
                'agent_findings_count': len(result.agent_findings),
                'recommendations': result.recommendations,
                'confidence_score': result.confidence_score,
                'metadata': result.metadata
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            # サマリー形式で出力
            print(f"\n🔍 LLM自発調査結果")
            print(f"=" * 50)
            print(f"📋 調査テーマ: {result.query}")
            print(f"⏱️ 調査時間: {result.start_time} → {result.end_time}")
            print(f"🤖 使用エージェント: {', '.join(result.agents_used)}")
            print(f"📚 既存知識発見: {len(result.knowledge_findings)}件")
            print(f"📊 エージェント調査: {len(result.agent_findings)}件")
            print(f"📈 信頼度スコア: {result.confidence_score:.2f}")
            print(f"\n💡 推奨アクション:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"  {i}. {rec}")

        return 0

    except Exception as e:
        print(f"❌ 調査中にエラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    asyncio.run(main())
