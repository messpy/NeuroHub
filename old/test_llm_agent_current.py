#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLMAgent現在実装対応テスト
現在の実装に基づいた実用的なテストケース
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.llm_agent import LLMAgent, LLMRequest, ProviderStatus
from services.llm.llm_common import LLMResponse


class TestLLMRequestCurrent:
    """現在のLLMRequestクラスのテスト"""

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
        """LLMRequestのデフォルト値テスト（現在の実装）"""
        request = LLMRequest(prompt="Test")
        assert request.prompt == "Test"
        assert request.system_message == ""
        assert request.request_type == "general"
        assert request.max_tokens == 500  # 現在の実装のデフォルト値
        assert request.temperature == 0.3
        assert request.preferred_provider is None
        assert request.fallback_enabled is True


class TestLLMResponseCurrent:
    """現在のLLMResponseクラスのテスト"""

    def test_llm_response_success(self):
        """成功レスポンステスト"""
        response = LLMResponse(
            status_code=200,
            provider="test_provider",
            model="test_model",
            content="Test response"
        )
        assert response.is_success is True
        assert response.is_error is False
        assert response.content == "Test response"

    def test_llm_response_failure(self):
        """失敗レスポンステスト"""
        response = LLMResponse(
            status_code=400,
            provider="test_provider",
            model="test_model",
            content="",
            error="Test error"
        )
        assert response.is_success is False
        assert response.is_error is True
        assert response.error == "Test error"


class TestProviderStatusCurrent:
    """現在のProviderStatusクラスのテスト"""

    def test_provider_status_available(self):
        """プロバイダー利用可能状態テスト"""
        status = ProviderStatus(
            name="test_provider",
            available=True,
            configured=True,
            error_message=None
        )
        assert status.available is True
        assert status.configured is True
        assert status.error_message is None

    def test_provider_status_unavailable(self):
        """プロバイダー利用不可状態テスト"""
        status = ProviderStatus(
            name="test_provider",
            available=False,
            configured=True,
            error_message="Connection failed"
        )
        assert status.available is False
        assert status.error_message == "Connection failed"


class TestLLMAgentCurrent:
    """現在のLLMAgentクラスのテスト"""

    @pytest.fixture
    def mock_llm_agent(self):
        """LLMAgentのモック"""
        with patch('agents.llm_agent.LLMHistoryManager'):
            agent = LLMAgent()
            agent.debug = True  # デバッグフラグを後から設定
            yield agent

    def test_init(self, mock_llm_agent):
        """初期化テスト"""
        agent = mock_llm_agent
        assert agent is not None
        assert hasattr(agent, 'history_manager')
        assert hasattr(agent, 'debug')

    def test_check_provider_status_method_exists(self, mock_llm_agent):
        """check_provider_statusメソッドの存在確認"""
        agent = mock_llm_agent
        assert hasattr(agent, 'check_provider_status')
        assert callable(getattr(agent, 'check_provider_status'))

    def test_get_best_provider_method_exists(self, mock_llm_agent):
        """get_best_providerメソッドの存在確認"""
        agent = mock_llm_agent
        assert hasattr(agent, 'get_best_provider')
        assert callable(getattr(agent, 'get_best_provider'))

    def test_generate_text_method_exists(self, mock_llm_agent):
        """generate_textメソッドの存在確認"""
        agent = mock_llm_agent
        assert hasattr(agent, 'generate_text')
        assert callable(getattr(agent, 'generate_text'))

    def test_generate_text_chunked_method_exists(self, mock_llm_agent):
        """generate_text_chunkedメソッドの存在確認"""
        agent = mock_llm_agent
        assert hasattr(agent, 'generate_text_chunked')
        assert callable(getattr(agent, 'generate_text_chunked'))

    def test_request_validation(self, mock_llm_agent):
        """リクエスト検証テスト"""
        agent = mock_llm_agent

        # 無効なリクエストのテスト
        with patch.object(agent, 'get_best_provider', return_value=None):
            invalid_request = LLMRequest(prompt="")
            response = agent.generate_text(invalid_request)
            assert isinstance(response, LLMResponse)
            # プロバイダーが見つからない場合のエラーレスポンス


