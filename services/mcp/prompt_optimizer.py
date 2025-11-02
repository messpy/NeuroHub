#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プロンプト最適化システム
過去の成功例から学習して最適なプロンプトを生成
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.db.database_manager import DatabaseManager
from services.web.practical_web_searcher import PracticalWebSearcher


@dataclass
class OptimizedPrompt:
    """最適化されたプロンプト"""
    prompt: str
    confidence: float
    based_on: List[str]  # 参考にした成功例
    enhancements: List[str]  # 追加した強化要素


class PromptOptimizer:
    """プロンプト最適化クラス"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.web_searcher = PracticalWebSearcher()
        self._create_tables()

    def _create_tables(self):
        """最適化用テーブル作成"""
        sql = """
        CREATE TABLE IF NOT EXISTS prompt_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_prompt TEXT,
            optimized_prompt TEXT,
            task_type TEXT,
            success BOOLEAN,
            execution_time REAL,
            error_count INTEGER,
            provider TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db_manager._execute_sql(sql)

    def optimize_prompt(self, user_request: str, task_type: str = "general") -> OptimizedPrompt:
        """
        ユーザーリクエストから最適化されたプロンプトを生成

        Args:
            user_request: ユーザーの要求
            task_type: タスクタイプ（'calculator', 'database', 'file_operation'等）

        Returns:
            最適化されたプロンプト
        """
        print(f"🎯 プロンプト最適化開始: {user_request}")

        # 1. タスクタイプを自動判定
        detected_type = self._detect_task_type(user_request)
        task_type = detected_type if detected_type else task_type

        # 2. 過去の成功例を検索
        successful_examples = self._search_successful_prompts(task_type)

        # 3. Web検索で最新のベストプラクティス取得
        web_tips = self._search_best_practices(user_request, task_type)

        # 4. プロンプトを構築
        optimized = self._build_optimized_prompt(
            user_request,
            task_type,
            successful_examples,
            web_tips
        )

        return optimized

    def _detect_task_type(self, user_request: str) -> Optional[str]:
        """タスクタイプを自動判定"""
        keywords = {
            'calculator': ['計算', '足し算', '引き算', '掛け算', '割り算', '四則演算'],
            'database': ['データベース', 'SQL', 'sqlite', 'レコード', 'CRUD'],
            'file_operation': ['ファイル', 'フォルダ', '整理', 'コピー', '移動'],
            'web_scraping': ['スクレイピング', 'クロール', 'Web', 'HTML'],
            'data_conversion': ['変換', 'JSON', 'CSV', 'XML', 'コンバータ'],
            'cli_tool': ['コマンドライン', 'CLI', 'ツール']
        }

        for task, words in keywords.items():
            if any(word in user_request for word in words):
                return task

        return 'general'

    def _search_successful_prompts(self, task_type: str, limit: int = 5) -> List[Dict]:
        """過去の成功プロンプトを検索"""
        try:
            sql = """
            SELECT original_prompt, optimized_prompt, execution_time
            FROM prompt_performance
            WHERE task_type = ? AND success = 1
            ORDER BY execution_time ASC
            LIMIT ?
            """
            cursor = self.db_manager._execute_sql(sql, (task_type, limit))
            results = cursor.fetchall()

            examples = []
            for row in results:
                examples.append({
                    'original': row[0],
                    'optimized': row[1],
                    'time': row[2]
                })

            return examples

        except Exception as e:
            print(f"DB検索エラー: {e}")
            return []

    def _search_best_practices(self, user_request: str, task_type: str) -> List[str]:
        """Web検索でベストプラクティス取得（既存の検索機能を活用）"""
        try:
            query = f"Python {task_type} best practices implementation"

            # 既存の_search_web_simpleメソッドを活用
            results = self.web_searcher._search_web_simple(query, max_results=3)

            tips = []
            for result in results:
                if result.snippet:
                    tips.append(result.snippet)

            return tips

        except Exception as e:
            print(f"Web検索エラー: {e}")
            return []

    def _build_optimized_prompt(self, user_request: str, task_type: str,
                                successful_examples: List[Dict],
                                web_tips: List[str]) -> OptimizedPrompt:
        """最適化されたプロンプトを構築"""

        # 基本プロンプト
        base_prompt = f"""
以下の仕様に基づいて、完全に動作するPythonプログラムを生成してください。

【タスクタイプ】
{task_type}

【ユーザー要求】
{user_request}

【実装要件】
"""

        # タスクタイプ別の強化要素
        enhancements = self._get_task_enhancements(task_type)

        for enhancement in enhancements:
            base_prompt += f"- {enhancement}\n"

        # 成功例からの学習
        if successful_examples:
            base_prompt += "\n【成功パターン参考】\n"
            for i, example in enumerate(successful_examples[:2], 1):
                base_prompt += f"{i}. 類似タスク成功例あり\n"

        # ベストプラクティス
        if web_tips:
            base_prompt += "\n【推奨事項】\n"
            for tip in web_tips[:2]:
                if tip:
                    base_prompt += f"- {tip[:100]}...\n"

        # 品質要件
        base_prompt += """
【品質要件】
- エラーハンドリングを必ず実装
- ユーザーフレンドリーなメッセージ
- --help でヘルプ表示
- ログ出力機能
- 実際に動作する具体的なコード
- TODOコメントは残さない
- テスト可能な実装

【出力形式】
完全なPythonコード（#!/usr/bin/env python3から始まる）のみを出力してください。
"""

        # 信頼度計算
        confidence = 0.5
        if successful_examples:
            confidence += 0.2
        if web_tips:
            confidence += 0.2
        if task_type != 'general':
            confidence += 0.1

        based_on = []
        if successful_examples:
            based_on.append(f"{len(successful_examples)}件の成功例")
        if web_tips:
            based_on.append(f"{len(web_tips)}件のベストプラクティス")

        return OptimizedPrompt(
            prompt=base_prompt,
            confidence=min(confidence, 1.0),
            based_on=based_on,
            enhancements=enhancements
        )

    def _get_task_enhancements(self, task_type: str) -> List[str]:
        """タスクタイプ別の強化要素"""
        enhancements = {
            'calculator': [
                "eval()を使用した式評価",
                "四則演算（+, -, *, /）対応",
                "括弧による計算順序制御",
                "ゼロ除算エラー検出",
                "無効な文字のチェック"
            ],
            'database': [
                "sqlite3を使用",
                "CREATE TABLE文の実装",
                "INSERT/SELECT/UPDATE/DELETE操作",
                "トランザクション管理",
                "エラーロールバック"
            ],
            'file_operation': [
                "pathlibを使用",
                "ファイル存在チェック",
                "安全なファイル操作",
                "バックアップ機能",
                "進捗表示"
            ],
            'data_conversion': [
                "json/csvモジュール使用",
                "エンコーディング指定（utf-8）",
                "データ検証",
                "型変換処理",
                "エラーリカバリー"
            ],
            'general': [
                "標準ライブラリのみ使用",
                "argparseでCLI実装",
                "loggingモジュール使用",
                "適切な例外処理"
            ]
        }

        return enhancements.get(task_type, enhancements['general'])

    def save_performance(self, original_prompt: str, optimized_prompt: str,
                        task_type: str, success: bool, execution_time: float,
                        error_count: int, provider: str):
        """プロンプトの性能を記録"""
        try:
            sql = """
            INSERT INTO prompt_performance
            (original_prompt, optimized_prompt, task_type, success,
             execution_time, error_count, provider)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.db_manager._execute_sql(
                sql,
                (original_prompt, optimized_prompt, task_type, success,
                 execution_time, error_count, provider)
            )
            print(f"📊 性能記録保存: {task_type}")
        except Exception as e:
            print(f"性能記録エラー: {e}")


def main():
    """テスト実行"""
    optimizer = PromptOptimizer()

    # テストケース
    test_requests = [
        "足し算と引き算ができる計算機",
        "SQLiteにデータを保存するツール",
        "JSONをCSVに変換するプログラム"
    ]

    for request in test_requests:
        print(f"\n{'='*60}")
        result = optimizer.optimize_prompt(request)
        print(f"✅ 最適化完了")
        print(f"信頼度: {result.confidence:.2f}")
        print(f"参考: {', '.join(result.based_on)}")
        print(f"強化要素: {len(result.enhancements)}件")
        print(f"\nプロンプト:\n{result.prompt[:200]}...")


if __name__ == "__main__":
    main()
