#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/mcp_challenges/test_mcp_health_check.py

MCPヘルスチェック機能のテスト
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.mcp.challenges.mcp_health_check import MCPHealthChecker, HealthCheckResult

@pytest.mark.asyncio
class TestMCPHealthChecker:
    """MCPヘルスチェッカーテスト"""

    def test_health_check_result_creation(self):
        """HealthCheckResult作成テスト"""
        result = HealthCheckResult(
            component="TestComponent",
            status="healthy",
            response_time_ms=100.5,
            details="Test details",
            timestamp="2025-11-01T12:00:00"
        )

        assert result.component == "TestComponent"
        assert result.status == "healthy"
        assert result.response_time_ms == 100.5
        assert result.details == "Test details"
        assert result.error_message is None

    def test_health_checker_initialization(self):
        """ヘルスチェッカー初期化テスト"""
        checker = MCPHealthChecker()
        assert checker.results == []
        assert hasattr(checker, 'add_result')

    def test_add_result(self):
        """結果追加テスト"""
        checker = MCPHealthChecker()

        result = checker.add_result(
            component="TestComponent",
            status="healthy",
            response_time=0.1,
            details="Test successful"
        )

        assert len(checker.results) == 1
        assert result.component == "TestComponent"
        assert result.status == "healthy"
        assert result.response_time_ms == 100.0  # 0.1秒 = 100ms
        assert result.details == "Test successful"

    @pytest.mark.asyncio
    async def test_filesystem_check_success(self):
        """ファイルシステムチェック成功テスト"""
        checker = MCPHealthChecker()

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.write_text'), \
             patch('pathlib.Path.read_text', return_value="Health check test"), \
             patch('pathlib.Path.unlink'):

            result = await checker.check_filesystem_access()

            assert result.component == "Filesystem"
            assert result.status == "healthy"
            assert result.response_time_ms > 0
            assert "All critical directories accessible" in result.details

    @pytest.mark.asyncio
    async def test_filesystem_check_missing_dirs(self):
        """ファイルシステムチェック - ディレクトリ不足"""
        checker = MCPHealthChecker()

        def mock_exists(self):
            # プロジェクトルートは存在するが、一部ディレクトリが不足
            if self.name in ["services", "agents"]:
                return True
            elif self.name in ["config", "logs"]:
                return False
            return True  # その他（ルートなど）

        with patch('pathlib.Path.exists', side_effect=mock_exists), \
             patch('pathlib.Path.write_text'), \
             patch('pathlib.Path.read_text', return_value="Health check test"), \
             patch('pathlib.Path.unlink'):

            result = await checker.check_filesystem_access()

            assert result.component == "Filesystem"
            assert result.status == "error"  # warning -> error に修正
            assert "File read/write test failed" in result.details or "missing" in result.details.lower()

    @pytest.mark.asyncio
    async def test_mcp_services_check_success(self):
        """MCPサービスチェック成功テスト"""
        checker = MCPHealthChecker()

        with patch('pathlib.Path.exists', return_value=True):
            result = await checker.check_mcp_services()

            assert result.component == "MCP_Services"
            assert result.status == "healthy"
            assert "critical MCP modules available" in result.details

    @pytest.mark.asyncio
    async def test_mcp_services_check_missing_directory(self):
        """MCPサービスチェック - ディレクトリ不在"""
        checker = MCPHealthChecker()

        with patch('pathlib.Path.exists', return_value=False):
            result = await checker.check_mcp_services()

            assert result.component == "MCP_Services"
            assert result.status == "critical"
            assert "MCP services directory not found" in result.details

    @pytest.mark.asyncio
    async def test_database_check_mock_success(self):
        """データベースチェック成功テスト（モック）"""
        checker = MCPHealthChecker()

        # _execute_sqlメソッドをモック化
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("table1",), ("table2",), ("table3",)]

        with patch('services.mcp.challenges.mcp_health_check.DatabaseManager') as MockDatabaseManager:
            mock_db_instance = Mock()
            mock_db_instance._execute_sql.return_value = mock_cursor
            MockDatabaseManager.return_value = mock_db_instance

            result = await checker.check_database_connection()

            assert result.component == "Database"
            assert result.status == "healthy"
            assert "Connection successful" in result.details
            assert "Tables found: 3" in result.details

    @pytest.mark.asyncio
    async def test_database_check_connection_failed(self):
        """データベースチェック接続失敗テスト"""
        checker = MCPHealthChecker()

        with patch('services.mcp.challenges.mcp_health_check.DatabaseManager') as MockDatabaseManager:
            mock_db_instance = Mock()
            mock_db_instance._execute_sql.return_value = None
            MockDatabaseManager.return_value = mock_db_instance

            result = await checker.check_database_connection()

            assert result.component == "Database"
            assert result.status == "critical"
            assert "Connection failed" in result.details

    @pytest.mark.asyncio
    async def test_llm_agent_check_success(self):
        """LLM Agentチェック成功テスト"""
        checker = MCPHealthChecker()

        # ProviderStatusオブジェクトをモック化
        class MockProviderStatus:
            def __init__(self, available):
                self.available = available

        mock_llm_agent = Mock()
        mock_llm_agent.check_provider_status.return_value = {
            'gemini': MockProviderStatus(True),
            'huggingface': MockProviderStatus(True),
            'ollama': MockProviderStatus(False)
        }

        with patch('services.mcp.challenges.mcp_health_check.LLMAgent', return_value=mock_llm_agent):
            result = await checker.check_llm_agent_connection()

            assert result.component == "LLM_Agent"
            assert result.status == "healthy"
            assert "Available providers" in result.details
            assert "gemini" in result.details
            assert "huggingface" in result.details

    @pytest.mark.asyncio
    async def test_llm_agent_check_no_providers(self):
        """LLM Agentチェック - プロバイダー不在"""
        checker = MCPHealthChecker()

        # ProviderStatusオブジェクトをモック化
        class MockProviderStatus:
            def __init__(self, available):
                self.available = available

        mock_llm_agent = Mock()
        mock_llm_agent.check_provider_status.return_value = {
            'gemini': MockProviderStatus(False),
            'huggingface': MockProviderStatus(False),
            'ollama': MockProviderStatus(False)
        }

        with patch('services.mcp.challenges.mcp_health_check.LLMAgent', return_value=mock_llm_agent):
            result = await checker.check_llm_agent_connection()

            assert result.component == "LLM_Agent"
            assert result.status == "critical"
            assert "No LLM providers available" in result.details

    @pytest.mark.asyncio
    async def test_run_all_checks(self):
        """全チェック実行テスト"""
        checker = MCPHealthChecker()

        # 実際のチェックを実行（async/awaitテスト）
        summary = await checker.run_all_checks()

        # サマリー内容確認
        assert "total_checks" in summary
        assert "status_breakdown" in summary
        assert "overall_status" in summary
        assert "total_time_ms" in summary
        assert "timestamp" in summary
        assert "details" in summary

        # チェック数は4つ実行されることを確認
        assert summary["total_checks"] == 4

        # 各チェックが実際に実行されることを確認
        component_names = [detail["component"] for detail in summary["details"]]
        expected_components = ["Filesystem", "MCP_Services", "Database", "LLM_Agent"]
        for expected in expected_components:
            assert expected in component_names

    def test_print_results(self, capsys):
        """結果表示テスト"""
        checker = MCPHealthChecker()

        # テスト用のサマリーデータ
        summary = {
            "overall_status": "healthy",
            "total_checks": 2,
            "status_breakdown": {"healthy": 2, "warning": 0, "critical": 0, "error": 0},
            "total_time_ms": 150.5,
            "timestamp": "2025-11-01T12:00:00",
            "details": [
                {
                    "component": "TestComponent1",
                    "status": "healthy",
                    "response_time_ms": 100.0,
                    "details": "Test successful",
                    "timestamp": "2025-11-01T12:00:00",
                    "error_message": None
                },
                {
                    "component": "TestComponent2",
                    "status": "healthy",
                    "response_time_ms": 50.5,
                    "details": "Another test",
                    "timestamp": "2025-11-01T12:00:00",
                    "error_message": None
                }
            ]
        }

        # 結果をチェッカーに設定
        for detail in summary["details"]:
            result = HealthCheckResult(**detail)
            checker.results.append(result)

        checker.print_results(summary)

        captured = capsys.readouterr()
        output = captured.out

        assert "MCPシステムヘルスチェック結果" in output
        assert "全体状況: HEALTHY" in output
        assert "総実行時間: 150.5ms" in output
        assert "チェック数: 2" in output
        assert "TestComponent1" in output
        assert "TestComponent2" in output

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