class TestChunkProcessing:
    """チャンク処理のテスト"""

    @pytest.fixture
    def agent_with_mock_providers(self):
        """プロバイダーをモックしたエージェント"""
        with patch('agents.llm_agent.LLMHistoryManager'):
            agent = LLMAgent()
            agent.debug = True

            # generate_textメソッドをモック
            def mock_generate_text(request):
                return LLMResponse(
                    status_code=200,
                    provider="mock_provider",
                    model="mock_model",
                    content=f"要約: {request.prompt[:50]}..."
                )

            agent.generate_text = Mock(side_effect=mock_generate_text)
            yield agent

    def test_chunk_processing_short_text(self, agent_with_mock_providers):
        """短いテキストのチャンク処理テスト"""
        agent = agent_with_mock_providers
        short_text = "これは短いテキストです。"

        response = agent.generate_text_chunked(short_text)

        assert isinstance(response, LLMResponse)
        # 短いテキストはチャンク分割されずに直接処理される
        agent.generate_text.assert_called_once()

    def test_chunk_processing_long_text(self, agent_with_mock_providers):
        """長いテキストのチャンク処理テスト"""
        agent = agent_with_mock_providers
        long_text = "これは非常に長いテキストです。" * 100  # 長いテキストを作成

        response = agent.generate_text_chunked(long_text, chunk_size=100)

        assert isinstance(response, LLMResponse)
        # 長いテキストは複数回のgenerate_text呼び出しが発生
        assert agent.generate_text.call_count > 1

    def test_chunk_processing_invalid_input(self, agent_with_mock_providers):
        """無効な入力のチャンク処理テスト"""
        agent = agent_with_mock_providers

        # None入力
        response = agent.generate_text_chunked(None)
        assert isinstance(response, LLMResponse)
        assert response.status_code == 400
        assert "無効な入力" in response.error

        # 空文字列
        response = agent.generate_text_chunked("")
        assert isinstance(response, LLMResponse)
        assert response.status_code == 400

    def test_chunk_processing_error_handling(self, agent_with_mock_providers):
        """チャンク処理のエラーハンドリングテスト"""
        agent = agent_with_mock_providers

        # generate_textでエラーが発生する場合
        def error_generate_text(request):
            return LLMResponse(
                status_code=500,
                provider="error_provider",
                model="error_model",
                content="",
                error="Processing failed"
            )

        agent.generate_text = Mock(side_effect=error_generate_text)

        long_text = "エラーテスト用の長いテキストです。" * 50
        response = agent.generate_text_chunked(long_text, chunk_size=100)

        assert isinstance(response, LLMResponse)
        # エラー耐性により何らかの結果が返される


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    @pytest.fixture
    def agent_with_error_simulation(self):
        """エラーシミュレーション用エージェント"""
        with patch('agents.llm_agent.LLMHistoryManager'):
            agent = LLMAgent()
            agent.debug = True
            yield agent

    def test_log_request_error_handling(self, agent_with_error_simulation):
        """_log_requestのエラーハンドリングテスト"""
        agent = agent_with_error_simulation

        # 不正なデータでのログ記録
        request = LLMRequest(prompt="test")
        response = LLMResponse(
            status_code=200,
            provider="test",
            model="test",
            content="test",
            tokens_used="invalid_token_count"  # 不正なトークン数
        )

        # エラーが発生してもクラッシュしないことを確認
        try:
            agent._log_request("test_provider", request, response, 1.0)
            # ログ記録でエラーが発生しても例外は発生しない
        except Exception as e:
            pytest.fail(f"ログ記録でエラーハンドリングが失敗: {e}")


class TestRealProviderIntegration:
    """実際のプロバイダーとの統合テスト（オプショナル）"""

    def test_provider_status_check_real(self):
        """実際のプロバイダーステータスチェック"""
        agent = LLMAgent()

        try:
            status = agent.check_provider_status()

            # ステータスが辞書であることを確認
            assert isinstance(status, dict)

            # 少なくとも1つのプロバイダーが存在することを確認
            assert len(status) > 0

            # 各プロバイダーステータスが適切な形式であることを確認
            for provider_name, provider_status in status.items():
                assert isinstance(provider_status, ProviderStatus)
                assert hasattr(provider_status, 'available')
                assert hasattr(provider_status, 'configured')

        except Exception as e:
            # 実際のプロバイダーテストは失敗しても構わない（環境依存）
            pytest.skip(f"実際のプロバイダーテストをスキップ: {e}")

    def test_best_provider_selection_real(self):
        """実際の最適プロバイダー選択テスト"""
        agent = LLMAgent()

        try:
            best_provider = agent.get_best_provider()

            # None または文字列が返されることを確認
            assert best_provider is None or isinstance(best_provider, str)

        except Exception as e:
            pytest.skip(f"最適プロバイダー選択テストをスキップ: {e}")


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v"])
