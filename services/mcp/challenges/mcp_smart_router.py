#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCPスマートルーティング - レベル3: 連携機能開発
リクエストを分析して最適なプロバイダーに自動ルーティング
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.llm_agent import LLMAgent, LLMRequest
from services.db.database_manager import DatabaseManager


@dataclass
class RouteDecision:
    """ルーティング決定"""
    selected_provider: str
    confidence: float
    reasoning: str
    alternatives: List[str]
    estimated_time: float


class MCPSmartRouter:
    """MCPスマートルーティングクラス"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.available_providers = ["gemini", "huggingface", "ollama"]
        self.provider_profiles = self._load_provider_profiles()

    def _load_provider_profiles(self) -> Dict[str, Dict]:
        """プロバイダープロファイル取得"""
        profiles = {}

        for provider in self.available_providers:
            try:
                # DBから過去の性能データ取得
                sql = """
                SELECT
                    AVG(response_time_ms) as avg_time,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
                    COUNT(*) as total_requests
                FROM llm_history
                WHERE provider = ? AND created_at >= datetime('now', '-7 days')
                """
                cursor = self.db_manager._execute_sql(sql, (provider,))
                row = cursor.fetchone()

                avg_time = row[0] if row[0] else 2.0
                success_rate = row[1] if row[1] else 0.8
                total_requests = row[2] if row[2] else 0

                profiles[provider] = {
                    "avg_execution_time": avg_time,
                    "success_rate": success_rate,
                    "total_requests": total_requests,
                    "strengths": self._get_provider_strengths(provider),
                    "weaknesses": self._get_provider_weaknesses(provider)
                }

            except Exception as e:
                print(f"⚠️ {provider}プロファイル取得エラー: {e}")
                profiles[provider] = {
                    "avg_execution_time": 3.0,
                    "success_rate": 0.7,
                    "total_requests": 0,
                    "strengths": [],
                    "weaknesses": []
                }

        return profiles

    def _get_provider_strengths(self, provider: str) -> List[str]:
        """プロバイダーの強み"""
        strengths = {
            "gemini": [
                "高速応答",
                "長文処理",
                "複雑な推論",
                "多言語対応"
            ],
            "huggingface": [
                "オープンソース",
                "カスタマイズ可能",
                "豊富なモデル"
            ],
            "ollama": [
                "ローカル実行",
                "プライバシー保護",
                "オフライン動作",
                "コスト削減"
            ]
        }
        return strengths.get(provider, [])

    def _get_provider_weaknesses(self, provider: str) -> List[str]:
        """プロバイダーの弱み"""
        weaknesses = {
            "gemini": [
                "API制限",
                "コスト"
            ],
            "huggingface": [
                "応答速度",
                "API安定性"
            ],
            "ollama": [
                "モデルサイズ",
                "推論品質（小型モデル時）"
            ]
        }
        return weaknesses.get(provider, [])

    def analyze_request(self, request: str, request_type: str = "general") -> RouteDecision:
        """
        リクエストを分析して最適なプロバイダーを選択

        Args:
            request: ユーザーリクエスト
            request_type: リクエストタイプ

        Returns:
            ルーティング決定
        """
        print(f"🔍 リクエスト分析中...")
        print(f"   タイプ: {request_type}")
        print(f"   内容: {request[:50]}...")

        # リクエスト特性分析
        characteristics = self._analyze_request_characteristics(request, request_type)

        # プロバイダースコアリング
        scores = {}
        for provider in self.available_providers:
            score = self._calculate_provider_score(provider, characteristics)
            scores[provider] = score

        # 最適プロバイダー選択
        selected = max(scores.items(), key=lambda x: x[1])
        provider = selected[0]
        confidence = selected[1]

        # 代替候補
        alternatives = sorted(
            [p for p in scores.keys() if p != provider],
            key=lambda p: scores[p],
            reverse=True
        )

        # 推定時間
        estimated_time = self.provider_profiles[provider]["avg_execution_time"]

        # ルーティング理由
        reasoning = self._generate_reasoning(provider, characteristics, scores)

        return RouteDecision(
            selected_provider=provider,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            estimated_time=estimated_time
        )

    def _analyze_request_characteristics(self, request: str, request_type: str) -> Dict[str, Any]:
        """リクエスト特性分析"""
        return {
            "length": len(request),
            "complexity": self._estimate_complexity(request),
            "type": request_type,
            "requires_speed": "緊急" in request or "速く" in request,
            "requires_quality": "正確" in request or "品質" in request,
            "is_code_generation": "コード" in request or "プログラム" in request,
            "is_data_processing": "データ" in request or "分析" in request,
            "requires_privacy": "プライバシー" in request or "秘密" in request
        }

    def _estimate_complexity(self, request: str) -> str:
        """複雑度推定"""
        if len(request) < 50:
            return "simple"
        elif len(request) < 200:
            return "medium"
        else:
            return "complex"

    def _calculate_provider_score(self, provider: str, characteristics: Dict) -> float:
        """プロバイダースコア計算"""
        profile = self.provider_profiles[provider]
        score = 0.0

        # 基本スコア（成功率）
        score += profile["success_rate"] * 40

        # 速度スコア
        if characteristics["requires_speed"]:
            speed_score = max(0, (5.0 - profile["avg_execution_time"]) / 5.0 * 20)
            score += speed_score
        else:
            score += 10  # 中立

        # 品質スコア
        if characteristics["requires_quality"]:
            if provider == "gemini":
                score += 20
            elif provider == "huggingface":
                score += 15
            else:
                score += 10

        # タスク特性マッチング
        if characteristics["is_code_generation"]:
            if provider == "gemini":
                score += 15
            elif provider == "ollama":
                score += 10

        if characteristics["requires_privacy"]:
            if provider == "ollama":
                score += 20
            else:
                score -= 10

        # 複雑度対応
        if characteristics["complexity"] == "complex":
            if provider == "gemini":
                score += 15
        elif characteristics["complexity"] == "simple":
            if provider == "ollama":
                score += 10

        # 実績スコア
        if profile["total_requests"] > 100:
            score += 5

        return min(score / 100, 1.0)  # 0-1に正規化

    def _generate_reasoning(self, provider: str, characteristics: Dict, scores: Dict) -> str:
        """ルーティング理由生成"""
        reasons = []

        profile = self.provider_profiles[provider]

        reasons.append(f"成功率: {profile['success_rate']*100:.1f}%")
        reasons.append(f"平均応答時間: {profile['avg_execution_time']:.2f}秒")

        if characteristics["requires_speed"] and provider in ["gemini", "ollama"]:
            reasons.append("高速応答が必要なため")

        if characteristics["requires_quality"] and provider == "gemini":
            reasons.append("高品質な出力が必要なため")

        if characteristics["requires_privacy"] and provider == "ollama":
            reasons.append("プライバシー保護が必要なため")

        if characteristics["is_code_generation"]:
            reasons.append("コード生成タスクに適しているため")

        return " / ".join(reasons)

    def save_routing_history(self, request: str, decision: RouteDecision):
        """ルーティング履歴保存"""
        try:
            # テーブル作成
            sql_create = """
            CREATE TABLE IF NOT EXISTS routing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request TEXT,
                selected_provider TEXT,
                confidence REAL,
                reasoning TEXT,
                estimated_time REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.db_manager._execute_sql(sql_create)

            # 履歴保存
            sql_insert = """
            INSERT INTO routing_history
            (request, selected_provider, confidence, reasoning, estimated_time)
            VALUES (?, ?, ?, ?, ?)
            """
            self.db_manager._execute_sql(
                sql_insert,
                (request[:200], decision.selected_provider, decision.confidence,
                 decision.reasoning, decision.estimated_time)
            )

        except Exception as e:
            print(f"⚠️ 履歴保存エラー: {e}")

    def print_decision(self, decision: RouteDecision):
        """ルーティング決定表示"""
        print("\n" + "=" * 60)
        print("🎯 ルーティング決定")
        print("=" * 60)
        print(f"\n✅ 選択プロバイダー: {decision.selected_provider.upper()}")
        print(f"📊 信頼度: {decision.confidence*100:.1f}%")
        print(f"⏱️  推定実行時間: {decision.estimated_time:.2f}秒")
        print(f"\n💡 選択理由:")
        print(f"   {decision.reasoning}")

        if decision.alternatives:
            print(f"\n🔄 代替候補:")
            for i, alt in enumerate(decision.alternatives, 1):
                print(f"   {i}. {alt}")

        print("\n" + "=" * 60)


def main():
    """メイン実行"""
    router = MCPSmartRouter()

    print("🚀 レベル3: MCPスマートルーティング")
    print("=" * 60)

    # テストケース
    test_cases = [
        ("簡単な計算機を作って", "code_generation"),
        ("大量のデータを分析してください。正確性が重要です", "data_processing"),
        ("緊急！速く応答してください", "general"),
        ("プライバシーを守りながらコードを生成", "code_generation")
    ]

    for i, (request, req_type) in enumerate(test_cases, 1):
        print(f"\n📝 テストケース {i}:")
        print(f"   {request}")

        decision = router.analyze_request(request, req_type)
        router.print_decision(decision)
        router.save_routing_history(request, decision)

        time.sleep(0.5)

    print("\n✅ スマートルーティングテスト完了！")


if __name__ == "__main__":
    main()
