"""
パスワードマネージャー設定
"""
import os
from pathlib import Path

class Config:
    """アプリケーション設定クラス"""

    # データベース設定
    DATABASE_URL = "sqlite:///./password_manager.db"
    DATABASE_PATH = Path("./password_manager.db")

    # 暗号化設定
    ENCRYPTION_ALGORITHM = "AES-256-GCM"
    KEY_DERIVATION_ITERATIONS = 100000

    # API設定
    API_HOST = "127.0.0.1"
    API_PORT = 8000
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    # CLI設定
    CLI_APP_NAME = "secure-pwd"

    # ログ設定
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def get_database_path(cls) -> Path:
        """データベースファイルのパスを取得"""
        return cls.DATABASE_PATH.absolute()

    @classmethod
    def ensure_database_dir(cls) -> None:
        """データベースディレクトリが存在することを確認"""
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
