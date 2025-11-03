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
        print(f"✅ 初期化完了: プロバイダー={agent.current_provider}")
        return agent
    
    def test_agent_initialization(self, agent):
        """エージェント初期化テスト"""
        assert agent is not None
        assert agent.current_provider in ["gemini", "huggingface", "ollama"]
        print(f"✅ 現在のプロバイダー: {agent.current_provider}")
    
    def test_get_status(self, agent):
        """ステータス取得テスト"""
        status = agent.get_status()
        
        print("\n📊 LLMステータス:")
        print(f"   現在のプロバイダー: {status['current_provider']}")
        print(f"   利用可能プロバイダー: {', '.join(status['available_providers'])}")
        
        assert "current_provider" in status
        assert "available_providers" in status
        assert isinstance(status["available_providers"], list)
        assert len(status["available_providers"]) > 0
    
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
        """Gemini切替テスト"""
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")
        
        success = agent.switch_provider("gemini")
        print(f"\n🔄 Gemini切替: {'成功' if success else '失敗'}")
        
        if success:
            assert agent.current_provider == "gemini"
            response = agent.generate("こんにちは世界を英語にしたら？")
            print(f"📤 Gemini応答: {response}")
            assert len(response) > 0
    
    def test_switch_to_huggingface(self, agent):
        """HuggingFace切替テスト"""
        if not os.getenv("HUGGINGFACE_API_KEY"):
            pytest.skip("HUGGINGFACE_API_KEY not set")
        
        success = agent.switch_provider("huggingface")
        print(f"\n🔄 HuggingFace切替: {'成功' if success else '失敗'}")
        
        if success:
            assert agent.current_provider == "huggingface"
            response = agent.generate("こんにちは世界を英語にしたら？")
            print(f"📤 HuggingFace応答: {response}")
            assert len(response) > 0
    
    def test_switch_to_ollama(self, agent):
        """Ollama切替テスト"""
        # Ollama利用可能性確認
        from services.ai.provider_ollama import OllamaProvider
        ollama = OllamaProvider()
        is_available, msg = ollama.check_availability()
        
        if not is_available:
            pytest.skip(f"Ollama利用不可: {msg}")
        
        success = agent.switch_provider("ollama")
        print(f"\n🔄 Ollama切替: {'成功' if success else '失敗'}")
        
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
        response = agent.generate(test_prompt)
        
        print(f"\n💾 DB保存確認:")
        print(f"   プロンプト: {test_prompt}")
        print(f"   応答: {response[:50]}...")
        
        # DB保存確認（agent_llm.pyにDB保存機能がある場合）
        # TODO: DB保存機能実装後にアサーション追加


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
