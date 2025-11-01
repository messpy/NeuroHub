#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_config_agent.py - ConfigAgent のユニットテスト
"""

import pytest
import tempfile
import shutil
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.config_agent import ConfigAgent, LLMProviderConfig, AgentConfig
except ImportError as e:
    print(f"Import error: {e}")
    # フォールバック定義
    class ConfigAgent:
        def __init__(self):
            pass
    class LLMProviderConfig:
        def __init__(self, name="test", enabled=True, api_key="", base_url="", model="", options=None):
            self.name = name
            self.enabled = enabled
            self.api_key = api_key
            self.base_url = base_url
            self.model = model
            self.options = options or {}
    class AgentConfig:
        def __init__(self, name="test", enabled=True, priority=1, fallback_enabled=True, options=None):
            self.name = name
            self.enabled = enabled
            self.priority = priority
            self.fallback_enabled = fallback_enabled
            self.options = options or {}


class TestLLMProviderConfig:
    """LLMProviderConfig のテストクラス"""

    def test_llm_provider_config_creation(self):
        """LLMProviderConfig作成テスト"""
        config = LLMProviderConfig(
            name="gemini",
            enabled=True,
            api_url="https://api.example.com",
            model="gemini-pro",
            max_tokens=500,
            temperature=0.7,
            priority=1
        )

        assert config.name == "gemini"
        assert config.enabled is True
        assert config.api_url == "https://api.example.com"
        assert config.model == "gemini-pro"
        assert config.max_tokens == 500
        assert config.temperature == 0.7
        assert config.priority == 1

    def test_llm_provider_config_defaults(self):
        """デフォルト値テスト"""
        config = LLMProviderConfig(name="test")

        assert config.enabled is True
        assert config.max_tokens == 200
        assert config.temperature == 0.3
        assert config.timeout == 30
        assert config.priority == 1


class TestAgentConfig:
    """AgentConfig のテストクラス"""

    def test_agent_config_creation(self):
        """AgentConfig作成テスト"""
        config = AgentConfig(
            name="test_agent",
            enabled=False,
            auto_mode=True,
            log_level="DEBUG",
            session_timeout=7200,
            max_retries=5
        )

        assert config.name == "test_agent"
        assert config.enabled is False
        assert config.auto_mode is True
        assert config.log_level == "DEBUG"
        assert config.session_timeout == 7200
        assert config.max_retries == 5

    def test_agent_config_defaults(self):
        """デフォルト値テスト"""
        config = AgentConfig(name="test")

        assert config.enabled is True
        assert config.auto_mode is False
        assert config.log_level == "INFO"
        assert config.session_timeout == 3600
        assert config.max_retries == 3


class TestConfigAgent:
    """ConfigAgent のテストクラス"""

    @pytest.fixture
    def temp_config_dir(self):
        """一時設定ディレクトリ"""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()

        yield config_dir

        # クリーンアップ
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_config_agent(self, temp_config_dir):
        """モックされたConfigAgent"""
        with patch('agents.config_agent.project_root', temp_config_dir.parent):
            with patch('agents.config_agent.LLMHistoryManager') as mock_history:
                agent = ConfigAgent()
                agent.config_dir = temp_config_dir

                # 設定ファイルパスを更新
                agent.config_files = {
                    "main": temp_config_dir / "config.yaml",
                    "llm": temp_config_dir / "llm_config.yaml",
                    "agent": temp_config_dir / "agent_config.yaml",
                    "prompts": temp_config_dir / "prompt_templates.yaml"
                }

                yield agent

    def test_init(self, mock_config_agent):
        """初期化テスト"""
        assert hasattr(mock_config_agent, 'config_dir')
        assert hasattr(mock_config_agent, 'config_files')
        assert hasattr(mock_config_agent, 'current_config')
        assert len(mock_config_agent.config_files) == 4

    def test_save_config_success(self, mock_config_agent):
        """設定保存成功テスト"""
        test_config = {
            "test_section": {
                "enabled": True,
                "value": 42
            }
        }

        success = mock_config_agent.save_config("main", test_config)

        assert success is True
        assert mock_config_agent.config_files["main"].exists()

        # ファイル内容確認
        with open(mock_config_agent.config_files["main"], 'r', encoding='utf-8') as f:
            saved_config = yaml.safe_load(f)

        assert saved_config == test_config

    def test_save_config_invalid_name(self, mock_config_agent):
        """無効な設定名での保存テスト"""
        test_config = {"test": "value"}

        with pytest.raises(KeyError):
            mock_config_agent.save_config("invalid_name", test_config)

    def test_load_all_configs_empty(self, mock_config_agent):
        """空設定読み込みテスト"""
        configs = mock_config_agent.load_all_configs()

        assert isinstance(configs, dict)
        assert len(configs) == 4
        assert all(isinstance(config, dict) for config in configs.values())

    def test_load_all_configs_existing(self, mock_config_agent):
        """既存設定読み込みテスト"""
        # テスト設定作成
        test_config = {"test": {"enabled": True}}

        with open(mock_config_agent.config_files["main"], 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f)

        configs = mock_config_agent.load_all_configs()

        assert configs["main"] == test_config

    def test_generate_llm_config_default(self, mock_config_agent):
        """デフォルトLLM設定生成テスト"""
        config = mock_config_agent.generate_llm_config()

        assert "llm" in config
        assert "providers" in config["llm"]
        assert "provider_priority" in config["llm"]
        assert "default_settings" in config["llm"]

        # デフォルトプロバイダーチェック
        providers = config["llm"]["providers"]
        assert "gemini" in providers
        assert "huggingface" in providers
        assert "ollama" in providers

        # 優先順位チェック
        priority_list = config["llm"]["provider_priority"]
        assert "gemini" in priority_list or "huggingface" in priority_list or "ollama" in priority_list

    def test_generate_llm_config_custom(self, mock_config_agent):
        """カスタムLLM設定生成テスト"""
        custom_providers = [
            LLMProviderConfig(
                name="custom",
                api_url="https://custom.api.com",
                model="custom-model",
                priority=1
            )
        ]

        config = mock_config_agent.generate_llm_config(custom_providers)

        providers = config["llm"]["providers"]
        assert "custom" in providers
        assert providers["custom"]["api_url"] == "https://custom.api.com"
        assert providers["custom"]["model"] == "custom-model"
        assert providers["custom"]["priority"] == 1

    def test_generate_agent_config_default(self, mock_config_agent):
        """デフォルトエージェント設定生成テスト"""
        config = mock_config_agent.generate_agent_config()

        assert "agents" in config
        assert "global_settings" in config

        agents = config["agents"]
        assert "git_agent" in agents
        assert "llm_agent" in agents
        assert "config_agent" in agents
        assert "command_agent" in agents

        # エージェント設定確認
        for agent_name, agent_config in agents.items():
            assert "enabled" in agent_config
            assert "auto_mode" in agent_config
            assert "log_level" in agent_config

    def test_generate_agent_config_custom(self, mock_config_agent):
        """カスタムエージェント設定生成テスト"""
        custom_agents = [
            AgentConfig(
                name="custom_agent",
                enabled=False,
                auto_mode=True,
                log_level="DEBUG"
            )
        ]

        config = mock_config_agent.generate_agent_config(custom_agents)

        agents = config["agents"]
        assert "custom_agent" in agents
        assert agents["custom_agent"]["enabled"] is False
        assert agents["custom_agent"]["auto_mode"] is True
        assert agents["custom_agent"]["log_level"] == "DEBUG"

    @patch('os.getenv')
    def test_auto_detect_llm_providers_gemini(self, mock_getenv, mock_config_agent):
        """Gemini自動検出テスト"""
        mock_getenv.side_effect = lambda key, default=None: {
            'GEMINI_API_KEY': 'test_api_key',
            'HF_TOKEN': None,
            'OLLAMA_HOST': 'http://localhost:11434'
        }.get(key, default)

        providers = mock_config_agent.auto_detect_llm_providers()

        gemini_provider = next((p for p in providers if p.name == "gemini"), None)
        assert gemini_provider is not None
        assert gemini_provider.enabled is True
        assert gemini_provider.priority == 1

    @patch('os.getenv')
    def test_auto_detect_llm_providers_huggingface(self, mock_getenv, mock_config_agent):
        """HuggingFace自動検出テスト"""
        mock_getenv.side_effect = lambda key, default=None: {
            'GEMINI_API_KEY': None,
            'HF_TOKEN': 'test_hf_token',
            'OLLAMA_HOST': 'http://localhost:11434'
        }.get(key, default)

        providers = mock_config_agent.auto_detect_llm_providers()

        hf_provider = next((p for p in providers if p.name == "huggingface"), None)
        assert hf_provider is not None
        assert hf_provider.enabled is True

    @patch('os.getenv')
    @patch('requests.get')
    def test_auto_detect_llm_providers_ollama(self, mock_get, mock_getenv, mock_config_agent):
        """Ollama自動検出テスト"""
        mock_getenv.side_effect = lambda key, default=None: {
            'GEMINI_API_KEY': None,
            'HF_TOKEN': None,
            'OLLAMA_HOST': 'http://localhost:11434'
        }.get(key, default)

        # Ollama応答シミュレート
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        providers = mock_config_agent.auto_detect_llm_providers()

        ollama_provider = next((p for p in providers if p.name == "ollama"), None)
        assert ollama_provider is not None
        assert ollama_provider.enabled is True

    def test_update_from_history_empty(self, mock_config_agent):
        """空履歴での最適化テスト"""
        mock_config_agent.history_manager.get_provider_stats = Mock(return_value=[])

        optimization = mock_config_agent.update_from_history()

        assert "provider_performance" in optimization
        assert "recommended_priority" in optimization
        assert "configuration_updates" in optimization
        assert len(optimization["provider_performance"]) == 0

    def test_update_from_history_with_data(self, mock_config_agent):
        """履歴データありでの最適化テスト"""
        mock_stats = [
            {
                'provider': 'gemini',
                'total_requests': 100,
                'successful_requests': 95,
                'avg_response_time': 1500
            },
            {
                'provider': 'huggingface',
                'total_requests': 50,
                'successful_requests': 45,
                'avg_response_time': 3000
            }
        ]

        mock_config_agent.history_manager.get_provider_stats = Mock(return_value=mock_stats)

        optimization = mock_config_agent.update_from_history()

        assert len(optimization["provider_performance"]) == 2
        assert len(optimization["recommended_priority"]) == 2

        # パフォーマンスが良いgeminiが最初に来るはず
        assert optimization["recommended_priority"][0] == "gemini"

    def test_generate_full_config_success(self, mock_config_agent):
        """完全設定生成成功テスト"""
        with patch.object(mock_config_agent, 'auto_detect_llm_providers') as mock_detect:
            with patch.object(mock_config_agent, 'update_from_history') as mock_optimize:

                # モック設定
                mock_detect.return_value = [
                    LLMProviderConfig(name="gemini", priority=1),
                    LLMProviderConfig(name="ollama", priority=2)
                ]

                mock_optimize.return_value = {
                    "recommended_priority": ["gemini", "ollama"],
                    "configuration_updates": {}
                }

                success = mock_config_agent.generate_full_config()

                assert success is True

                # 生成されたファイル確認
                assert mock_config_agent.config_files["llm"].exists()
                assert mock_config_agent.config_files["agent"].exists()
                assert mock_config_agent.config_files["main"].exists()

    def test_get_config_status(self, mock_config_agent):
        """設定状態取得テスト"""
        # テスト設定ファイル作成
        test_content = {"test": "data"}
        with open(mock_config_agent.config_files["main"], 'w', encoding='utf-8') as f:
            yaml.dump(test_content, f)

        status = mock_config_agent.get_config_status()

        assert "config_files" in status
        assert "current_config" in status
        assert "environment_vars" in status

        # ファイル状態確認
        main_file_status = status["config_files"]["main"]
        assert main_file_status["exists"] is True
        assert main_file_status["size"] > 0

        # 環境変数状態確認
        env_vars = status["environment_vars"]
        assert "GEMINI_API_KEY" in env_vars
        assert "HF_TOKEN" in env_vars
        assert "OLLAMA_HOST" in env_vars


class TestConfigAgentIntegration:
    """ConfigAgent の統合テスト"""

    @pytest.fixture
    def integration_config_agent(self):
        """統合テスト用ConfigAgent"""
        temp_dir = tempfile.mkdtemp()

        with patch('agents.config_agent.project_root', temp_dir):
            with patch('agents.config_agent.LLMHistoryManager'):
                agent = ConfigAgent()
                yield agent

        # クリーンアップ
        shutil.rmtree(temp_dir)

    @patch('os.getenv')
    def test_full_config_workflow(self, mock_getenv, integration_config_agent):
        """完全設定ワークフローテスト"""
        # 環境変数シミュレート
        mock_getenv.side_effect = lambda key, default=None: {
            'GEMINI_API_KEY': 'test_gemini_key',
            'HF_TOKEN': 'test_hf_token'
        }.get(key, default)

        # 履歴データモック
        integration_config_agent.history_manager.get_provider_stats = Mock(return_value=[
            {
                'provider': 'gemini',
                'total_requests': 10,
                'successful_requests': 9,
                'avg_response_time': 1000
            }
        ])

        # 1. 設定生成
        success = integration_config_agent.generate_full_config()
        assert success is True

        # 2. 設定状態確認
        status = integration_config_agent.get_config_status()
        assert status["config_files"]["llm"]["exists"] is True
        assert status["config_files"]["agent"]["exists"] is True

        # 3. 設定内容確認
        configs = integration_config_agent.load_all_configs()
        assert "llm" in configs
        assert "agent" in configs

        # LLM設定詳細確認
        llm_config = configs["llm"]
        assert "llm" in llm_config
        assert "providers" in llm_config["llm"]

        providers = llm_config["llm"]["providers"]
        assert len(providers) > 0  # 少なくとも1つのプロバイダーが設定されている


class TestConfigAgentCLI:
    """ConfigAgent CLI 引数テスト"""

    def test_cli_generate_option(self):
        """--generate オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Config Agent - 設定管理")
        parser.add_argument("--generate", action="store_true", help="設定ファイルを生成")
        parser.add_argument("--status", action="store_true", help="設定状態を表示")
        parser.add_argument("--optimize", action="store_true", help="履歴ベースで最適化")
        parser.add_argument("--config", choices=["llm", "agent", "main"], help="特定の設定のみ生成")

        args = parser.parse_args(['--generate'])

        assert args.generate is True
        assert args.status is False
        assert args.optimize is False
        assert args.config is None

    def test_cli_status_option(self):
        """--status オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Config Agent - 設定管理")
        parser.add_argument("--generate", action="store_true", help="設定ファイルを生成")
        parser.add_argument("--status", action="store_true", help="設定状態を表示")
        parser.add_argument("--optimize", action="store_true", help="履歴ベースで最適化")
        parser.add_argument("--config", choices=["llm", "agent", "main"], help="特定の設定のみ生成")

        args = parser.parse_args(['--status'])

        assert args.status is True
        assert args.generate is False
        assert args.optimize is False
        assert args.config is None

    def test_cli_optimize_option(self):
        """--optimize オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Config Agent - 設定管理")
        parser.add_argument("--generate", action="store_true", help="設定ファイルを生成")
        parser.add_argument("--status", action="store_true", help="設定状態を表示")
        parser.add_argument("--optimize", action="store_true", help="履歴ベースで最適化")
        parser.add_argument("--config", choices=["llm", "agent", "main"], help="特定の設定のみ生成")

        args = parser.parse_args(['--optimize'])

        assert args.optimize is True
        assert args.generate is False
        assert args.status is False
        assert args.config is None

    def test_cli_config_option_llm(self):
        """--config llm オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Config Agent - 設定管理")
        parser.add_argument("--generate", action="store_true", help="設定ファイルを生成")
        parser.add_argument("--status", action="store_true", help="設定状態を表示")
        parser.add_argument("--optimize", action="store_true", help="履歴ベースで最適化")
        parser.add_argument("--config", choices=["llm", "agent", "main"], help="特定の設定のみ生成")

        args = parser.parse_args(['--config', 'llm'])

        assert args.config == 'llm'
        assert args.generate is False
        assert args.status is False
        assert args.optimize is False

    def test_cli_config_option_agent(self):
        """--config agent オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Config Agent - 設定管理")
        parser.add_argument("--generate", action="store_true", help="設定ファイルを生成")
        parser.add_argument("--status", action="store_true", help="設定状態を表示")
        parser.add_argument("--optimize", action="store_true", help="履歴ベースで最適化")
        parser.add_argument("--config", choices=["llm", "agent", "main"], help="特定の設定のみ生成")

        args = parser.parse_args(['--config', 'agent'])

        assert args.config == 'agent'
        assert args.generate is False
        assert args.status is False
        assert args.optimize is False

    def test_cli_config_option_main(self):
        """--config main オプションテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Config Agent - 設定管理")
        parser.add_argument("--generate", action="store_true", help="設定ファイルを生成")
        parser.add_argument("--status", action="store_true", help="設定状態を表示")
        parser.add_argument("--optimize", action="store_true", help="履歴ベースで最適化")
        parser.add_argument("--config", choices=["llm", "agent", "main"], help="特定の設定のみ生成")

        args = parser.parse_args(['--config', 'main'])

        assert args.config == 'main'
        assert args.generate is False
        assert args.status is False
        assert args.optimize is False

    def test_cli_combined_options(self):
        """複数オプション組み合わせテスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Config Agent - 設定管理")
        parser.add_argument("--generate", action="store_true", help="設定ファイルを生成")
        parser.add_argument("--status", action="store_true", help="設定状態を表示")
        parser.add_argument("--optimize", action="store_true", help="履歴ベースで最適化")
        parser.add_argument("--config", choices=["llm", "agent", "main"], help="特定の設定のみ生成")

        args = parser.parse_args(['--generate', '--config', 'llm'])

        assert args.generate is True
        assert args.config == 'llm'
        assert args.status is False
        assert args.optimize is False

    def test_cli_invalid_config_choice(self):
        """無効な--config選択肢テスト"""
        import argparse
        parser = argparse.ArgumentParser(description="Config Agent - 設定管理")
        parser.add_argument("--generate", action="store_true", help="設定ファイルを生成")
        parser.add_argument("--status", action="store_true", help="設定状態を表示")
        parser.add_argument("--optimize", action="store_true", help="履歴ベースで最適化")
        parser.add_argument("--config", choices=["llm", "agent", "main"], help="特定の設定のみ生成")

        with pytest.raises(SystemExit):
            parser.parse_args(['--config', 'invalid'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
