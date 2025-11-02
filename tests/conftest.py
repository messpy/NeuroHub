"""
NeuroHub テスト共通設定 (conftest.py)

全テストで使用される共通フィクスチャとテスト設定を定義します。
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

import pytest

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# テスト用の環境変数設定
os.environ.update({
    "ENVIRONMENT": "test",
    "LOG_LEVEL": "INFO",
    "DATABASE_URL": "sqlite:///:memory:",
    "DISCORD_TOKEN": "test_discord_token",
    "OPENAI_API_KEY": "test_openai_key",
    "ANTHROPIC_API_KEY": "test_anthropic_key",
})


# ==================== 基本フィクスチャ ====================

@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で使用するイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """プロジェクトルートパス"""
    return project_root


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """一時ディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """テスト用基本設定"""
    return {
        "environment": "test",
        "debug": True,
        "log_level": "INFO",
        "database": {
            "url": "sqlite:///:memory:",
            "echo": False,
        },
        "llm": {
            "provider": "test",
            "model": "test-model",
            "api_key": "test-key",
        },
        "discord": {
            "token": "test_discord_token",
            "guild_id": 123456789,
        },
        "mcp": {
            "server_port": 8000,
            "client_timeout": 10,
        }
    }


# ==================== データベースフィクスチャ ====================
# 注：現在SQLAlchemyがインストールされていないため一時的にコメントアウト

# @pytest.fixture
# def db_engine():
#     """テスト用データベースエンジン"""
#     engine = create_engine("sqlite:///:memory:", echo=False)
#     yield engine
#     engine.dispose()


# @pytest.fixture
# def db_session(db_engine):
#     """テスト用データベースセッション"""
#     from services.db.models import Base

#     # テーブル作成
#     Base.metadata.create_all(db_engine)

#     # セッション作成
#     Session = sessionmaker(bind=db_engine)
#     session = Session()

#     yield session

#     # クリーンアップ
#     session.rollback()
#     session.close()
#     Base.metadata.drop_all(db_engine)


@pytest.fixture
def mock_db_manager():
    """モックデータベースマネージャー"""
    # from services.db.database_manager import DatabaseManager

    manager = Mock()
    manager.engine = Mock()
    manager.Session = Mock()
    manager.is_connected = Mock(return_value=True)
    manager.execute_query = AsyncMock()
    manager.get_session = Mock()
    return manager


# ==================== LLMフィクスチャ ====================

@pytest.fixture
def mock_llm_agent():
    """モックLLMエージェント"""
    # from agents.llm_agent import LLMAgent

    agent = Mock()
    agent.provider = "test"
    agent.model = "test-model"
    agent.generate_response = AsyncMock(return_value="テストレスポンス")
    agent.analyze_code = AsyncMock(return_value={"analysis": "テスト分析"})
    agent.generate_commit_message = AsyncMock(return_value="feat: テストコミット")
    return agent


@pytest.fixture
def mock_openai_client():
    """モックOpenAIクライアント"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "テストレスポンス"
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def mock_anthropic_client():
    """モックAnthropicクライアント"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = "テストレスポンス"
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    return mock_client


# ==================== Gitフィクスチャ ====================

@pytest.fixture
def mock_git_agent():
    """モックGitエージェント"""
    # from agents.git_smart_agent import GitSmartAgent

    agent = Mock()
    agent.repo = Mock()
    agent.get_status = AsyncMock(return_value={"status": "clean"})
    agent.commit_changes = AsyncMock(return_value="abc123")
    agent.analyze_diff = AsyncMock(return_value={"changes": "テスト変更"})
    return agent


@pytest.fixture
def git_repo(temp_dir):
    """テスト用Gitリポジトリ（簡易版）"""
    # import git  # GitPythonがインストールされていない場合の代替

    repo_path = temp_dir / "test_repo"
    repo_path.mkdir()

    # .gitディレクトリを作成してGitリポジトリの形を作る
    git_dir = repo_path / ".git"
    git_dir.mkdir()

    # 初期ファイル作成
    test_file = repo_path / "test.txt"
    test_file.write_text("テストファイル")

    return repo_path


