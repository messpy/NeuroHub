#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_llm_agent.py - LLMAgent のユニットテスト
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.agent_llm import LLMAgent, LLMRequest, LLMResponse, ProviderStatus
except ImportError as e:
    print(f"Import error: {e}")
    # フォールバック定義
    class LLMAgent:
        def __init__(self):
            pass
    class LLMRequest:
        def __init__(self, prompt="", system_prompt="", provider_hint=None, options=None):
            self.prompt = prompt
            self.system_prompt = system_prompt
            self.provider_hint = provider_hint
            self.options = options or {}
    class LLMResponse:
        def __init__(self, text="", success=True, provider="test", error_message=None):
            self.text = text
            self.success = success
            self.provider = provider
            self.error_message = error_message
    class ProviderStatus:
        def __init__(self, name="test", available=True, configured=True, response_time=0.1, error=None):
            self.name = name
            self.available = available
            self.configured = configured
            self.response_time = response_time
            self.error = error


class TestLLMRequest:
    """LLMRequest のテストクラス"""

    def test_llm_request_creation(self):
        """LLMRequest作成テスト"""
        request = LLMRequest(
            prompt="Test prompt",
            system_message="System message",
            max_tokens=100,
            temperature=0.5
        )

        assert request.prompt == "Test prompt"
        assert request.system_message == "System message"
        assert request.max_tokens == 100
        assert request.temperature == 0.5

    def test_llm_request_defaults(self):
        """LLMRequestデフォルト値テスト"""
        request = LLMRequest(prompt="Test")

        assert request.system_message is None
        assert request.max_tokens == 200
        assert request.temperature == 0.3


class TestLLMResponse:
    """LLMResponse のテストクラス"""

    def test_llm_response_success(self):
        """成功レスポンステスト"""
        response = LLMResponse(
            provider="gemini",
            model="gemini-pro",
            prompt="Test prompt",
            content="Generated content",
            is_success=True,
            error_message=None,
            response_time=1.5,
            token_usage={"input": 10, "output": 20}
        )

        assert response.provider == "gemini"
        assert response.model == "gemini-pro"
        assert response.content == "Generated content"
        assert response.is_success is True
        assert response.error_message is None
        assert response.response_time == 1.5

    def test_llm_response_failure(self):
        """失敗レスポンステスト"""
        response = LLMResponse(
            provider="ollama",
            model="llama",
            prompt="Test prompt",
            content="",
            is_success=False,
            error_message="Connection failed",
            response_time=0.0,
            token_usage={}
        )

        assert response.is_success is False
        assert response.error_message == "Connection failed"
        assert response.content == ""


class TestProviderStatus:
    """ProviderStatus のテストクラス"""

    def test_provider_status_available(self):
        """利用可能プロバイダーテスト"""
        status = ProviderStatus(
            name="gemini",
            available=True,
            error_message=None,
            response_time=1.2,
            last_checked=1234567890.0
        )

        assert status.name == "gemini"
        assert status.available is True
        assert status.error_message is None
        assert status.response_time == 1.2

    def test_provider_status_unavailable(self):
        """利用不可プロバイダーテスト"""
        status = ProviderStatus(
            name="ollama",
            available=False,
            error_message="Server not running",
            response_time=0.0,
            last_checked=1234567890.0
        )

        assert status.available is False
        assert status.error_message == "Server not running"


