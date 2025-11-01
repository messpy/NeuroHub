#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLMAgent統合テスト - 現在の実装に対応
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.llm_agent import (
    LLMAgent, LLMRequest, ProviderStatus
)
from services.llm.llm_common import LLMResponse


class TestLLMRequest:
    """LLMRequestクラスのテスト"""

    def test_llm_request_creation(self):
        """LLMRequestの作成テスト"""
        request = LLMRequest(
            prompt="Test prompt",
            system_message="Test system",
            request_type="test",
            max_tokens=100,
            temperature=0.7
        )
        assert request.prompt == "Test prompt"
        assert request.system_message == "Test system"
        assert request.request_type == "test"
        assert request.max_tokens == 100
        assert request.temperature == 0.7

    def test_llm_request_defaults(self):
        """LLMRequestのデフォルト値テスト（修正版）"""
        request = LLMRequest(prompt="Test")
        assert request.prompt == "Test"
        assert request.system_message == ""
        assert request.request_type == "general"
        assert request.max_tokens == 500  # 実際のデフォルト値に修正
        assert request.temperature == 0.3
        assert request.preferred_provider is None
        assert request.fallback_enabled is True


class TestLLMResponse:
    """LLMResponseクラスのテスト"""

    def test_llm_response_success(self):
        """成功レスポンスのテスト"""
        response = LLMResponse(
            status_code=200,
            provider="test_provider",
            model="test_model",
            content="Test response"
        )
        assert response.status_code == 200
        assert response.provider == "test_provider"
        assert response.model == "test_model"
        assert response.content == "Test response"
        assert response.is_success is True
        assert response.is_error is False

    def test_llm_response_failure(self):
        """失敗レスポンスのテスト"""
        response = LLMResponse(
            status_code=500,
            provider="test_provider",
            model="test_model",
            content="",
            error="Test error"
        )
        assert response.status_code == 500
        assert response.error == "Test error"
        assert response.is_success is False
        assert response.is_error is True


class TestProviderStatus:
    """ProviderStatusクラスのテスト"""

    def test_provider_status_available(self):
        """利用可能プロバイダーのテスト"""
        status = ProviderStatus(
            name="test_provider",
            available=True,
            configured=True
        )
        assert status.name == "test_provider"
        assert status.available is True
        assert status.configured is True

    def test_provider_status_unavailable(self):
        """利用不可プロバイダーのテスト"""
        status = ProviderStatus(
            name="test_provider",
            available=False,
            configured=False
        )
        assert status.name == "test_provider"
        assert status.available is False
        assert status.configured is False