# ==================== MCPフィクスチャ ====================

@pytest.fixture
def mock_mcp_server():
    """モックMCPサーバー"""
    # from services.mcp.mcp_enhanced import MCPEnhancedServer

    server = Mock()
    server.is_running = Mock(return_value=True)
    server.start = AsyncMock()
    server.stop = AsyncMock()
    server.handle_request = AsyncMock()
    return server


@pytest.fixture
def mock_mcp_client():
    """モックMCPクライアント"""
    # from services.mcp.mcp_enhanced import MCPEnhancedClient

    client = Mock()
    client.is_connected = Mock(return_value=True)
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.send_request = AsyncMock()
    return client


# ==================== Discordフィクスチャ ====================

@pytest.fixture
def mock_discord_bot():
    """モックDiscordボット"""
    # from services.discord.discord_bot import DiscordBot

    bot = Mock()
    bot.user = Mock()
    bot.user.id = 123456789
    bot.guilds = []
    bot.start = AsyncMock()
    bot.close = AsyncMock()
    return bot


@pytest.fixture
def mock_discord_context():
    """モックDiscordコンテキスト"""
    context = Mock()
    context.author = Mock()
    context.author.id = 987654321
    context.channel = Mock()
    context.guild = Mock()
    context.send = AsyncMock()
    context.reply = AsyncMock()
    return context


# ==================== ファイルシステムフィクスチャ ====================

@pytest.fixture
def sample_files(temp_dir):
    """サンプルファイル群"""
    files = {}

    # Python ファイル
    py_file = temp_dir / "sample.py"
    py_file.write_text('''
def hello_world():
    """Hello World関数"""
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
''')
    files['python'] = py_file

    # JSON ファイル
    json_file = temp_dir / "config.json"
    json_file.write_text('{"key": "value", "number": 42}')
    files['json'] = json_file

    # テキストファイル
    txt_file = temp_dir / "readme.txt"
    txt_file.write_text("これはテスト用のREADMEファイルです。")
    files['text'] = txt_file

    return files


# ==================== ネットワークフィクスチャ ====================

@pytest.fixture
def mock_http_session():
    """モックHTTPセッション"""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "success"})
        mock_response.text = AsyncMock(return_value="success")

        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

        yield mock_session


# ==================== ユーティリティフィクスチャ ====================

@pytest.fixture
def capture_logs():
    """ログキャプチャ"""
    import logging
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    yield log_capture

    logger.removeHandler(handler)


@pytest.fixture
def mock_time():
    """時間のモック"""
    with patch('time.time', return_value=1638360000.0):
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2021-12-01T12:00:00"
            yield mock_datetime


# ==================== テストマーカー設定 ====================

def pytest_configure(config):
    """pytest設定"""
    # カスタムマーカー登録
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """テスト収集後の処理"""
    # スローテストのマーク
    for item in items:
        # 統合テストは自動的にslowマーク
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.slow)

        # ファイル名でマーク自動付与
        if "test_db" in item.nodeid:
            item.add_marker(pytest.mark.db)
        elif "test_git" in item.nodeid:
            item.add_marker(pytest.mark.git)
        elif "test_llm" in item.nodeid:
            item.add_marker(pytest.mark.llm)
        elif "test_mcp" in item.nodeid:
            item.add_marker(pytest.mark.mcp)
        elif "test_discord" in item.nodeid:
            item.add_marker(pytest.mark.discord)


# ==================== テスト後クリーンアップ ====================

@pytest.fixture(autouse=True)
def cleanup_environment():
    """各テスト後の環境クリーンアップ"""
    yield

    # 環境変数のクリーンアップ
    test_env_vars = [
        "TEST_DATABASE_URL",
        "TEST_API_KEY",
        "TEST_CONFIG_PATH",
    ]

    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]


# ==================== パフォーマンス測定 ====================

@pytest.fixture
def benchmark_timer():
    """ベンチマーク用タイマー"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()
            return self

        def stop(self):
            self.end_time = time.perf_counter()
            return self

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()
