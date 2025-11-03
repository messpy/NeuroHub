"""
パスワードマネージャー メインエントリーポイント
"""
import sys
import os

# パッケージパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
import logging

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=Config.LOG_FORMAT
    )

def main():
    """メイン関数"""
    setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python main.py cli    # CLIアプリを起動")
        print("  python main.py api    # APIサーバーを起動")
        print("  python main.py test   # テストを実行")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "cli":
        # CLIアプリを起動
        from cli.app import cli
        # CLIの引数を調整（main.pyの引数を除去）
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        cli()

    elif mode == "api":
        # APIサーバーを起動
        import uvicorn
        from api.server import app

        logger.info("Starting Password Manager API Server")
        uvicorn.run(
            app,
            host=Config.API_HOST,
            port=Config.API_PORT,
            log_level=Config.LOG_LEVEL.lower()
        )

    elif mode == "test":
        # テストを実行
        import pytest
        test_args = [
            "tests/",
            "-v",
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term"
        ]
        pytest.main(test_args)

    else:
        print(f"不明なモード: {mode}")
        print("使用可能なモード: cli, api, test")
        sys.exit(1)

if __name__ == "__main__":
    main()