class TestLLMAgent:
    """LLMAgentクラスのテスト"""

    @pytest.fixture
    def mock_llm_agent(self):
        """LLMAgentのモック設定"""
        with patch('agents.llm_agent.LLMHistoryManager') as mock_history:
            mock_history.return_value = Mock()
            agent = LLMAgent()
            yield agent

    def test_init(self, mock_llm_agent):
        """初期化テスト"""
        agent = mock_llm_agent
        assert agent is not None
        assert hasattr(agent, 'history_manager')

    def test_check_provider_status_success(self, mock_llm_agent):
        """プロバイダー状態チェック成功テスト"""
        agent = mock_llm_agent

        with patch.object(agent, '_test_gemini_connection', return_value=True), \
             patch.object(agent, '_is_gemini_configured', return_value=True):

            status = agent.check_provider_status("gemini")
            assert isinstance(status, dict)
            assert status['available'] is True

    def test_check_provider_status_failure(self, mock_llm_agent):
        """プロバイダー状態チェック失敗テスト"""
        agent = mock_llm_agent

        with patch.object(agent, '_test_gemini_connection', return_value=False), \
             patch.object(agent, '_is_gemini_configured', return_value=True):

            status = agent.check_provider_status("gemini")
            assert isinstance(status, dict)
            assert status['available'] is False

    def test_check_provider_status_not_configured(self, mock_llm_agent):
        """未設定プロバイダーの状態チェックテスト"""
        agent = mock_llm_agent

        with patch.object(agent, '_is_gemini_configured', return_value=False):
            status = agent.check_provider_status("gemini")
            assert isinstance(status, dict)
            assert status['configured'] is False

    def test_get_all_provider_status(self, mock_llm_agent):
        """全プロバイダー状態取得テスト"""
        agent = mock_llm_agent

        with patch.object(agent, 'check_provider_status') as mock_check:
            mock_check.return_value = {'available': True, 'configured': True}

            all_status = agent.get_all_provider_status()
            assert isinstance(all_status, dict)
            assert 'gemini' in all_status
            assert 'huggingface' in all_status
            assert 'ollama' in all_status

    def test_get_best_provider_all_available(self, mock_llm_agent):
        """全プロバイダー利用可能時の最適選択テスト"""
        agent = mock_llm_agent

        with patch.object(agent, 'get_all_provider_status') as mock_status:
            mock_status.return_value = {
                'gemini': {'available': True, 'configured': True},
                'huggingface': {'available': True, 'configured': True},
                'ollama': {'available': True, 'configured': True}
            }

            best_provider = agent.get_best_provider()
            assert best_provider in ['gemini', 'huggingface', 'ollama']

    def test_get_best_provider_fallback(self, mock_llm_agent):
        """フォールバック選択テスト"""
        agent = mock_llm_agent

        with patch.object(agent, 'get_all_provider_status') as mock_status:
            mock_status.return_value = {
                'gemini': {'available': False, 'configured': True},
                'huggingface': {'available': True, 'configured': True},
                'ollama': {'available': False, 'configured': True}
            }

            best_provider = agent.get_best_provider()
            assert best_provider == 'huggingface'

    def test_get_best_provider_none_available(self, mock_llm_agent):
        """利用可能プロバイダーなしテスト"""
        agent = mock_llm_agent

        with patch.object(agent, 'get_all_provider_status') as mock_status:
            mock_status.return_value = {
                'gemini': {'available': False, 'configured': True},
                'huggingface': {'available': False, 'configured': True},
                'ollama': {'available': False, 'configured': True}
            }

            best_provider = agent.get_best_provider()
            assert best_provider is None

    def test_generate_text_success(self, mock_llm_agent):
        """テキスト生成成功テスト"""
        agent = mock_llm_agent

        mock_response = LLMResponse(
            status_code=200,
            provider="gemini",
            model="gemini-pro",
            content="Generated text"
        )

        with patch.object(agent, 'get_best_provider', return_value='gemini'), \
             patch.object(agent, '_call_gemini', return_value=mock_response):

            request = LLMRequest(prompt="Test prompt")
            response = agent.generate_text(request)

            assert isinstance(response, LLMResponse)
            assert response.is_success
            assert response.content == "Generated text"

    def test_generate_text_no_provider(self, mock_llm_agent):
        """プロバイダー無しテキスト生成テスト"""
        agent = mock_llm_agent

        with patch.object(agent, 'get_best_provider', return_value=None):
            request = LLMRequest(prompt="Test prompt")
            response = agent.generate_text(request)

            assert isinstance(response, LLMResponse)
            assert response.is_error
            assert "No available provider" in response.error

    def test_generate_text_with_fallback(self, mock_llm_agent):
        """フォールバック付きテキスト生成テスト"""
        agent = mock_llm_agent

        mock_success_response = LLMResponse(
            status_code=200,
            provider="huggingface",
            model="test-model",
            content="Fallback response"
        )

        with patch.object(agent, 'get_best_provider', return_value='gemini'), \
             patch.object(agent, '_call_gemini', side_effect=Exception("Gemini error")), \
             patch.object(agent, '_call_huggingface', return_value=mock_success_response):

            request = LLMRequest(prompt="Test prompt", fallback_enabled=True)
            response = agent.generate_text(request)

            assert isinstance(response, LLMResponse)
            assert response.is_success
            assert response.provider == "huggingface"

    def test_simple_generate_success(self, mock_llm_agent):
        """シンプル生成成功テスト"""
        agent = mock_llm_agent

        mock_response = LLMResponse(
            status_code=200,
            provider="gemini",
            model="gemini-pro",
            content="Simple response"
        )

        with patch.object(agent, 'generate_text', return_value=mock_response):
            result = agent.simple_generate("Test prompt")
            assert result == "Simple response"

    def test_simple_generate_failure(self, mock_llm_agent):
        """シンプル生成失敗テスト"""
        agent = mock_llm_agent

        mock_response = LLMResponse(
            status_code=500,
            provider="",
            model="",
            content="",
            error="Generation failed"
        )

        with patch.object(agent, 'generate_text', return_value=mock_response):
            result = agent.simple_generate("Test prompt")
            assert result is None


