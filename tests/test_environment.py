"""
テスト環境確認用の基本テスト

pytestの動作とフィクスチャが正しく設定されているかを確認します。
"""

import pytest
from pathlib import Path


class TestEnvironmentSetup:
    """テスト環境セットアップの確認"""

    def test_project_structure(self, project_root_path):
        """プロジェクト構造の確認"""
        assert project_root_path.exists()
        assert (project_root_path / "agents").exists()
        assert (project_root_path / "services").exists()
        assert (project_root_path / "tests").exists()
        assert (project_root_path / "pyproject.toml").exists()

    def test_temp_dir_fixture(self, temp_dir):
        """一時ディレクトリフィクスチャの確認"""
        assert temp_dir.exists()
        assert temp_dir.is_dir()

        # テストファイル作成
        test_file = temp_dir / "test.txt"
        test_file.write_text("テスト")
        assert test_file.exists()

    def test_config_fixture(self, test_config):
        """設定フィクスチャの確認"""
        assert test_config["environment"] == "test"
        assert "database" in test_config
        assert "llm" in test_config
        assert "discord" in test_config

    def test_sample_files_fixture(self, sample_files):
        """サンプルファイルフィクスチャの確認"""
        assert "python" in sample_files
        assert "json" in sample_files
        assert "text" in sample_files

        # Pythonファイルの内容確認
        py_content = sample_files["python"].read_text()
        assert "def hello_world" in py_content


@pytest.mark.unit
class TestBasicFunctionality:
    """基本機能のテスト"""

    def test_simple_assertion(self):
        """基本的なアサーション"""
        assert 1 + 1 == 2
        assert "hello" == "hello"
        assert [1, 2, 3] == [1, 2, 3]

    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 3),
        (3, 4),
        (10, 11),
    ])
    def test_parametrized(self, input, expected):
        """パラメータ化テスト"""
        assert input + 1 == expected

    def test_exception_handling(self):
        """例外処理テスト"""
        with pytest.raises(ValueError):
            int("not_a_number")

        with pytest.raises(ZeroDivisionError):
            1 / 0


@pytest.mark.asyncio
class TestAsyncFunctionality:
    """非同期機能のテスト"""

    async def test_async_basic(self):
        """基本的な非同期テスト"""
        import asyncio

        async def async_func():
            await asyncio.sleep(0.001)
            return "success"

        result = await async_func()
        assert result == "success"

    async def test_async_with_mock(self):
        """非同期モックテスト"""
        from unittest.mock import AsyncMock

        mock_func = AsyncMock(return_value="mocked_result")
        result = await mock_func()
        assert result == "mocked_result"
        mock_func.assert_called_once()


@pytest.mark.unit
class TestUtilityFunctions:
    """ユーティリティ関数のテスト"""

    def test_path_operations(self, temp_dir):
        """パス操作のテスト"""
        # ディレクトリ作成
        new_dir = temp_dir / "new_directory"
        new_dir.mkdir()
        assert new_dir.exists()

        # ファイル作成
        new_file = new_dir / "file.txt"
        new_file.write_text("content")
        assert new_file.read_text() == "content"

    def test_string_operations(self):
        """文字列操作のテスト"""
        text = "Hello, World!"
        assert text.lower() == "hello, world!"
        assert text.replace("World", "Python") == "Hello, Python!"
        assert len(text) == 13

    def test_list_operations(self):
        """リスト操作のテスト"""
        data = [1, 2, 3, 4, 5]
        assert len(data) == 5
        assert sum(data) == 15
        assert max(data) == 5
        assert data[0] == 1
        assert data[-1] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
