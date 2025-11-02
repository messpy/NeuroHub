#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/mcp/spec_normalizer.py

仕様正規化モジュール - ユーザープロンプトをJSON Schemaで構造化
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path


class SpecNormalizer:
    """仕様正規化クラス - ユーザー要求をJSON構造に変換"""

    # JSON Schema定義
    SPEC_SCHEMA = {
        "type": "object",
        "required": ["project_type", "description", "features"],
        "properties": {
            "project_type": {
                "type": "string",
                "enum": ["cli", "web_app", "api", "db_app", "scraper", "automation"],
                "description": "プロジェクトタイプ"
            },
            "description": {
                "type": "string",
                "minLength": 10,
                "description": "プロジェクト説明（10文字以上）"
            },
            "features": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "必要な機能リスト"
            },
            "database": {
                "type": "boolean",
                "description": "データベース使用有無"
            },
            "api_integration": {
                "type": "array",
                "items": {"type": "string"},
                "description": "外部API連携（例: weather_api, news_api）"
            },
            "testing_level": {
                "type": "string",
                "enum": ["basic", "comprehensive"],
                "default": "basic",
                "description": "テストレベル"
            }
        }
    }

    def __init__(self):
        """初期化"""
        self.schema = self.SPEC_SCHEMA

    def normalize_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """
        ユーザープロンプトを正規化してJSON構造に変換

        Args:
            user_prompt: ユーザーの自然言語要求

        Returns:
            正規化されたJSON仕様
        """
        # 基本的なキーワード抽出
        spec = {
            "project_type": self._detect_project_type(user_prompt),
            "description": self._extract_description(user_prompt),
            "features": self._extract_features(user_prompt),
            "database": self._detect_database_need(user_prompt),
            "api_integration": self._extract_api_integrations(user_prompt),
            "testing_level": "basic"
        }

        return spec

    def _detect_project_type(self, prompt: str) -> str:
        """プロジェクトタイプ検出"""
        prompt_lower = prompt.lower()

        if any(kw in prompt_lower for kw in ["cli", "コマンドライン", "ターミナル"]):
            return "cli"
        elif any(kw in prompt_lower for kw in ["web", "ウェブ", "サイト"]):
            return "web_app"
        elif any(kw in prompt_lower for kw in ["api", "rest", "エンドポイント"]):
            return "api"
        elif any(kw in prompt_lower for kw in ["database", "db", "データベース", "sql"]):
            return "db_app"
        elif any(kw in prompt_lower for kw in ["scraper", "スクレイピング", "クロール"]):
            return "scraper"
        else:
            return "cli"  # デフォルト

    def _extract_description(self, prompt: str) -> str:
        """説明抽出"""
        # 最初の100文字を説明として使用
        return prompt[:100].strip()

    def _extract_features(self, prompt: str) -> list:
        """機能リスト抽出"""
        features = []

        # キーワードベースで機能抽出
        feature_keywords = {
            "計算": "calculator",
            "検索": "search",
            "変換": "converter",
            "保存": "storage",
            "表示": "display",
            "入力": "input_handler",
            "出力": "output_handler"
        }

        for keyword, feature in feature_keywords.items():
            if keyword in prompt:
                features.append(feature)

        if not features:
            features.append("basic_functionality")

        return features

    def _detect_database_need(self, prompt: str) -> bool:
        """データベース必要性検出"""
        db_keywords = ["database", "db", "データベース", "保存", "記録", "履歴"]
        return any(kw in prompt.lower() for kw in db_keywords)

    def _extract_api_integrations(self, prompt: str) -> list:
        """API連携抽出"""
        apis = []

        api_keywords = {
            "天気": "weather_api",
            "ニュース": "news_api",
            "翻訳": "translation_api"
        }

        for keyword, api in api_keywords.items():
            if keyword in prompt:
                apis.append(api)

        return apis

    def validate_spec(self, spec: Dict[str, Any]) -> tuple:
        """
        仕様のバリデーション

        Returns:
            (is_valid, error_message)
        """
        # 必須フィールドチェック
        for field in self.SPEC_SCHEMA["required"]:
            if field not in spec:
                return False, f"必須フィールド '{field}' が不足しています"

        # project_typeの妥当性チェック
        valid_types = self.SPEC_SCHEMA["properties"]["project_type"]["enum"]
        if spec["project_type"] not in valid_types:
            return False, f"無効なproject_type: {spec['project_type']}"

        # descriptionの長さチェック
        if len(spec["description"]) < 10:
            return False, "descriptionが短すぎます（10文字以上必要）"

        # featuresが空でないかチェック
        if not spec.get("features") or len(spec["features"]) == 0:
            return False, "少なくとも1つの機能が必要です"

        return True, ""

    def to_json(self, spec: Dict[str, Any], filepath: Optional[Path] = None) -> str:
        """
        仕様をJSON文字列に変換（オプションでファイル保存）

        Args:
            spec: 仕様辞書
            filepath: 保存先パス（Noneの場合は保存しない）

        Returns:
            JSON文字列
        """
        json_str = json.dumps(spec, ensure_ascii=False, indent=2)

        if filepath:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def from_json(self, json_str: str) -> Dict[str, Any]:
        """JSON文字列から仕様を復元"""
        return json.loads(json_str)


# 使用例とテスト
if __name__ == "__main__":
    normalizer = SpecNormalizer()

    # テストプロンプト
    test_prompts = [
        "シンプルな計算機CLIアプリを作りたい。加算、減算、乗算、除算機能が必要。",
        "天気情報を取得してデータベースに保存するアプリ",
        "Webスクレイピングツールでニュースサイトから記事を収集"
    ]

    print("=== 仕様正規化テスト ===\n")

    for i, prompt in enumerate(test_prompts, 1):
        print(f"テスト{i}: {prompt}")
        spec = normalizer.normalize_prompt(prompt)

        # バリデーション
        is_valid, error_msg = normalizer.validate_spec(spec)

        if is_valid:
            print("✅ バリデーション成功")
            print(normalizer.to_json(spec))
        else:
            print(f"❌ バリデーション失敗: {error_msg}")

        print("-" * 60 + "\n")