class TestLLMAgentIntegration:
    """LLMAgent統合テスト"""

    @pytest.fixture
    def real_llm_agent(self):
        """実際のLLMAgentインスタンス（モック付き）"""
        with patch('agents.llm_agent.LLMHistoryManager'):
            with patch('services.llm.llm_common.load_env_from_config'):
                agent = LLMAgent()
                yield agent

    def test_full_workflow_mock(self, real_llm_agent):
        """フルワークフローテスト（モック使用）"""
        agent = real_llm_agent

        # プロバイダー状態をモック
        with patch.object(agent, 'get_all_provider_status') as mock_status:
            mock_status.return_value = {
                'gemini': {'available': True, 'configured': True},
                'huggingface': {'available': False, 'configured': False},
                'ollama': {'available': False, 'configured': False}
            }

            # 最適プロバイダー選択をテスト
            best_provider = agent.get_best_provider()
            assert best_provider == 'gemini'

            # レスポンス生成をモック
            mock_response = LLMResponse(
                status_code=200,
                provider="gemini",
                model="gemini-pro",
                content="Integration test response"
            )

            with patch.object(agent, '_call_gemini', return_value=mock_response):
                request = LLMRequest(
                    prompt="Integration test prompt",
                    max_tokens=50,
                    temperature=0.5
                )

                response = agent.generate_text(request)

                assert response.is_success
                assert response.provider == "gemini"
                assert response.content == "Integration test response"


class TestLLMAgentCLI:
    """LLMAgent CLI テスト"""

    def test_cli_status_option(self):
        """CLIステータスオプションテスト"""
        from agents.llm_agent import main

        with patch('sys.argv', ['llm_agent.py', '--status']):
            with patch('agents.llm_agent.LLMAgent') as mock_agent_class:
                mock_agent = Mock()
                mock_agent.get_all_provider_status.return_value = {
                    'gemini': {'available': True, 'configured': True}
                }
                mock_agent_class.return_value = mock_agent

                # 例外が発生しないことを確認
                try:
                    main()
                except SystemExit:
                    pass  # 正常終了

    def test_cli_test_option(self):
        """CLIテストオプションテスト"""
        from agents.llm_agent import main

        with patch('sys.argv', ['llm_agent.py', '--test']):
            with patch('agents.llm_agent.LLMAgent') as mock_agent_class:
                mock_agent = Mock()
                mock_response = LLMResponse(
                    status_code=200,
                    provider="gemini",
                    model="test",
                    content="Test response"
                )
                mock_agent.generate_text.return_value = mock_response
                mock_agent_class.return_value = mock_agent

                try:
                    main()
                except SystemExit:
                    pass

    def test_cli_provider_option(self):
        """CLIプロバイダーオプションテスト"""
        from agents.llm_agent import main

        with patch('sys.argv', ['llm_agent.py', '--provider', 'gemini']):
            with patch('agents.llm_agent.LLMAgent') as mock_agent_class:
                mock_agent = Mock()
                mock_agent.check_provider_status.return_value = {
                    'available': True, 'configured': True
                }
                mock_agent_class.return_value = mock_agent

                try:
                    main()
                except SystemExit:
                    pass

    def test_cli_combined_options(self):
        """CLI複合オプションテスト"""
        from agents.llm_agent import main

        with patch('sys.argv', ['llm_agent.py', '--status', '--test']):
            with patch('agents.llm_agent.LLMAgent') as mock_agent_class:
                mock_agent = Mock()
                mock_agent.get_all_provider_status.return_value = {}
                mock_response = LLMResponse(
                    status_code=200,
                    provider="test",
                    model="test",
                    content="Test"
                )
                mock_agent.generate_text.return_value = mock_response
                mock_agent_class.return_value = mock_agent

                try:
                    main()
                except SystemExit:
                    pass

    def test_cli_no_options(self):
        """CLIオプション無しテスト"""
        from agents.llm_agent import main

        with patch('sys.argv', ['llm_agent.py']):
            try:
                main()
            except SystemExit:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
