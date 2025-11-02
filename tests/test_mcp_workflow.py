#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_mcp_workflow.py

MCP統合テスト - README記載のフロー全体をテスト
"""

import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.mcp.spec_normalizer import SpecNormalizer
from services.mcp.command_validator import CommandValidator
from services.mcp.project_designer import ProjectDesigner


class TestMCPWorkflow:
    """MCP統合ワークフローテスト"""

    def setup_method(self):
        """各テストの前処理"""
        self.normalizer = SpecNormalizer()
        self.validator = CommandValidator()
        self.designer = ProjectDesigner()

    def test_full_workflow_cli_app(self):
        """完全なワークフローテスト: CLIアプリ"""
        # ステップ1: 仕様正規化
        user_prompt = "シンプルなTODOリストCLIアプリ。追加、削除、一覧表示機能が必要。"
        spec = self.normalizer.normalize_prompt(user_prompt)

        # バリデーション
        is_valid, error_msg = self.normalizer.validate_spec(spec)
        assert is_valid, f"仕様バリデーション失敗: {error_msg}"
        assert spec["project_type"] == "cli"
        assert len(spec["features"]) > 0

        # ステップ2: プロジェクト設計
        plan = self.designer.create_plan(spec)

        assert "metadata" in plan
        assert "structure" in plan
        assert "dependencies" in plan
        assert "tasks" in plan
        assert "validation_steps" in plan

        # 静的検証ステップの確認
        assert "ruff check ." in plan["validation_steps"]
        assert "mypy ." in plan["validation_steps"]
        assert "bandit -r ." in plan["validation_steps"]
        assert "pytest tests/" in plan["validation_steps"]

        print("\n✅ ステップ1: 仕様正規化 完了")
        print(f"   プロジェクトタイプ: {spec['project_type']}")
        print(f"   機能数: {len(spec['features'])}")

        print("\n✅ ステップ2: プロジェクト設計 完了")
        print(f"   ファイル数: {len(plan['structure'])}")
        print(f"   依存関係数: {len(plan['dependencies'])}")
        print(f"   タスク数: {len(plan['tasks'])}")

    def test_command_validation_in_workflow(self):
        """ワークフロー内でのコマンド検証"""
        # 安全なコマンド
        safe_cmd = "pytest tests/"
        is_safe, _ = self.validator.validate_command(safe_cmd)
        assert is_safe, "安全なコマンドが誤検出されました"

        # 危険なコマンド
        dangerous_cmd = "rm -rf /"
        is_safe, violation = self.validator.validate_command(dangerous_cmd)
        assert not is_safe, "危険なコマンドが検出されませんでした"
        assert violation is not None
        assert "alternatives" in violation
        assert len(violation["alternatives"]) > 0

        print("\n✅ コマンド検証テスト完了")
        print(f"   危険なコマンド検出: {violation['command']}")
        print(f"   代替案数: {len(violation['alternatives'])}")

    def test_workflow_with_database(self):
        """データベース使用ワークフローテスト"""
        # ステップ1: 仕様正規化（DB使用）
        user_prompt = "ユーザー管理システム。データベースに保存、検索、更新機能が必要。"
        spec = self.normalizer.normalize_prompt(user_prompt)

        # データベース使用検出
        assert spec["database"] == True, "データベース使用が検出されませんでした"

        # ステップ2: プロジェクト設計
        plan = self.designer.create_plan(spec)

        # データベース関連の構造確認
        assert "models/database.py" in plan["structure"]
        assert "sqlalchemy" in plan["dependencies"]
        assert "alembic" in plan["dependencies"]

        print("\n✅ データベースワークフローテスト完了")
        print(f"   データベース使用: {spec['database']}")
        print(f"   DB関連依存関係: sqlalchemy, alembic")

    def test_workflow_with_api_integration(self):
        """API連携ワークフローテスト"""
        # ステップ1: 仕様正規化（API連携）
        user_prompt = "天気予報アプリ。天気APIから情報取得して表示。"
        spec = self.normalizer.normalize_prompt(user_prompt)

        # API連携検出
        assert len(spec["api_integration"]) > 0, "API連携が検出されませんでした"
        assert "weather_api" in spec["api_integration"]

        # ステップ2: プロジェクト設計
        plan = self.designer.create_plan(spec)

        # API関連の構造確認
        assert "requests" in plan["dependencies"]
        assert any("weather_api" in item for item in plan["structure"])

        print("\n✅ API連携ワークフローテスト完了")
        print(f"   API連携: {spec['api_integration']}")

    def test_code_snippet_validation(self):
        """コードスニペット検証テスト"""
        # 危険なコードスニペット
        dangerous_code = '''
import subprocess
subprocess.run("rm -rf /tmp", shell=True)
subprocess.run("chmod 777 /var", shell=True)
'''

        violations = self.validator.validate_code_snippet(dangerous_code)

        assert len(violations) > 0, "危険なコードが検出されませんでした"

        for violation in violations:
            assert "command" in violation
            assert "reason" in violation
            assert "alternatives" in violation

        print("\n✅ コードスニペット検証テスト完了")
        print(f"   検出された違反数: {len(violations)}")

    def test_json_schema_validation(self):
        """JSON Schema検証テスト（弱いLLM対応）"""
        # 正しい仕様
        valid_spec = {
            "project_type": "cli",
            "description": "テストアプリケーション説明文です",
            "features": ["feature1", "feature2"],
            "database": False,
            "api_integration": [],
            "testing_level": "basic"
        }

        is_valid, error_msg = self.normalizer.validate_spec(valid_spec)
        assert is_valid, f"正しい仕様が検証失敗: {error_msg}"

        # 不正な仕様（descriptionが短すぎる）
        invalid_spec = {
            "project_type": "cli",
            "description": "短い",
            "features": ["feature1"]
        }

        is_valid, error_msg = self.normalizer.validate_spec(invalid_spec)
        assert not is_valid, "不正な仕様が検証成功してしまいました"
        assert "短すぎます" in error_msg

        print("\n✅ JSON Schema検証テスト完了")


# pytest実行時のメイン関数
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
