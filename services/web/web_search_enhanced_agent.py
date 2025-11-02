#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web検索統合エージェント
弱いLLMとWeb検索システムを統合した知識拡張エージェント
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.web.web_search_investigator import WebSearchInvestigator
from services.mcp.weak_llm_support import WeakLLMSupport
from services.db.database_manager import DatabaseManager


@dataclass
class EnhancedResponse:
    """拡張レスポンスデータクラス"""
    user_query: str
    llm_response: str
    web_search_results: List[dict]
    knowledge_sources: List[str]
    confidence_score: float
    response_type: str  # 'cached', 'web_enhanced', 'hybrid'
    execution_time: float
    timestamp: str


class WebSearchEnhancedAgent:
    """Web検索拡張エージェント"""

    def __init__(self):
        self.web_investigator = WebSearchInvestigator()
        self.weak_llm = WeakLLMSupport()
        self.db_manager = DatabaseManager()

        # レスポンス品質の閾値
        self.confidence_threshold = 0.7
        self.search_trigger_keywords = [
            'とは', 'について', '意味', '定義', '方法', 'やり方', 'how to', 'what is',
            'explain', 'describe', '使い方', 'tutorial', 'example', '例'
        ]

        self._create_tables()

    def _create_tables(self):
        """拡張レスポンステーブル作成"""
        enhanced_responses_sql = """
        CREATE TABLE IF NOT EXISTS enhanced_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT NOT NULL,
            llm_response TEXT,
            web_search_results TEXT,
            knowledge_sources TEXT,
            confidence_score REAL,
            response_type TEXT,
            execution_time REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        self.db_manager._execute_sql(enhanced_responses_sql)

    async def process_query(self, user_query: str, enable_web_search: bool = True) -> EnhancedResponse:
        """クエリ処理（Web検索拡張付き）"""
        start_time = datetime.now()

        try:
            print(f"🤖 クエリ処理開始: '{user_query}'")

            # 1. まずLLMで基本回答を生成
            print("📝 基本LLM応答生成中...")
            llm_context = self.weak_llm._create_context(user_query, {})
            llm_response = await self._get_llm_response(user_query, llm_context)

            # 2. Web検索が必要かチェック
            needs_web_search = self._should_perform_web_search(user_query, llm_response)

            web_results = []
            knowledge_sources = ["llm_internal"]
            response_type = "cached"

            if enable_web_search and needs_web_search:
                print("🔍 Web検索拡張実行中...")

                # 3. Web検索実行
                search_terms = self._extract_search_terms(user_query)
                web_results = await self._perform_enhanced_search(search_terms)

                if web_results:
                    # 4. Web検索結果を統合
                    enhanced_response = await self._enhance_response_with_web_data(
                        user_query, llm_response, web_results
                    )
                    llm_response = enhanced_response
                    knowledge_sources.extend([result.get('source', 'web') for result in web_results])
                    response_type = "web_enhanced"

            # 5. 信頼度計算
            confidence = self._calculate_response_confidence(llm_response, web_results)

            # 6. レスポンス構築
            execution_time = (datetime.now() - start_time).total_seconds()

            enhanced_response = EnhancedResponse(
                user_query=user_query,
                llm_response=llm_response,
                web_search_results=web_results,
                knowledge_sources=list(set(knowledge_sources)),
                confidence_score=confidence,
                response_type=response_type,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

            # 7. データベースに保存
            self._save_enhanced_response(enhanced_response)

            print(f"✅ クエリ処理完了 (信頼度: {confidence:.2f}, タイプ: {response_type})")

            return enhanced_response

        except Exception as e:
            print(f"❌ クエリ処理エラー: {e}")

            # エラー時のフォールバック
            execution_time = (datetime.now() - start_time).total_seconds()
            return EnhancedResponse(
                user_query=user_query,
                llm_response=f"申し訳ありません。エラーが発生しました: {str(e)}",
                web_search_results=[],
                knowledge_sources=["error"],
                confidence_score=0.1,
                response_type="error",
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

    async def _get_llm_response(self, query: str, context: dict) -> str:
        """LLM応答取得（非同期）"""
        try:
            # 弱いLLM支援システムを使用
            result = self.weak_llm.generate_code(query, context)

            if result.get("success"):
                return result["generated_code"]
            else:
                # フォールバック: 基本応答
                return f"'{query}'についての情報を調査中です。より詳細な情報が必要でしたら、Web検索を実行します。"

        except Exception as e:
            return f"LLM応答生成エラー: {str(e)}"

    def _should_perform_web_search(self, query: str, llm_response: str) -> bool:
        """Web検索必要性判定"""
        # 1. キーワード判定
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in self.search_trigger_keywords):
            return True

        # 2. LLM応答の不確実性判定
        uncertainty_indicators = [
            "わからない", "不明", "確信がない", "調べる必要", "情報が不足",
            "don't know", "uncertain", "not sure", "need more information"
        ]

        response_lower = llm_response.lower()
        if any(indicator in response_lower for indicator in uncertainty_indicators):
            return True

        # 3. 短すぎる応答
        if len(llm_response) < 100:
            return True

        # 4. 技術的クエリ
        technical_keywords = [
            "python", "javascript", "api", "library", "framework", "algorithm",
            "programming", "code", "function", "method", "class"
        ]

        if any(keyword in query_lower for keyword in technical_keywords):
            return True

        return False

    def _extract_search_terms(self, query: str) -> List[str]:
        """検索用語抽出"""
        import re

        # 基本的な単語抽出
        words = re.findall(r'\b\w+\b', query)

        # ストップワード除去
        stop_words = {
            'の', 'は', 'が', 'を', 'に', 'で', 'から', 'まで', 'と', 'や',
            'について', 'とは', 'です', 'ます', 'である', 'する', 'した',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
            'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'what', 'how'
        }

        # 有効な検索語を抽出
        search_terms = []
        for word in words:
            if (len(word) > 2 and
                word.lower() not in stop_words and
                not word.isdigit()):
                search_terms.append(word)

        # メインの検索語（最初の有効な語 + 重要そうな語）
        if search_terms:
            main_term = search_terms[0]
            # 複合検索語も作成
            if len(search_terms) > 1:
                compound_term = " ".join(search_terms[:3])
                return [main_term, compound_term]
            else:
                return [main_term]

        return [query]  # フォールバック

    async def _perform_enhanced_search(self, search_terms: List[str]) -> List[dict]:
        """拡張Web検索実行"""
        all_results = []

        for term in search_terms:
            try:
                # Web検索実行
                search_result = self.web_investigator.search_term(
                    term,
                    search_type="programming" if self._is_programming_term(term) else "general",
                    max_results=3
                )

                if search_result.get("success"):
                    # 結果をフォーマット
                    formatted_result = {
                        "term": term,
                        "success": True,
                        "definition": search_result.get("definition"),
                        "search_results": search_result.get("search_results", []),
                        "source": "web_search",
                        "search_time": search_result.get("search_time", 0)
                    }

                    all_results.append(formatted_result)

            except Exception as e:
                print(f"⚠️ 検索エラー ({term}): {e}")

        return all_results

    def _is_programming_term(self, term: str) -> bool:
        """プログラミング用語判定"""
        programming_keywords = {
            'python', 'javascript', 'java', 'cpp', 'c++', 'html', 'css',
            'react', 'vue', 'angular', 'node', 'express', 'flask', 'django',
            'api', 'rest', 'graphql', 'json', 'xml', 'sql', 'nosql',
            'git', 'github', 'docker', 'kubernetes', 'aws', 'azure',
            'function', 'method', 'class', 'object', 'array', 'string',
            'algorithm', 'data structure', 'database', 'framework', 'library'
        }

        return term.lower() in programming_keywords

    async def _enhance_response_with_web_data(self, query: str, base_response: str, web_results: List[dict]) -> str:
        """Web検索結果でレスポンス拡張"""
        try:
            # Web検索結果から最も関連性の高い情報を抽出
            best_definition = None
            additional_sources = []

            for result in web_results:
                if result.get("success") and result.get("definition"):
                    definition = result["definition"]
                    if hasattr(definition, 'definition'):
                        if not best_definition or definition.confidence > best_definition.confidence:
                            best_definition = definition

                    # 追加ソース情報
                    for search_item in result.get("search_results", []):
                        if search_item.get("title") and search_item.get("url"):
                            additional_sources.append({
                                "title": search_item["title"],
                                "url": search_item["url"],
                                "snippet": search_item.get("snippet", "")
                            })

            # 拡張レスポンス構築
            enhanced = base_response

            if best_definition:
                enhanced += f"\n\n📚 **定義** ({best_definition.source}):\n"
                enhanced += f"{best_definition.definition}\n"

                if best_definition.examples:
                    enhanced += f"\n💡 **例**: {', '.join(best_definition.examples)}\n"

                if best_definition.related_terms:
                    enhanced += f"\n🔗 **関連用語**: {', '.join(best_definition.related_terms)}\n"

            # 追加ソース
            if additional_sources:
                enhanced += f"\n📖 **参考リンク**:\n"
                for i, source in enumerate(additional_sources[:3], 1):
                    enhanced += f"{i}. [{source['title']}]({source['url']})\n"
                    if source['snippet']:
                        enhanced += f"   {source['snippet'][:100]}...\n"

            return enhanced

        except Exception as e:
            print(f"❌ レスポンス拡張エラー: {e}")
            return base_response

    def _calculate_response_confidence(self, response: str, web_results: List[dict]) -> float:
        """レスポンス信頼度計算"""
        confidence = 0.5  # ベース信頼度

        # レスポンス長による調整
        if len(response) > 200:
            confidence += 0.1
        elif len(response) > 500:
            confidence += 0.2

        # Web検索結果による調整
        if web_results:
            successful_searches = sum(1 for result in web_results if result.get("success"))
            confidence += min(0.3, successful_searches * 0.1)

            # 定義品質による調整
            for result in web_results:
                if result.get("definition") and hasattr(result["definition"], 'confidence'):
                    confidence += result["definition"].confidence * 0.2

        # 確実性指標の検出
        uncertainty_indicators = [
            "わからない", "不明", "確信がない", "かもしれない",
            "don't know", "uncertain", "might be", "possibly"
        ]

        if any(indicator in response.lower() for indicator in uncertainty_indicators):
            confidence -= 0.2

        # 具体的情報の存在
        if any(keyword in response for keyword in ["例:", "参考:", "定義:", "方法:"]):
            confidence += 0.1

        return max(0.1, min(1.0, confidence))

    def _save_enhanced_response(self, response: EnhancedResponse):
        """拡張レスポンス保存"""
        try:
            insert_sql = """
            INSERT INTO enhanced_responses (
                user_query, llm_response, web_search_results,
                knowledge_sources, confidence_score, response_type, execution_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                response.user_query,
                response.llm_response,
                json.dumps(response.web_search_results, ensure_ascii=False),
                json.dumps(response.knowledge_sources, ensure_ascii=False),
                response.confidence_score,
                response.response_type,
                response.execution_time
            ))

        except Exception as e:
            print(f"❌ 拡張レスポンス保存エラー: {e}")

    def get_search_history(self, limit: int = 10) -> List[dict]:
        """検索履歴取得"""
        try:
            select_sql = """
            SELECT user_query, confidence_score, response_type, execution_time, created_at
            FROM enhanced_responses
            ORDER BY created_at DESC
            LIMIT ?
            """

            cursor = self.db_manager._execute_sql(select_sql, (limit,))

            history = []
            for row in cursor.fetchall():
                history.append({
                    "query": row[0],
                    "confidence": row[1],
                    "type": row[2],
                    "time": row[3],
                    "timestamp": row[4]
                })

            return history

        except Exception as e:
            return []

    def get_statistics(self) -> dict:
        """統計情報取得"""
        try:
            stats = {}

            # 総クエリ数
            cursor = self.db_manager._execute_sql("SELECT COUNT(*) FROM enhanced_responses")
            stats["total_queries"] = cursor.fetchone()[0]

            # 平均信頼度
            cursor = self.db_manager._execute_sql("SELECT AVG(confidence_score) FROM enhanced_responses")
            result = cursor.fetchone()[0]
            stats["average_confidence"] = result if result else 0

            # タイプ別統計
            cursor = self.db_manager._execute_sql("""
                SELECT response_type, COUNT(*)
                FROM enhanced_responses
                GROUP BY response_type
            """)
            stats["response_types"] = {row[0]: row[1] for row in cursor.fetchall()}

            # 平均実行時間
            cursor = self.db_manager._execute_sql("SELECT AVG(execution_time) FROM enhanced_responses")
            result = cursor.fetchone()[0]
            stats["average_execution_time"] = result if result else 0

            # Web検索統計
            web_stats = self.web_investigator.get_search_statistics()
            stats["web_search"] = web_stats

            return stats

        except Exception as e:
            return {"error": str(e)}