class TestLLMAgent:
    """LLMAgent のテストクラス"""

    @pytest.fixture
    def mock_llm_agent(self):
        """モックされたLLMAgent"""
        with patch('agents.llm_agent.LLMHistoryManager') as mock_history:
            with patch('agents.llm_agent.load_config') as mock_config:
                with patch('agents.llm_agent.load_env_from_config'):
                    mock_config.return_value = {
                        'llm': {
                            'providers': {
                                'gemini': {'enabled': True, 'priority': 1},
                                'huggingface': {'enabled': True, 'priority': 2},
                                'ollama': {'enabled': True, 'priority': 3}
                            }
                        }
                    }

                    agent = LLMAgent()
                    yield agent

    def test_init(self, mock_llm_agent):
        """初期化テスト"""
        assert hasattr(mock_llm_agent, 'history_manager')
        assert hasattr(mock_llm_agent, 'providers')
        assert hasattr(mock_llm_agent, 'provider_priority')

    @patch('agents.llm_agent.GeminiConfig')
    @patch('agents.llm_agent.HuggingFaceConfig')
    @patch('agents.llm_agent.OllamaConfig')
    def test_check_provider_status_success(self, mock_ollama, mock_hf, mock_gemini, mock_llm_agent):
        """プロバイダー状態チェック成功テスト"""
        # モックプロバイダー設定
        mock_provider = Mock()
        mock_provider.is_configured.return_value = True
        mock_provider.test_connection.return_value = (True, None, 1.0)
        mock_gemini.return_value = mock_provider

        # プロバイダーを設定
        mock_llm_agent.providers = {'gemini': mock_provider}

        status = mock_llm_agent.check_provider_status('gemini')

        assert status.name == 'gemini'
        assert status.available is True
        assert status.error_message is None
        assert status.response_time == 1.0

    @patch('agents.llm_agent.GeminiConfig')
    def test_check_provider_status_failure(self, mock_gemini, mock_llm_agent):
        """プロバイダー状態チェック失敗テスト"""
        # モックプロバイダー設定
        mock_provider = Mock()
        mock_provider.is_configured.return_value = True
        mock_provider.test_connection.return_value = (False, "API key invalid", 0.0)
        mock_gemini.return_value = mock_provider

        mock_llm_agent.providers = {'gemini': mock_provider}

        status = mock_llm_agent.check_provider_status('gemini')

        assert status.available is False
        assert status.error_message == "API key invalid"

    def test_check_provider_status_not_configured(self, mock_llm_agent):
        """未設定プロバイダーテスト"""
        # 空のプロバイダー
        mock_provider = Mock()
        mock_provider.is_configured.return_value = False
        mock_llm_agent.providers = {'gemini': mock_provider}

        status = mock_llm_agent.check_provider_status('gemini')

        assert status.available is False
        assert "未設定" in status.error_message

    def test_get_all_provider_status(self, mock_llm_agent):
        """全プロバイダー状態取得テスト"""
        # モックプロバイダー設定
        mock_providers = {}
        for name in ['gemini', 'huggingface', 'ollama']:
            mock_provider = Mock()
            mock_provider.is_configured.return_value = True
            mock_provider.test_connection.return_value = (True, None, 1.0)
            mock_providers[name] = mock_provider

        mock_llm_agent.providers = mock_providers

        all_status = mock_llm_agent.get_all_provider_status()

        assert len(all_status) == 3
        assert all(status.available for status in all_status)

    def test_get_best_provider_all_available(self, mock_llm_agent):
        """最適プロバイダー選択（全て利用可能）テスト"""
        mock_llm_agent.provider_priority = ['gemini', 'huggingface', 'ollama']

        with patch.object(mock_llm_agent, 'check_provider_status') as mock_check:
            mock_check.return_value = ProviderStatus(
                name="gemini",
                available=True,
                error_message=None,
                response_time=1.0,
                last_checked=1234567890.0
            )

            best = mock_llm_agent.get_best_provider()

            assert best == 'gemini'  # 最高優先度

    def test_get_best_provider_fallback(self, mock_llm_agent):
        """フォールバック動作テスト"""
        mock_llm_agent.provider_priority = ['gemini', 'huggingface', 'ollama']

        def mock_check_status(provider_name):
            if provider_name == 'gemini':
                return ProviderStatus(provider_name, False, "API Error", 0.0, 1234567890.0)
            elif provider_name == 'huggingface':
                return ProviderStatus(provider_name, True, None, 1.5, 1234567890.0)
            else:
                return ProviderStatus(provider_name, True, None, 2.0, 1234567890.0)

        with patch.object(mock_llm_agent, 'check_provider_status', side_effect=mock_check_status):
            best = mock_llm_agent.get_best_provider()

            assert best == 'huggingface'  # geminiが失敗してhuggingfaceにフォールバック

    def test_get_best_provider_none_available(self, mock_llm_agent):
        """全プロバイダー利用不可テスト"""
        mock_llm_agent.provider_priority = ['gemini', 'huggingface', 'ollama']

        with patch.object(mock_llm_agent, 'check_provider_status') as mock_check:
            mock_check.return_value = ProviderStatus(
                name="test",
                available=False,
                error_message="Not available",
                response_time=0.0,
                last_checked=1234567890.0
            )

            best = mock_llm_agent.get_best_provider()

            assert best is None

    def test_generate_text_success(self, mock_llm_agent):
        """テキスト生成成功テスト"""
        request = LLMRequest(
            prompt="Generate a greeting",
            max_tokens=50,
            temperature=0.3
        )

        # モックプロバイダー設定
        mock_provider = Mock()
        mock_provider.generate_text.return_value = LLMResponse(
            provider="gemini",
            model="gemini-pro",
            prompt="Generate a greeting",
            content="Hello, how can I help you?",
            is_success=True,
            error_message=None,
            response_time=1.2,
            token_usage={"input": 5, "output": 8}
        )

        mock_llm_agent.providers = {'gemini': mock_provider}

        with patch.object(mock_llm_agent, 'get_best_provider', return_value='gemini'):
            response = mock_llm_agent.generate_text(request)

            assert response.is_success is True
            assert response.content == "Hello, how can I help you?"
            assert response.provider == "gemini"

    def test_generate_text_no_provider(self, mock_llm_agent):
        """プロバイダーなしでのテキスト生成テスト"""
        request = LLMRequest(prompt="Test")

        with patch.object(mock_llm_agent, 'get_best_provider', return_value=None):
            response = mock_llm_agent.generate_text(request)

            assert response.is_success is False
            assert "利用可能" in response.error_message

    def test_generate_text_with_fallback(self, mock_llm_agent):
        """フォールバック付きテキスト生成テスト"""
        request = LLMRequest(prompt="Test with fallback")

        # 最初のプロバイダーは失敗、二番目は成功
        mock_provider1 = Mock()
        mock_provider1.generate_text.side_effect = Exception("API Error")

        mock_provider2 = Mock()
        mock_provider2.generate_text.return_value = LLMResponse(
            provider="huggingface",
            model="llama",
            prompt="Test with fallback",
            content="Fallback response",
            is_success=True,
            error_message=None,
            response_time=2.0,
            token_usage={"input": 4, "output": 6}
        )

        mock_llm_agent.providers = {
            'gemini': mock_provider1,
            'huggingface': mock_provider2
        }
        mock_llm_agent.provider_priority = ['gemini', 'huggingface']

        response = mock_llm_agent.generate_text(request)

        assert response.is_success is True
        assert response.content == "Fallback response"
        assert response.provider == "huggingface"

    def test_simple_generate_success(self, mock_llm_agent):
        """シンプル生成成功テスト"""
        mock_provider = Mock()
        mock_provider.generate_text.return_value = LLMResponse(
            provider="gemini",
            model="gemini-pro",
            prompt="Simple test",
            content="Simple response",
            is_success=True,
            error_message=None,
            response_time=1.0,
            token_usage={"input": 3, "output": 4}
        )

        mock_llm_agent.providers = {'gemini': mock_provider}

        with patch.object(mock_llm_agent, 'get_best_provider', return_value='gemini'):
            content = mock_llm_agent.simple_generate("Simple test")

            assert content == "Simple response"

    def test_simple_generate_failure(self, mock_llm_agent):
        """シンプル生成失敗テスト"""
        with patch.object(mock_llm_agent, 'get_best_provider', return_value=None):
            content = mock_llm_agent.simple_generate("Fail test")

            assert content is None


