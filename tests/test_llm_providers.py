#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_llm_providers.py - LLMプロバイダーのユニットテスト
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from services.llm.provider_gemini import GeminiConfig
    from services.llm.provider_huggingface import HuggingFaceConfig
    from services.llm.provider_ollama import OllamaConfig
    from services.llm.llm_common import LLMResponse, create_llm_response
except ImportError as e:
    print(f"Import error: {e}")
    # フォールバック定義
    class GeminiConfig:
        def __init__(self):
            pass

    class HuggingFaceConfig:
        def __init__(self):
            pass

    class OllamaConfig:
        def __init__(self):
            pass

    class LLMResponse:
        def __init__(self, text="", success=True, provider="test", error_message=None):
            self.text = text
            self.success = success
            self.provider = provider
            self.error_message = error_message

    def create_llm_response(text="", success=True, provider="test", error_message=None):
        return LLMResponse(text=text, success=success, provider=provider, error_message=error_message)


class TestGeminiProvider:
    """Gemini プロバイダーのテストクラス"""

    @pytest.fixture
    def mock_gemini_config(self):
        """モックされたGeminiConfig"""
        with patch('services.llm.provider_gemini.load_config') as mock_config:
            with patch('services.llm.provider_gemini.load_env_from_config'):
                mock_config.return_value = {
                    'llm': {
                        'providers': {
                            'gemini': {
                                'model': 'gemini-pro',
                                'max_tokens': 200,
                                'temperature': 0.3
                            }
                        }
                    }
                }

                with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
                    config = GeminiConfig()
                    yield config

    def test_init(self, mock_gemini_config):
        """初期化テスト"""
        assert hasattr(mock_gemini_config, 'api_key')
        assert hasattr(mock_gemini_config, 'model')
        assert hasattr(mock_gemini_config, 'api_url')

    def test_is_configured_with_key(self, mock_gemini_config):
        """API key設定済みテスト"""
        mock_gemini_config.api_key = 'test_key'
        assert mock_gemini_config.is_configured() is True

    def test_is_configured_without_key(self, mock_gemini_config):
        """API key未設定テスト"""
        mock_gemini_config.api_key = None
        assert mock_gemini_config.is_configured() is False

    @patch('services.llm.provider_gemini.make_api_request')
    def test_test_connection_success(self, mock_request, mock_gemini_config):
        """接続テスト成功"""
        mock_request.return_value = (200, {'candidates': [{'content': {'parts': [{'text': 'test'}]}}]})

        success, message, response_time = mock_gemini_config.test_connection()

        assert success is True
        assert message is None
        assert isinstance(response_time, float)

    @patch('services.llm.provider_gemini.make_api_request')
    def test_test_connection_failure(self, mock_request, mock_gemini_config):
        """接続テスト失敗"""
        mock_request.return_value = (401, {'error': {'message': 'Invalid API key'}})

        success, message, response_time = mock_gemini_config.test_connection()

        assert success is False
        assert 'Invalid API key' in message

    @patch('services.llm.provider_gemini.make_api_request')
    def test_generate_text_success(self, mock_request, mock_gemini_config):
        """テキスト生成成功テスト"""
        mock_request.return_value = (200, {
            'candidates': [{
                'content': {'parts': [{'text': 'Generated response'}]},
                'finishReason': 'STOP'
            }],
            'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 5}
        })

        response = mock_gemini_config.generate_text(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.3
        )

        assert isinstance(response, LLMResponse)
        assert response.is_success is True
        assert response.content == 'Generated response'
        assert response.provider == 'gemini'

    @patch('services.llm.provider_gemini.make_api_request')
    def test_generate_text_api_error(self, mock_request, mock_gemini_config):
        """API エラーテスト"""
        mock_request.return_value = (400, {'error': {'message': 'Bad request'}})

        response = mock_gemini_config.generate_text(prompt="Test")

        assert response.is_success is False
        assert 'Bad request' in response.error_message


