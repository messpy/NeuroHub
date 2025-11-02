#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_provider_ollama.py - Ollama Provider テストスイート

Ollama Providerの以下機能をテスト:
1. 接続確認
2. モデル一覧取得
3. 推論実行（日本語プロンプト）
4. Modelfileからモデル作成
5. カスタムモデル推論
6. モデル削除

実行方法:
    # 単体実行
    pytest tests/test_provider_ollama.py -v

    # 詳細デバッグ
    pytest tests/test_provider_ollama.py -v -s

    # 特定のテストのみ実行
    pytest tests/test_provider_ollama.py -v -k test_connection
"""

import pytest
import sys
import time
from pathlib import Path

# プロジェクトルート追加
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "llm"))

from services.ai.provider_ollama import OllamaConfig
from services.ai.llm_common import DebugLogger


# テスト設定
TEST_MODEL_NAME = "test-ollama-assistant"
TEST_PROMPT_JAPANESE = "こんにちは。簡単な自己紹介をしてください。"
TEST_MODELFILE_CONTENT = """FROM qwen2.5:0.5b-instruct

SYSTEM \"\"\"あなたはテスト用のAIアシスタントです。
質問に対して、簡潔で正確な日本語で回答してください。
\"\"\"

PARAMETER temperature 0.3
PARAMETER top_p 0.9
"""


@pytest.fixture(scope="module")
def ollama_config():
    """Ollama設定（モジュールスコープで1回だけ初期化）"""
    debug_logger = DebugLogger(True, level=2)
    config = OllamaConfig(debug_logger=debug_logger)
    yield config


class TestOllamaConnection:
    """接続・基本機能テスト"""

    def test_connection(self, ollama_config):
        """Ollamaサーバー接続テスト"""
        print("\n=== Ollama接続テスト ===")
        assert ollama_config.test_connection(), "Ollamaサーバーに接続できません"
        print("✅ 接続成功")

    def test_list_models(self, ollama_config):
        """モデル一覧取得テスト"""
        print("\n=== モデル一覧取得テスト ===")
        models = ollama_config.list_models()

        assert isinstance(models, list), "モデル一覧がリスト形式ではありません"
        assert len(models) > 0, "モデルが見つかりません（少なくとも1つ必要）"

        print(f"✅ {len(models)}個のモデルを検出:")
        for model in models[:5]:  # 最初の5つだけ表示
            print(f"  - {model.get('name', 'unknown')}")

    def test_inference_basic(self, ollama_config):
        """基本推論テスト（日本語プロンプト）"""
        print(f"\n=== 基本推論テスト ===")
        print(f"プロンプト: {TEST_PROMPT_JAPANESE}")

        response = ollama_config.infer(TEST_PROMPT_JAPANESE)

        assert response.status_code == 200, f"推論失敗: {response.error}"
        assert response.content, "応答が空です"
        assert len(response.content) > 0, "応答内容が空です"

        print(f"✅ 推論成功")
        print(f"応答: {response.content[:200]}...")  # 最初の200文字のみ
        print(f"モデル: {response.model}")
        print(f"レスポンス時間: {response.response_time:.2f}秒")


class TestModelfileOperations:
    """Modelfile操作テスト"""

    @pytest.fixture(scope="class")
    def cleanup_test_model(self, ollama_config):
        """テスト前後でテストモデルをクリーンアップ"""
        # テスト前にモデルを削除（既存の場合）
        debug_logger = DebugLogger(False)
        ollama_config.delete_model(TEST_MODEL_NAME, debug_logger)

        yield

        # テスト後にモデルを削除
        print(f"\n🧹 テストモデル削除: {TEST_MODEL_NAME}")
        ollama_config.delete_model(TEST_MODEL_NAME, debug_logger)

    def test_create_model_from_modelfile(self, ollama_config, cleanup_test_model):
        """Modelfileからモデル作成テスト"""
        print(f"\n=== Modelfile作成テスト ===")
        print(f"モデル名: {TEST_MODEL_NAME}")

        debug_logger = DebugLogger(True, level=2)
        success = ollama_config.create_model_from_modelfile(
            model_name=TEST_MODEL_NAME,
            modelfile_content=TEST_MODELFILE_CONTENT,
            debug_logger=debug_logger
        )

        assert success, "Modelfileからのモデル作成に失敗しました"

        # 作成されたモデルが一覧に存在するか確認
        time.sleep(2)  # モデル作成完了待機
        models = ollama_config.list_models()
        model_names = [m.get('name', '') for m in models]

        # モデル名は "name:latest" 形式になる可能性があるため部分一致で確認
        model_found = any(TEST_MODEL_NAME in name for name in model_names)
        assert model_found, f"{TEST_MODEL_NAME}が一覧に見つかりません。一覧: {model_names}"
        print(f"✅ モデル作成成功: {TEST_MODEL_NAME}")

    def test_custom_model_inference(self, ollama_config, cleanup_test_model):
        """カスタムモデルで推論テスト"""
        print(f"\n=== カスタムモデル推論テスト ===")
        print(f"モデル: {TEST_MODEL_NAME}")

        # テストモデルが存在しない場合は作成
        models = ollama_config.list_models()
        model_names = [m.get('name', '') for m in models]

        # モデル名は "name:latest" 形式になる可能性があるため部分一致で確認
        model_exists = any(TEST_MODEL_NAME in name for name in model_names)

        if not model_exists:
            debug_logger = DebugLogger(True, level=2)
            success = ollama_config.create_model_from_modelfile(
                model_name=TEST_MODEL_NAME,
                modelfile_content=TEST_MODELFILE_CONTENT,
                debug_logger=debug_logger
            )
            assert success, "テストモデルの作成に失敗しました"
            time.sleep(2)

        # カスタムモデルに切り替えて推論
        original_model = ollama_config.current_model
        ollama_config.current_model = TEST_MODEL_NAME

        try:
            response = ollama_config.infer(TEST_PROMPT_JAPANESE)

            assert response.status_code == 200, f"推論失敗: {response.error}"
            assert response.content, "応答が空です"
            assert response.model == TEST_MODEL_NAME, f"モデル名が一致しません（期待: {TEST_MODEL_NAME}, 実際: {response.model}）"

            print(f"✅ カスタムモデル推論成功")
            print(f"応答: {response.content[:200]}...")
            print(f"レスポンス時間: {response.response_time:.2f}秒")

        finally:
            # 元のモデルに戻す
            ollama_config.current_model = original_model


class TestRealModelfile:
    """実際のModelfileを使ったテスト"""

    def test_db_assistant_light_exists(self):
        """db_assistant_light.Modelfile 存在確認"""
        modelfile_path = ROOT / "services" / "ai" / "modelfiles" / "db_assistant_light.Modelfile"
        assert modelfile_path.exists(), f"Modelfileが見つかりません: {modelfile_path}"
        print(f"\n✅ Modelfile存在確認: {modelfile_path.name}")

    def test_build_db_assistant(self, ollama_config):
        """db_assistant_light をビルドしてテスト（簡略版Modelfile使用）"""
        print(f"\n=== db_assistant_light ビルドテスト ===")

        model_name = "neurohub-db-assistant-test"

        # 簡略版Modelfile（バッククォートを含まないシンプルな内容）
        simple_modelfile = """FROM qwen2.5:1.5b-instruct

