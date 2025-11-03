"""
LLMエージェント統合テスト

agent_llm.pyの各機能（ステータス、プロバイダー切替、応答生成）をテスト
"""

import pytest
import os
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.agent_llm import LLMAgent


class TestLLMAgentBasic:
    """LLMエージェント基本機能テスト"""

    @pytest.fixture
    def agent(self):
        """テスト用エージェント作成"""
        print("\n🤖 LLMエージェント初期化中...")
        agent = LLMAgent()
        available_provider = agent.get_first_available_provider()
        print(f"✅ 初期化完了: 利用可能プロバイダー={available_provider}")
        return agent

    def test_agent_initialization(self, agent):
        """エージェント初期化テスト"""
        assert agent is not None
        available_provider = agent.get_first_available_provider()
        assert available_provider in ["gemini", "huggingface", "ollama", None]
        print(f"✅ 利用可能プロバイダー: {available_provider}")

    def test_get_status(self, agent):
        """ステータス取得テスト"""
        status = agent.check_provider_status()

        print("\n📊 LLMステータス:")
        for provider_name, provider_status in status.items():
            print(f"   {provider_name}: 利用可能={provider_status.available}, 設定済み={provider_status.configured}")

        assert isinstance(status, dict)
        assert len(status) > 0
        # 少なくとも1つのプロバイダーが存在することを確認
        assert any(status.values())

    def test_generate_response(self, agent):
        """応答生成テスト（固定プロンプト）"""
        test_prompt = "こんにちは世界を英語にしたら？"

        print(f"\n📝 プロンプト: {test_prompt}")
        response = agent.generate(test_prompt)

        print(f"📤 応答({agent.current_provider}): {response}")

        # 検証
        assert response is not None
        assert len(response) > 0

        # キーワードチェック
        response_lower = response.lower()
        has_keyword = any(kw in response_lower for kw in ["hello", "world"])
        print(f"{'✅' if has_keyword else '⚠️'} キーワード検出: {has_keyword}")


class TestLLMAgentProviderSwitch:
    """プロバイダー切替テスト"""

    @pytest.fixture
    def agent(self):
        """テスト用エージェント作成"""
        return LLMAgent()

    def test_switch_to_gemini(self, agent):
        """Gemini利用可能性テスト"""
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")

        # 特定プロバイダーでエージェント作成
        gemini_agent = LLMAgent(provider="gemini")
        available_provider = gemini_agent.get_first_available_provider()
        print(f"\n🔄 Gemini利用可能性: {available_provider == 'gemini'}")

        if available_provider == "gemini":
            from agents.agent_llm import LLMRequest
            request = LLMRequest(prompt="こんにちは世界を英語にしたら？")
            response = gemini_agent.generate_text(request)
            print(f"📤 Gemini応答: {response.content[:50]}...")
            assert response.is_success

    def test_switch_to_huggingface(self, agent):
        """HuggingFace利用可能性テスト"""
        if not os.getenv("HUGGINGFACE_API_KEY"):
            pytest.skip("HUGGINGFACE_API_KEY not set")

        huggingface_agent = LLMAgent(provider="huggingface")
        available_provider = huggingface_agent.get_first_available_provider()
        print(f"\n🔄 HuggingFace利用可能性: {available_provider == 'huggingface'}")

        if available_provider == "huggingface":
            from agents.agent_llm import LLMRequest
            request = LLMRequest(prompt="こんにちは世界を英語にしたら？")
            response = huggingface_agent.generate_text(request)
            print(f"📤 HuggingFace応答: {response.content[:50]}...")
            assert response.is_success

    def test_switch_to_ollama(self, agent):
        """Ollama利用可能性テスト"""
        # Ollama利用可能性確認
        ollama_agent = LLMAgent(provider="ollama")
        available_provider = ollama_agent.get_first_available_provider()

        if available_provider != "ollama":
            pytest.skip(f"Ollama利用不可")

        print(f"\n🔄 Ollama利用可能性: True")

        from agents.agent_llm import LLMRequest
        request = LLMRequest(prompt="こんにちは世界を英語にしたら？")
        response = ollama_agent.generate_text(request)
        print(f"� Ollama応答: {response.content[:50]}...")
        assert response.is_success

        if success:
            assert agent.current_provider == "ollama"
            response = agent.generate("こんにちは世界を英語にしたら？")
            print(f"📤 Ollama応答: {response}")
            assert len(response) > 0


class TestLLMAgentCLI:
    """CLI機能テスト"""

    @patch('sys.argv', ['agent_llm.py', '--test'])
    def test_cli_test_mode(self):
        """--testモードテスト"""
        # 標準出力キャプチャ
        captured_output = StringIO()

        with patch('sys.stdout', captured_output):
            # CLIメイン関数実行（import時実行を防ぐため、ここでimport）
            from agents.agent_llm import main
            try:
                main()
            except SystemExit:
                pass

        output = captured_output.getvalue()
        print(f"\n📋 CLI出力:\n{output}")

        # 出力検証
        assert "レスポンス:" in output or "応答:" in output

    @patch('sys.argv', ['agent_llm.py', '--status'])
    def test_cli_status_mode(self):
        """--statusモードテスト"""
        captured_output = StringIO()

        with patch('sys.stdout', captured_output):
            from agents.agent_llm import main
            try:
                main()
            except SystemExit:
                pass

        output = captured_output.getvalue()
        print(f"\n📋 CLI出力:\n{output}")

        # 出力検証
        assert "プロバイダー:" in output or "provider" in output.lower()


class TestLLMAgentDB:
    """DB参照機能テスト"""

    @pytest.fixture
    def agent(self):
        """テスト用エージェント作成"""
        return LLMAgent()

    def test_db_history_save(self, agent):
        """履歴保存テスト"""
        test_prompt = "テスト用プロンプト"
        from agents.agent_llm import LLMRequest
        request = LLMRequest(prompt=test_prompt)
        response = agent.generate_text(request)

        print(f"\n💾 DB保存確認:")
        print(f"   プロンプト: {test_prompt}")
        print(f"   応答: {response.content[:50]}...")

        # 応答が正常に生成されたことを確認
        assert response.is_success or response.content

        # DB保存確認（履歴マネージャーがセッションIDを持っているか）
        assert agent.history_manager.session_id is not None
        print(f"   セッションID: {agent.history_manager.session_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