class TestHuggingFaceProvider:
    """HuggingFace プロバイダーのテストクラス"""

    @pytest.fixture
    def mock_hf_config(self):
        """モックされたHuggingFaceConfig"""
        with patch('services.llm.provider_huggingface.load_config') as mock_config:
            with patch('services.llm.provider_huggingface.load_env_from_config'):
                mock_config.return_value = {
                    'llm': {
                        'providers': {
                            'huggingface': {
                                'model': 'meta-llama/Llama-3.2-3B-Instruct',
                                'max_tokens': 200,
                                'temperature': 0.3
                            }
                        }
                    }
                }

                with patch.dict(os.environ, {'HF_TOKEN': 'test_hf_token'}):
                    config = HuggingFaceConfig()
                    yield config

    def test_init(self, mock_hf_config):
        """初期化テスト"""
        assert hasattr(mock_hf_config, 'token')
        assert hasattr(mock_hf_config, 'model')
        assert hasattr(mock_hf_config, 'api_url')

    def test_is_configured_with_token(self, mock_hf_config):
        """トークン設定済みテスト"""
        mock_hf_config.token = 'test_token'
        assert mock_hf_config.is_configured() is True

    def test_is_configured_without_token(self, mock_hf_config):
        """トークン未設定テスト"""
        mock_hf_config.token = None
        assert mock_hf_config.is_configured() is False

    @patch('services.llm.provider_huggingface.make_api_request')
    def test_test_connection_success(self, mock_request, mock_hf_config):
        """接続テスト成功"""
        mock_request.return_value = (200, {
            'choices': [{'message': {'content': 'test response'}}]
        })

        success, message, response_time = mock_hf_config.test_connection()

        assert success is True
        assert message is None
        assert isinstance(response_time, float)

    @patch('services.llm.provider_huggingface.make_api_request')
    def test_generate_text_success(self, mock_request, mock_hf_config):
        """テキスト生成成功テスト"""
        mock_request.return_value = (200, {
            'choices': [{
                'message': {'content': 'HF generated response'},
                'finish_reason': 'stop'
            }],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        })

        response = mock_hf_config.generate_text(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.3
        )

        assert response.is_success is True
        assert response.content == 'HF generated response'
        assert response.provider == 'huggingface'


class TestOllamaProvider:
    """Ollama プロバイダーのテストクラス"""

    @pytest.fixture
    def mock_ollama_config(self):
        """モックされたOllamaConfig"""
        with patch('services.llm.provider_ollama.load_config') as mock_config:
            with patch('services.llm.provider_ollama.load_env_from_config'):
                mock_config.return_value = {
                    'llm': {
                        'providers': {
                            'ollama': {
                                'model': 'qwen2.5:1.5b-instruct',
                                'host': 'http://localhost:11434'
                            }
                        }
                    }
                }

                config = OllamaConfig()
                yield config

    def test_init(self, mock_ollama_config):
        """初期化テスト"""
        assert hasattr(mock_ollama_config, 'host')
        assert hasattr(mock_ollama_config, 'model')

    def test_is_configured_always_true(self, mock_ollama_config):
        """常に設定済みとするテスト（Ollamaはローカル）"""
        assert mock_ollama_config.is_configured() is True

    @patch('services.llm.provider_ollama.make_api_request')
    def test_test_connection_success(self, mock_request, mock_ollama_config):
        """接続テスト成功"""
        # /api/tags エンドポイントの応答
        mock_request.return_value = (200, {
            'models': [{'name': 'qwen2.5:1.5b-instruct'}]
        })

        success, message, response_time = mock_ollama_config.test_connection()

        assert success is True
        assert message is None

    @patch('services.llm.provider_ollama.make_api_request')
    def test_test_connection_server_down(self, mock_request, mock_ollama_config):
        """サーバー停止時テスト"""
        mock_request.side_effect = Exception("Connection refused")

        success, message, response_time = mock_ollama_config.test_connection()

        assert success is False
        assert 'Connection refused' in message

    @patch('services.llm.provider_ollama.make_api_request')
    def test_generate_text_success(self, mock_request, mock_ollama_config):
        """テキスト生成成功テスト"""
        mock_request.return_value = (200, {
            'response': 'Ollama generated response',
            'done': True,
            'total_duration': 1500000000,
            'prompt_eval_count': 10,
            'eval_count': 5
        })

        response = mock_ollama_config.generate_text(
            prompt="Test prompt",
            temperature=0.3
        )

        assert response.is_success is True
        assert response.content == 'Ollama generated response'
        assert response.provider == 'ollama'