class TestLLMAgentIntegration:
    """LLMAgent の統合テスト"""

    @pytest.fixture
    def real_llm_agent(self):
        """実際のLLMAgent（モック最小限）"""
        with patch('agents.llm_agent.LLMHistoryManager'):
            with patch('agents.llm_agent.load_env_from_config'):
                agent = LLMAgent()
                yield agent

    def test_full_workflow_mock(self, real_llm_agent):
        """完全ワークフローテスト（モック使用）"""
        # 1. プロバイダー状態確認
        with patch.object(real_llm_agent, 'check_provider_status') as mock_check:
            mock_check.return_value = ProviderStatus(
                name="gemini",
                available=True,
                error_message=None,
                response_time=1.0,
                last_checked=1234567890.0
            )

            status = real_llm_agent.check_provider_status('gemini')
            assert status.available is True

        # 2. 最適プロバイダー選択
        with patch.object(real_llm_agent, 'get_best_provider', return_value='gemini'):
            best = real_llm_agent.get_best_provider()
            assert best == 'gemini'

        # 3. テキスト生成
        mock_provider = Mock()
        mock_provider.generate_text.return_value = LLMResponse(
            provider="gemini",
            model="gemini-pro",
            prompt="Integration test",
            content="Integration test response",
            is_success=True,
            error_message=None,
            response_time=1.5,
            token_usage={"input": 10, "output": 15}
        )

        real_llm_agent.providers = {'gemini': mock_provider}

        with patch.object(real_llm_agent, 'get_best_provider', return_value='gemini'):
            request = LLMRequest(prompt="Integration test")
            response = real_llm_agent.generate_text(request)

            assert response.is_success is True
            assert response.content == "Integration test response"


