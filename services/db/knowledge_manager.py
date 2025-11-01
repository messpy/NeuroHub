#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Manager - ナレッジベース管理システム
LLMエージェント用の知識検索・管理・SQL実行機能を提供
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from .database_manager import DatabaseManager

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeManager:
    """ナレッジベース管理クラス"""

    def __init__(self, db_manager: DatabaseManager = None):
        """
        初期化

        Args:
            db_manager: DatabaseManagerインスタンス（Noneの場合は新規作成）
        """
        if db_manager is not None:
            self.db = db_manager
        else:
            self.db = DatabaseManager()
        logger.info("ナレッジマネージャー初期化完了")

    def close(self):
        """データベース接続を閉じる"""
        self.db.close()

    # ============================================================================
    # ナレッジベース検索・管理メソッド
    # ============================================================================

    def search_knowledge(self, query: str, category: str = None,
                        language: str = "ja", limit: int = 10) -> List[Dict[str, Any]]:
        """
        ナレッジベースの検索

        Args:
            query: 検索クエリ
            category: カテゴリフィルター
            language: 言語フィルター
            limit: 取得件数制限

        Returns:
            List[Dict]: 検索結果
        """
        try:
            # 全文検索を優先
            fts_results = self.db.search_data("knowledge_base_fts", query)

            if fts_results:
                # FTS結果をフィルタリング
                filtered_results = []
                for result in fts_results:
                    if category and result.get('category') != category:
                        continue
                    if language and result.get('language') != language:
                        continue
                    filtered_results.append(result)

                # 関連度スコアでソート（降順）
                filtered_results.sort(
                    key=lambda x: x.get('relevance_score', 0),
                    reverse=True
                )

                return filtered_results[:limit]

            # FTSで結果が無い場合、通常検索
            conditions = []
            if category:
                conditions.append(f"category = '{category}'")
            if language:
                conditions.append(f"language = '{language}'")

            condition_str = " AND ".join(conditions) if conditions else None
            results = self.db.get_data("knowledge_base", condition_str, limit=limit)

            logger.info(f"ナレッジ検索完了: {len(results)}件")
            return results

        except Exception as e:
            logger.error(f"ナレッジ検索エラー: {e}")
            return []

    def get_knowledge_by_id(self, knowledge_id: int) -> Optional[Dict[str, Any]]:
        """
        ID指定でナレッジを取得

        Args:
            knowledge_id: ナレッジID

        Returns:
            Optional[Dict]: ナレッジデータ
        """
        try:
            results = self.db.get_data("knowledge_base", f"id = {knowledge_id}")
            if results:
                # 使用回数を増加
                self.increment_usage_count(knowledge_id)
                return results[0]
            return None

        except Exception as e:
            logger.error(f"ナレッジ取得エラー (ID: {knowledge_id}): {e}")
            return None

    def add_knowledge(self, title: str, content: str, category: str = "general",
                     tags: str = "", language: str = "ja",
                     source_type: str = "manual", source_file: str = "",
                     user_id: int = 1, is_public: bool = True) -> int:
        """
        新規ナレッジ追加

        Args:
            title: タイトル
            content: 内容
            category: カテゴリ
            tags: タグ（カンマ区切り）
            language: 言語
            source_type: ソースタイプ
            source_file: ソースファイル
            user_id: ユーザーID
            is_public: 公開フラグ

        Returns:
            int: 新規作成されたナレッジID
        """
        try:
            knowledge_data = {
                'title': title,
                'content': content,
                'category': category,
                'tags': tags,
                'language': language,
                'source_type': source_type,
                'source_file': source_file,
                'relevance_score': 0.5,  # デフォルトスコア
                'usage_count': 0,
                'user_id': user_id,
                'is_public': is_public
            }

            knowledge_id = self.db.insert_data("knowledge_base", knowledge_data)
            logger.info(f"新規ナレッジ追加完了: ID {knowledge_id}")
            return knowledge_id

        except Exception as e:
            logger.error(f"ナレッジ追加エラー: {e}")
            return -1

    def update_knowledge(self, knowledge_id: int, **kwargs) -> bool:
        """
        ナレッジ更新

        Args:
            knowledge_id: ナレッジID
            **kwargs: 更新データ

        Returns:
            bool: 更新成功フラグ
        """
        try:
            if kwargs:
                kwargs['updated_at'] = datetime.now().isoformat()
                updated_rows = self.db.update_data(
                    "knowledge_base",
                    kwargs,
                    f"id = {knowledge_id}"
                )
                return updated_rows > 0
            return False

        except Exception as e:
            logger.error(f"ナレッジ更新エラー (ID: {knowledge_id}): {e}")
            return False

    def delete_knowledge(self, knowledge_id: int) -> bool:
        """
        ナレッジ削除

        Args:
            knowledge_id: ナレッジID

        Returns:
            bool: 削除成功フラグ
        """
        try:
            deleted_rows = self.db.delete_data("knowledge_base", f"id = {knowledge_id}")
            return deleted_rows > 0

        except Exception as e:
            logger.error(f"ナレッジ削除エラー (ID: {knowledge_id}): {e}")
            return False

    def increment_usage_count(self, knowledge_id: int) -> bool:
        """
        使用回数インクリメント

        Args:
            knowledge_id: ナレッジID

        Returns:
            bool: 更新成功フラグ
        """
        try:
            # 現在の使用回数を取得
            current = self.db.get_data("knowledge_base", f"id = {knowledge_id}")
            if current:
                new_count = current[0].get('usage_count', 0) + 1
                return self.update_knowledge(knowledge_id, usage_count=new_count)
            return False

        except Exception as e:
            logger.error(f"使用回数更新エラー (ID: {knowledge_id}): {e}")
            return False

    # ============================================================================
    # 関連質問管理メソッド
    # ============================================================================

    def get_related_questions(self, main_question: str = None,
                            category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        関連質問取得

        Args:
            main_question: メイン質問（部分一致）
            category: カテゴリフィルター
            limit: 取得件数制限

        Returns:
            List[Dict]: 関連質問一覧
        """
        try:
            conditions = []
            if main_question:
                conditions.append(f"main_question LIKE '%{main_question}%'")
            if category:
                conditions.append(f"category = '{category}'")

            condition_str = " AND ".join(conditions) if conditions else None

            results = self.db.get_data(
                "related_questions",
                condition_str,
                limit=limit,
                order_by="confidence_score DESC"
            )

            logger.info(f"関連質問取得完了: {len(results)}件")
            return results

        except Exception as e:
            logger.error(f"関連質問取得エラー: {e}")
            return []

    def add_related_question(self, main_question: str, related_questions: List[str],
                           category: str = "general", confidence_score: float = 0.8,
                           user_id: int = 1) -> int:
        """
        関連質問追加

        Args:
            main_question: メイン質問
            related_questions: 関連質問リスト
            category: カテゴリ
            confidence_score: 信頼度スコア
            user_id: ユーザーID

        Returns:
            int: 新規作成された関連質問ID
        """
        try:
            question_data = {
                'main_question': main_question,
                'related_questions': json.dumps(related_questions, ensure_ascii=False),
                'category': category,
                'confidence_score': confidence_score,
                'usage_count': 0,
                'user_id': user_id,
                'is_active': True
            }

            question_id = self.db.insert_data("related_questions", question_data)
            logger.info(f"新規関連質問追加完了: ID {question_id}")
            return question_id

        except Exception as e:
            logger.error(f"関連質問追加エラー: {e}")
            return -1

    # ============================================================================
    # SQL実行機能（id→textマッピング）
    # ============================================================================

    def execute_sql_by_id(self, sql_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        SQL ID指定でSQL実行

        Args:
            sql_id: SQL ID（tags内でsql_id=XXXで定義）

        Returns:
            Optional[List[Dict]]: 実行結果
        """
        try:
            # sql_idからSQL文を検索
            results = self.db.get_data("knowledge_base", f"tags LIKE '%sql_id={sql_id}%'")

            if not results:
                logger.warning(f"SQL ID '{sql_id}' が見つかりません")
                return None

            knowledge = results[0]
            sql_content = knowledge.get('content', '')

            # SQL実行（安全性チェック付き）
            if self._is_safe_sql(sql_content):
                sql_results = self.db._execute_sql(sql_content).fetchall()

                # 使用回数増加
                self.increment_usage_count(knowledge['id'])

                # 結果を辞書形式に変換
                if sql_results:
                    return [dict(row) for row in sql_results]
                return []
            else:
                logger.error(f"危険なSQL文が検出されました: {sql_id}")
                return None

        except Exception as e:
            logger.error(f"SQL実行エラー (ID: {sql_id}): {e}")
            return None

    def _is_safe_sql(self, sql: str) -> bool:
        """
        SQL文の安全性チェック

        Args:
            sql: SQL文

        Returns:
            bool: 安全性判定
        """
        # 危険なキーワードチェック
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
            'CREATE', 'TRUNCATE', 'REPLACE', 'MERGE'
        ]

        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False

        # SELECT文のみ許可
        return sql_upper.strip().startswith('SELECT')

    def get_sql_commands(self, category: str = None) -> List[Dict[str, Any]]:
        """
        利用可能なSQL指令一覧取得

        Args:
            category: カテゴリフィルター

        Returns:
            List[Dict]: SQL指令一覧
        """
        try:
            condition = "tags LIKE '%sql_id=%'"
            if category:
                condition += f" AND category = '{category}'"

            results = self.db.get_data("knowledge_base", condition)

            sql_commands = []
            for result in results:
                # tagsからsql_idを抽出
                tags = result.get('tags', '')
                sql_id = None
                for tag in tags.split(','):
                    if tag.strip().startswith('sql_id='):
                        sql_id = tag.strip().split('=')[1]
                        break

                if sql_id:
                    sql_commands.append({
                        'sql_id': sql_id,
                        'title': result.get('title'),
                        'category': result.get('category'),
                        'usage_count': result.get('usage_count', 0)
                    })

            return sql_commands

        except Exception as e:
            logger.error(f"SQL指令一覧取得エラー: {e}")
            return []

    # ============================================================================
    # 統計・分析メソッド
    # ============================================================================

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """
        ナレッジベース統計情報取得

        Returns:
            Dict: 統計情報
        """
        try:
            stats = {}

            # 総件数
            all_knowledge = self.db.get_data("knowledge_base")
            stats['total_count'] = len(all_knowledge)

            # カテゴリ別件数
            categories = {}
            languages = {}
            for kb in all_knowledge:
                cat = kb.get('category', 'unknown')
                lang = kb.get('language', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
                languages[lang] = languages.get(lang, 0) + 1

            stats['categories'] = categories
            stats['languages'] = languages

            # 使用回数上位
            sorted_knowledge = sorted(
                all_knowledge,
                key=lambda x: x.get('usage_count', 0),
                reverse=True
            )
            stats['top_used'] = sorted_knowledge[:5]

            return stats

        except Exception as e:
            logger.error(f"統計情報取得エラー: {e}")
            return {}

    def search_and_recommend(self, query: str, user_id: int = 1) -> Dict[str, Any]:
        """
        検索と推奨の組み合わせ

        Args:
            query: 検索クエリ
            user_id: ユーザーID

        Returns:
            Dict: 検索結果と推奨情報
        """
        try:
            # 基本検索
            search_results = self.search_knowledge(query)

            # 関連質問検索
            related_q = self.get_related_questions(query)

            # カテゴリ推定（最初の検索結果から）
            suggested_category = None
            if search_results:
                suggested_category = search_results[0].get('category')

            # 同カテゴリの人気ナレッジ
            popular_in_category = []
            if suggested_category:
                popular_in_category = self.db.get_data(
                    "knowledge_base",
                    f"category = '{suggested_category}'",
                    limit=3,
                    order_by="usage_count DESC"
                )

            return {
                'search_results': search_results,
                'related_questions': related_q,
                'suggested_category': suggested_category,
                'popular_in_category': popular_in_category,
                'search_query': query,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"検索・推奨エラー: {e}")
            return {
                'search_results': [],
                'related_questions': [],
                'suggested_category': None,
                'popular_in_category': [],
                'search_query': query,
                'error': str(e)
            }

# ============================================================================
# 便利関数
# ============================================================================

def create_knowledge_manager(db_path: str = None) -> KnowledgeManager:
    """ナレッジマネージャーのファクトリ関数"""
    return KnowledgeManager(db_path)

# 後方互換性のためのエイリアス
KnowledgeBaseManager = KnowledgeManager

if __name__ == "__main__":
    # テスト実行
    km = KnowledgeManager()

    try:
        print("🧪 ナレッジマネージャーテスト")

        # 検索テスト
        results = km.search_knowledge("Python")
        print(f"📚 Python検索結果: {len(results)} 件")

        # 関連質問テスト
        questions = km.get_related_questions(category="programming")
        print(f"❓ プログラミング関連質問: {len(questions)} 件")

        # 統計情報テスト
        stats = km.get_knowledge_stats()
        print(f"📊 総ナレッジ数: {stats.get('total_count', 0)} 件")

        print("✅ テスト完了")

    finally:
        km.close()