class TestLLMCommon:
    """LLM共通機能のテスト"""

    def test_create_llm_response_success(self):
        """成功レスポンス作成テスト"""
        response = create_llm_response(
            provider="test",
            model="test-model",
            prompt="test prompt",
            content="test content",
            is_success=True,
            response_time=1.5,
            token_usage={"input": 10, "output": 5}
        )

        assert isinstance(response, LLMResponse)
        assert response.provider == "test"
        assert response.model == "test-model"
        assert response.content == "test content"
        assert response.is_success is True
        assert response.response_time == 1.5

    def test_create_llm_response_failure(self):
        """失敗レスポンス作成テスト"""
        response = create_llm_response(
            provider="test",
            model="test-model",
            prompt="test prompt",
            content="",
            is_success=False,
            error_message="Test error",
            response_time=0.0
        )

        assert response.is_success is False
        assert response.error_message == "Test error"
        assert response.content == ""


class TestLLMProviderIntegration:
    """LLMプロバイダー統合テスト"""

    def test_provider_interface_consistency(self):
        """プロバイダーインターフェース一貫性テスト"""
        with patch('services.llm.provider_gemini.load_config'), \
             patch('services.llm.provider_gemini.load_env_from_config'), \
             patch('services.llm.provider_huggingface.load_config'), \
             patch('services.llm.provider_huggingface.load_env_from_config'), \
             patch('services.llm.provider_ollama.load_config'), \
             patch('services.llm.provider_ollama.load_env_from_config'):

            providers = [
                GeminiConfig(),
                HuggingFaceConfig(),
                OllamaConfig()
            ]

            for provider in providers:
                # 必須メソッドの存在確認
                assert hasattr(provider, 'is_configured')
                assert hasattr(provider, 'test_connection')
                assert hasattr(provider, 'generate_text')

                # メソッドが呼び出し可能であることを確認
                assert callable(provider.is_configured)
                assert callable(provider.test_connection)
                assert callable(provider.generate_text)

    @patch('services.llm.provider_gemini.make_api_request')
    @patch('services.llm.provider_huggingface.make_api_request')
    @patch('services.llm.provider_ollama.make_api_request')
    def test_all_providers_response_format(self, mock_ollama_req, mock_hf_req, mock_gemini_req):
        """全プロバイダーのレスポンス形式統一テスト"""
        # モックレスポンス設定
        mock_gemini_req.return_value = (200, {
            'candidates': [{'content': {'parts': [{'text': 'gemini response'}]}}]
        })

        mock_hf_req.return_value = (200, {
            'choices': [{'message': {'content': 'hf response'}}]
        })

        mock_ollama_req.return_value = (200, {
            'response': 'ollama response',
            'done': True
        })

        with patch('services.llm.provider_gemini.load_config'), \
             patch('services.llm.provider_gemini.load_env_from_config'), \
             patch('services.llm.provider_huggingface.load_config'), \
             patch('services.llm.provider_huggingface.load_env_from_config'), \
             patch('services.llm.provider_ollama.load_config'), \
             patch('services.llm.provider_ollama.load_env_from_config'):

            providers = [
                GeminiConfig(),
                HuggingFaceConfig(),
                OllamaConfig()
            ]

            for provider in providers:
                response = provider.generate_text(prompt="test")

                # 全プロバイダーがLLMResponseを返すことを確認
                assert isinstance(response, LLMResponse)
                assert hasattr(response, 'provider')
                assert hasattr(response, 'model')
                assert hasattr(response, 'content')
                assert hasattr(response, 'is_success')
                assert hasattr(response, 'error_message')
                assert hasattr(response, 'response_time')