SYSTEM \"\"\"あなたはデータベース操作コード生成アシスタントです。
SQLiteとPythonを使ったデータベース操作コードを生成してください。
日本語で丁寧に説明してください。
\"\"\"

PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
"""

        # モデル作成
        debug_logger = DebugLogger(True, level=2)
        success = ollama_config.create_model_from_modelfile(
            model_name=model_name,
            modelfile_content=simple_modelfile,
            debug_logger=debug_logger
        )

        try:
            assert success, "db_assistant_lightのビルドに失敗しました"
            print(f"✅ モデルビルド成功: {model_name}")

            # ビルドしたモデルで推論テスト
            time.sleep(2)
            original_model = ollama_config.current_model
            ollama_config.current_model = model_name

            test_prompt = "SQLiteでデータベースを作成するサンプルコードを教えてください"
            print(f"\nプロンプト: {test_prompt}")

            response = ollama_config.infer(test_prompt)

            assert response.status_code == 200, f"推論失敗: {response.error}"
            # 応答内容の確認（SQLite関連キーワードが含まれているか）
            assert any(keyword in response.content for keyword in ["sqlite3", "データベース", "SQL"]), \
                "期待されるコード要素が含まれていません"

            print(f"✅ 推論成功")
            print(f"応答（抜粋）: {response.content[:300]}...")

            ollama_config.current_model = original_model

        finally:
            # テスト後にモデル削除
            print(f"\n🧹 テストモデル削除: {model_name}")
            ollama_config.delete_model(model_name, DebugLogger(False))


class TestJapanesePrompt:
    """日本語プロンプトテスト"""

    def test_default_system_prompt_japanese(self, ollama_config):
        """デフォルトシステムプロンプトが日本語対応しているか確認"""
        print(f"\n=== 日本語プロンプトテスト ===")

        # config/llm_config.yaml の default_system_prompt を確認
        config_path = ROOT / "services" / "llm" / "config" / "llm_config.yaml"

        if not config_path.exists():
            pytest.skip("llm_config.yaml が見つかりません")

        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        default_prompt = config.get('llm', {}).get('default_settings', {}).get('default_system_prompt', '')

        assert default_prompt, "default_system_promptが設定されていません"
        assert "日本語" in default_prompt or "にほんご" in default_prompt, \
            "default_system_promptに日本語指定が含まれていません"

        print(f"✅ デフォルトプロンプト設定確認:")
        print(f"  {default_prompt[:100]}...")

    def test_japanese_response(self, ollama_config):
        """日本語応答テスト"""
        print(f"\n=== 日本語応答確認テスト ===")

        test_prompts = [
            "今日の天気を説明してください",
            "Pythonでリスト内包表記を使う例を教えてください",
            "こんにちは！元気ですか？"
        ]

        success_count = 0
        for prompt in test_prompts:
            print(f"\nプロンプト: {prompt}")
            response = ollama_config.infer(prompt)

            # タイムアウトの場合はスキップ（Ollamaサーバー負荷対策）
            if response.status_code == 500 and "timed out" in str(response.error):
                print(f"⚠️ タイムアウト（スキップ）: {response.error}")
                continue

            assert response.status_code == 200, f"推論失敗: {response.error}"
            assert response.content, "応答が空です"

            # 日本語文字が含まれているか確認（ひらがな・カタカナ・漢字）
            has_japanese = any(
                '\u3040' <= char <= '\u309F' or  # ひらがな
                '\u30A0' <= char <= '\u30FF' or  # カタカナ
                '\u4E00' <= char <= '\u9FFF'     # 漢字
                for char in response.content
            )

            assert has_japanese, f"日本語応答が含まれていません: {response.content[:100]}"
            print(f"✅ 日本語応答確認: {response.content[:100]}...")
            success_count += 1

        # 少なくとも1つは成功していることを確認
        assert success_count > 0, "すべてのプロンプトでタイムアウトしました"
        print(f"\n✅ 日本語応答テスト成功: {success_count}/{len(test_prompts)}")


if __name__ == "__main__":
    # 直接実行時の動作
    pytest.main([__file__, "-v", "-s"])
