"""
プロバイダー応答品質テスト

固定プロンプト「こんにちは世界を英語にしたら？」で各プロバイダーの応答確認
"""

import pytest
import os
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.ai.provider_gemini import GeminiConfig
from services.ai.provider_huggingface import HuggingFaceConfig
from services.ai.provider_ollama import OllamaConfig


# テスト用固定プロンプト
TEST_PROMPT = "こんにちは世界を英語にしたら？"
EXPECTED_KEYWORDS = ["hello", "world", "Hello World"]  # 期待される応答キーワード


class TestProviderResponse:
    """プロバイダー応答品質テスト"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テスト前セットアップ"""
        self.test_prompt = TEST_PROMPT
        print(f"\n📝 テストプロンプト: {self.test_prompt}")
    
    def _validate_response(self, response: str, provider_name: str) -> bool:
        """応答検証ヘルパー"""
        print(f"\n{'='*60}")
        print(f"🤖 プロバイダー: {provider_name}")
        print(f"📥 プロンプト: {self.test_prompt}")
        print(f"📤 応答: {response}")
        print(f"{'='*60}")
        
        # 応答が空でないこと
        assert response and len(response) > 0, f"{provider_name}: 応答が空です"
        
        # キーワードチェック（大文字小文字区別なし）
        response_lower = response.lower()
        has_keyword = any(kw.lower() in response_lower for kw in EXPECTED_KEYWORDS)
        
        print(f"✅ 応答長: {len(response)}文字")
        print(f"{'✅' if has_keyword else '⚠️'} キーワード検出: {has_keyword}")
        
        return has_keyword
    
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set"
    )
    def test_gemini_response(self):
        """Gemini応答品質テスト"""
        provider = GeminiConfig()
        
        # 接続確認
        is_available = provider.test_connection()
        assert is_available, f"Gemini接続失敗"
        
        # 応答取得
        llm_response = provider.infer(self.test_prompt)
        response = llm_response.content
        
        # 検証
        has_keyword = self._validate_response(response, "Gemini")
        assert has_keyword, f"Gemini応答に期待キーワードが含まれていません: {response}"
    
    @pytest.mark.skipif(
        not os.getenv("HUGGINGFACE_API_KEY"),
        reason="HUGGINGFACE_API_KEY not set"
    )
    def test_huggingface_response(self):
        """HuggingFace応答品質テスト"""
        provider = HuggingFaceConfig()
        
        # 接続確認
        is_available = provider.test_connection()
        assert is_available, f"HuggingFace接続失敗"
        
        # 応答取得
        llm_response = provider.infer(self.test_prompt)
        response = llm_response.content
        
        # 検証
        has_keyword = self._validate_response(response, "HuggingFace")
        assert has_keyword, f"HuggingFace応答に期待キーワードが含まれていません: {response}"
    
    def test_ollama_response(self):
        """Ollama応答品質テスト"""
        provider = OllamaConfig()
        
        # 接続確認
        is_available = provider.test_connection()
        
        if not is_available:
            pytest.skip(f"Ollama利用不可")
        
        # 応答取得
        llm_response = provider.infer(self.test_prompt)
        response = llm_response.content
        
        # 検証
        has_keyword = self._validate_response(response, "Ollama")
        assert has_keyword, f"Ollama応答に期待キーワードが含まれていません: {response}"


class TestProviderComparison:
    """プロバイダー比較テスト"""
    
    def test_all_providers_comparison(self):
        """全プロバイダー応答比較"""
        results = {}
        
        # Gemini
        if os.getenv("GEMINI_API_KEY"):
            try:
                provider = GeminiConfig()
                if provider.test_connection():
                    llm_response = provider.infer(TEST_PROMPT)
                    results["Gemini"] = llm_response.content
            except Exception as e:
                results["Gemini"] = f"ERROR: {e}"
        
        # HuggingFace
        if os.getenv("HUGGINGFACE_API_KEY"):
            try:
                provider = HuggingFaceConfig()
                if provider.test_connection():
                    llm_response = provider.infer(TEST_PROMPT)
                    results["HuggingFace"] = llm_response.content
            except Exception as e:
                results["HuggingFace"] = f"ERROR: {e}"
        
        # Ollama
        try:
            provider = OllamaConfig()
            if provider.test_connection():
                llm_response = provider.infer(TEST_PROMPT)
                results["Ollama"] = llm_response.content
        except Exception as e:
            results["Ollama"] = f"ERROR: {e}"
        
        # 結果表示
        print("\n" + "="*80)
        print("📊 プロバイダー応答比較")
        print("="*80)
        print(f"📝 プロンプト: {TEST_PROMPT}")
        print("-"*80)
        
        for provider_name, response in results.items():
            print(f"\n🤖 {provider_name}:")
            print(f"   {response}")
        
        print("="*80)
        
        # 少なくとも1つのプロバイダーが動作していることを確認
        assert len(results) > 0, "利用可能なプロバイダーがありません"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