async def main():
    """テスト実行"""
    print("🔍 Web検索拡張エージェント テスト開始")
    print("=" * 60)

    # エージェント初期化
    agent = WebSearchEnhancedAgent()

    # 統計表示
    stats = agent.get_statistics()
    print(f"📊 現在の統計:")
    print(f"  💬 総クエリ数: {stats.get('total_queries', 0)}")
    print(f"  🎯 平均信頼度: {stats.get('average_confidence', 0):.2f}")
    print(f"  ⏱️ 平均実行時間: {stats.get('average_execution_time', 0):.2f}秒")
    print()

    # テストクエリ
    test_queries = [
        "Pythonとは何ですか？",
        "BeautifulSoupの使い方を教えて",
        "機械学習について説明してください",
        "Flaskでウェブアプリを作る方法",
        "JSONとは何か？"
    ]

    for query in test_queries:
        print(f"💬 クエリ: '{query}'")

        # 拡張処理実行
        response = await agent.process_query(query, enable_web_search=True)

        print(f"✅ 応答タイプ: {response.response_type}")
        print(f"🎯 信頼度: {response.confidence_score:.2f}")
        print(f"📚 情報源: {', '.join(response.knowledge_sources)}")
        print(f"⏱️ 実行時間: {response.execution_time:.2f}秒")
        print(f"💭 応答: {response.llm_response[:200]}...")

        if response.web_search_results:
            print(f"🔍 Web検索: {len(response.web_search_results)}件の結果")

        print("-" * 40)

    # 最終統計
    final_stats = agent.get_statistics()
    print(f"\n📈 最終統計:")
    print(f"  💬 総クエリ数: {final_stats.get('total_queries', 0)}")
    print(f"  🎯 平均信頼度: {final_stats.get('average_confidence', 0):.2f}")
    print(f"  📊 応答タイプ分布: {final_stats.get('response_types', {})}")

    print(f"\n💾 データベース: {agent.db_manager.db_path}")
    print("🎉 テスト完了!")


if __name__ == "__main__":
    asyncio.run(main())