class TestLLMProvidersCLI:
    """LLMプロバイダー CLI 引数テスト"""

    def test_gemini_cli_arguments(self):
        """Gemini プロバイダー CLI 引数テスト"""
        import argparse

        # Gemini プロバイダーのargparseパターンを再現
        ap = argparse.ArgumentParser(description="Gemini provider")
        ap.add_argument("prompt", nargs="*", help="ユーザープロンプト（スペース可）")
        ap.add_argument("--system", help="system プロンプト")
        ap.add_argument("--opt", action="append", help="key=val（temperature, top_p など）")
        ap.add_argument("--timeout", type=int, default=60)
        ap.add_argument("--debug", type=int, default=0, metavar="LEVEL")
        ap.add_argument("--test", action="store_true", help="接続テストのみ実行")
        ap.add_argument("--list", action="store_true", help="利用可能なモデル一覧を表示")
        ap.add_argument("--model", type=str, help="使用するモデル名")

        # テストケース: --test オプション
        args = ap.parse_args(['--test'])
        assert args.test is True
        assert args.list is False
        assert args.debug == 0
        assert args.timeout == 60

        # テストケース: --list オプション
        args = ap.parse_args(['--list'])
        assert args.list is True
        assert args.test is False

        # テストケース: プロンプト指定
        args = ap.parse_args(['Hello', 'world'])
        assert args.prompt == ['Hello', 'world']
        assert args.test is False

        # テストケース: システムプロンプト
        args = ap.parse_args(['--system', 'You are a helpful assistant', 'Test prompt'])
        assert args.system == 'You are a helpful assistant'
        assert args.prompt == ['Test', 'prompt']

        # テストケース: 複数オプション
        args = ap.parse_args(['--opt', 'temperature=0.7', '--opt', 'top_p=0.9', '--model', 'gemini-pro', 'Generate text'])
        assert args.opt == ['temperature=0.7', 'top_p=0.9']
        assert args.model == 'gemini-pro'
        assert args.prompt == ['Generate', 'text']

        # テストケース: デバッグレベル
        args = ap.parse_args(['--debug', '2', 'Test'])
        assert args.debug == 2

        # テストケース: タイムアウト
        args = ap.parse_args(['--timeout', '120', 'Test'])
        assert args.timeout == 120

    def test_ollama_cli_arguments(self):
        """Ollama プロバイダー CLI 引数テスト"""
        import argparse

        # Ollama プロバイダーのargparseパターンを再現
        parser = argparse.ArgumentParser(description="Ollama LLM provider")
        parser.add_argument("--test", action="store_true", help="Test connection")
        parser.add_argument("--model", type=str, help="Model name to use")
        parser.add_argument("--prompt", type=str, help="Prompt to generate")
        parser.add_argument("--host", type=str, help="Ollama host URL")
        parser.add_argument("--list", action="store_true", help="List available models")
        parser.add_argument("--pull", type=str, help="Pull a model")
        parser.add_argument("--create", type=str, help="Create custom model from Modelfile")
        parser.add_argument("--modelfile", type=str, help="Path to Modelfile")
        parser.add_argument("--base-model", type=str, help="Base model for custom model")
        parser.add_argument("--delete", type=str, help="Delete a model")
        parser.add_argument("--debug", type=int, default=0, metavar="LEVEL")

        # テストケース: 接続テスト
        args = parser.parse_args(['--test'])
        assert args.test is True
        assert args.debug == 0

        # テストケース: モデル一覧
        args = parser.parse_args(['--list'])
        assert args.list is True
        assert args.test is False

        # テストケース: プロンプト生成
        args = parser.parse_args(['--model', 'llama2', '--prompt', 'Hello world'])
        assert args.model == 'llama2'
        assert args.prompt == 'Hello world'

        # テストケース: ホスト指定
        args = parser.parse_args(['--host', 'http://localhost:11434', '--test'])
        assert args.host == 'http://localhost:11434'
        assert args.test is True

        # テストケース: モデルプル
        args = parser.parse_args(['--pull', 'mistral'])
        assert args.pull == 'mistral'

        # テストケース: カスタムモデル作成
        args = parser.parse_args(['--create', 'my-model', '--modelfile', '/path/to/Modelfile'])
        assert args.create == 'my-model'
        assert args.modelfile == '/path/to/Modelfile'

        # テストケース: モデル削除
        args = parser.parse_args(['--delete', 'unused-model'])
        assert args.delete == 'unused-model'

        # テストケース: デバッグモード
        args = parser.parse_args(['--debug', '1', '--test'])
        assert args.debug == 1
        assert args.test is True

    def test_huggingface_cli_arguments(self):
        """HuggingFace プロバイダー CLI 引数テスト"""
        import argparse

        # HuggingFace プロバイダーのargparseパターンを再現
        ap = argparse.ArgumentParser(description="HF Router(OpenAI互換) client")
        ap.add_argument("prompt", nargs="*", help="ユーザープロンプト（スペース可）")
        ap.add_argument("--host", help="HF Router base URL")
        ap.add_argument("--model", help="モデル")
        ap.add_argument("--system", help="system プロンプト")
        ap.add_argument("--opt", action="append", help="key=val（temperature, top_p など）")
        ap.add_argument("--timeout", type=int, default=120)
        ap.add_argument("--debug", type=int, default=0, metavar="LEVEL")
        ap.add_argument("--test", action="store_true", help="接続テストのみ実行")
        ap.add_argument("--list", action="store_true", help="利用可能なモデル一覧を表示")

        # テストケース: 接続テスト
        args = ap.parse_args(['--test'])
        assert args.test is True
        assert args.timeout == 120
        assert args.debug == 0

        # テストケース: モデル一覧
        args = ap.parse_args(['--list'])
        assert args.list is True
        assert args.test is False

        # テストケース: カスタムホスト
        args = ap.parse_args(['--host', 'https://api.huggingface.co/v1', '--test'])
        assert args.host == 'https://api.huggingface.co/v1'
        assert args.test is True

        # テストケース: モデル指定
        args = ap.parse_args(['--model', 'openai/gpt-oss-20b:groq', 'Test prompt'])
        assert args.model == 'openai/gpt-oss-20b:groq'
        assert args.prompt == ['Test', 'prompt']

        # テストケース: システムプロンプト + オプション
        args = ap.parse_args([
            '--system', 'You are helpful',
            '--opt', 'temperature=0.8',
            '--opt', 'max_tokens=100',
            'Generate text'
        ])
        assert args.system == 'You are helpful'
        assert args.opt == ['temperature=0.8', 'max_tokens=100']
        assert args.prompt == ['Generate', 'text']

        # テストケース: タイムアウト + デバッグ
        args = ap.parse_args(['--timeout', '300', '--debug', '2', 'Test'])
        assert args.timeout == 300
        assert args.debug == 2
        assert args.prompt == ['Test']

    def test_cli_argument_validation(self):
        """CLI 引数バリデーションテスト"""
        import argparse

        # 無効な型のテスト
        parser = argparse.ArgumentParser()
        parser.add_argument("--timeout", type=int)
        parser.add_argument("--debug", type=int)

        # 正常な整数値
        args = parser.parse_args(['--timeout', '60', '--debug', '1'])
        assert args.timeout == 60
        assert args.debug == 1

        # 無効な値（SystemExitが発生）
        with pytest.raises(SystemExit):
            parser.parse_args(['--timeout', 'invalid'])

        with pytest.raises(SystemExit):
            parser.parse_args(['--debug', 'not_a_number'])

    def test_cli_help_generation(self):
        """CLI ヘルプ生成テスト"""
        import argparse

        # ヘルプメッセージが生成されることを確認
        parser = argparse.ArgumentParser(description="Test CLI")
        parser.add_argument("--test", action="store_true", help="Test option")
        parser.add_argument("--model", type=str, help="Model name")

        # ヘルプテキスト生成（SystemExitが発生するのが正常）
        with pytest.raises(SystemExit):
            parser.parse_args(['--help'])

    def test_cli_default_values(self):
        """CLI デフォルト値テスト"""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--timeout", type=int, default=60)
        parser.add_argument("--debug", type=int, default=0)
        parser.add_argument("--test", action="store_true")
        parser.add_argument("--model", type=str, default="default-model")

        # 引数なしの場合
        args = parser.parse_args([])
        assert args.timeout == 60
        assert args.debug == 0
        assert args.test is False
        assert args.model == "default-model"

        # 一部の引数のみ指定
        args = parser.parse_args(['--test', '--timeout', '120'])
        assert args.test is True
        assert args.timeout == 120
        assert args.debug == 0  # デフォルト値
        assert args.model == "default-model"  # デフォルト値


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