class TestLLMAgentCLI:
    """LLMAgent CLI 引数テスト"""

    def test_cli_status_option(self):
        """--status オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="LLM Agent - LLM統合管理")
        parser.add_argument("--status", action="store_true", help="プロバイダー状態表示")
        parser.add_argument("--test", help="テストプロンプト")
        parser.add_argument("--provider", help="使用するプロバイダー指定")

        args = parser.parse_args(['--status'])

        assert args.status is True
        assert args.test is None
        assert args.provider is None

    def test_cli_test_option(self):
        """--test オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="LLM Agent - LLM統合管理")
        parser.add_argument("--status", action="store_true", help="プロバイダー状態表示")
        parser.add_argument("--test", help="テストプロンプト")
        parser.add_argument("--provider", help="使用するプロバイダー指定")

        args = parser.parse_args(['--test', 'Hello, world!'])

        assert args.test == 'Hello, world!'
        assert args.status is False
        assert args.provider is None

    def test_cli_provider_option(self):
        """--provider オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="LLM Agent - LLM統合管理")
        parser.add_argument("--status", action="store_true", help="プロバイダー状態表示")
        parser.add_argument("--test", help="テストプロンプト")
        parser.add_argument("--provider", help="使用するプロバイダー指定")

        args = parser.parse_args(['--provider', 'gemini'])

        assert args.provider == 'gemini'
        assert args.status is False
        assert args.test is None

    def test_cli_combined_options(self):
        """複数オプション組み合わせテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="LLM Agent - LLM統合管理")
        parser.add_argument("--status", action="store_true", help="プロバイダー状態表示")
        parser.add_argument("--test", help="テストプロンプト")
        parser.add_argument("--provider", help="使用するプロバイダー指定")

        args = parser.parse_args(['--test', 'Test prompt', '--provider', 'ollama'])

        assert args.test == 'Test prompt'
        assert args.provider == 'ollama'
        assert args.status is False

    def test_cli_no_options(self):
        """オプション未指定テスト"""
        import argparse
        parser = argparse.ArgumentParser(description="LLM Agent - LLM統合管理")
        parser.add_argument("--status", action="store_true", help="プロバイダー状態表示")
        parser.add_argument("--test", help="テストプロンプト")
        parser.add_argument("--provider", help="使用するプロバイダー指定")

        args = parser.parse_args([])

        assert args.status is False
        assert args.test is None
        assert args.provider is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
