#!/usr/bin/env python3
"""
FastAPI パスワードマネージャー サーバー

RESTful API でパスワード管理機能を提供
完全なエラーハンドリング、ドキュメント、型ヒントを含む

Created by Ollama MCP Agent
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

# プロジェクトルートをpathに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastapi import FastAPI, HTTPException, Depends, status, Security
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError as e:
    print(f"FastAPI インポートエラー: {e}")
    print("pip install fastapi uvicorn を実行してください")
    sys.exit(1)

# ローカルモジュールのインポート
try:
    from src.main import PasswordManager
    from src.models import PasswordEntry
    from src.encryption import EncryptionManager
except ImportError as e:
    print(f"ローカルモジュール インポートエラー: {e}")
    print("src/ ディレクトリのモジュールが見つかりません")
    sys.exit(1)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI アプリケーションの初期化
app = FastAPI(
    title="パスワードマネージャー API",
    description="Ollama MCP で生成されたパスワードマネージャー",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS の設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セキュリティ設定
security = HTTPBearer()

# グローバル変数
password_manager: Optional[PasswordManager] = None

# Pydantic モデル定義
class PasswordEntryRequest(BaseModel):
    """パスワードエントリ追加リクエスト"""
    site: str = Field(..., description="サイト名", min_length=1, max_length=255)
    username: str = Field(..., description="ユーザー名", min_length=1, max_length=255)
    password: str = Field(..., description="パスワード", min_length=1)
    notes: str = Field("", description="備考", max_length=1000)

class PasswordEntryResponse(BaseModel):
    """パスワードエントリレスポンス"""
    id: Optional[int] = Field(None, description="エントリID")
    site: str = Field(..., description="サイト名")
    username: str = Field(..., description="ユーザー名")
    notes: str = Field("", description="備考")
    created_at: str = Field(..., description="作成日時")
    updated_at: str = Field(..., description="更新日時")

class PasswordEntryWithPassword(PasswordEntryResponse):
    """パスワード付きエントリレスポンス"""
    password: str = Field(..., description="復号化されたパスワード")

class APIResponse(BaseModel):
    """API共通レスポンス"""
    success: bool = Field(..., description="成功フラグ")
    message: str = Field(..., description="メッセージ")
    data: Optional[Any] = Field(None, description="データ")

class HealthResponse(BaseModel):
    """ヘルス チェック レスポンス"""
    status: str = Field(..., description="ステータス")
    timestamp: str = Field(..., description="チェック時刻")
    version: str = Field(..., description="バージョン")

# 依存性注入
async def get_password_manager() -> PasswordManager:
    """
    パスワードマネージャーインスタンスの取得

    Returns:
        PasswordManager: パスワードマネージャーインスタンス

    Raises:
        HTTPException: 初期化エラー
    """
    global password_manager

    if password_manager is None:
        try:
            # 環境変数からマスターパスワードを取得
            master_password = os.getenv("MASTER_PASSWORD", "default_master_password")
            password_manager = PasswordManager(master_password=master_password)
            logger.info("パスワードマネージャー初期化完了")
        except Exception as e:
            logger.error(f"パスワードマネージャー初期化エラー: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"パスワードマネージャー初期化エラー: {e}"
            )

    return password_manager

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    認証トークンの検証

    Args:
        credentials: 認証情報

    Returns:
        str: 検証済みトークン

    Raises:
        HTTPException: 認証エラー
    """
    # 簡単な認証（本番環境ではJWTやOAuth2を使用）
    expected_token = os.getenv("API_TOKEN", "password_manager_token_123")

    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効な認証トークン",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials

# API エンドポイント

@app.get("/", response_model=APIResponse)
async def root():
    """ルートエンドポイント"""
    return APIResponse(
        success=True,
        message="パスワードマネージャー API",
        data={
            "version": "1.0.0",
            "description": "Ollama MCP で生成されたパスワードマネージャー",
            "endpoints": [
                "/health - ヘルスチェック",
                "/docs - API ドキュメント",
                "/passwords - パスワード管理"
            ]
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェック"""
    try:
        # パスワードマネージャーの状態確認
        manager = await get_password_manager()

        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"サービス利用不可: {e}"
        )

@app.post("/passwords", response_model=APIResponse)
async def add_password(
    entry_request: PasswordEntryRequest,
    manager: PasswordManager = Depends(get_password_manager),
    token: str = Depends(verify_token)
):
    """
    パスワードエントリの追加

    Args:
        entry_request: パスワードエントリ情報
        manager: パスワードマネージャーインスタンス
        token: 認証トークン

    Returns:
        APIResponse: 追加結果
    """
    try:
        success = manager.add_password(
            site=entry_request.site,
            username=entry_request.username,
            password=entry_request.password,
            notes=entry_request.notes
        )

        if success:
            return APIResponse(
                success=True,
                message="パスワードエントリが正常に追加されました",
                data={
                    "site": entry_request.site,
                    "username": entry_request.username
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="パスワードエントリの追加に失敗しました"
            )

    except Exception as e:
        logger.error(f"パスワード追加エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"パスワード追加エラー: {e}"
        )

@app.get("/passwords/{site}", response_model=PasswordEntryWithPassword)
async def get_password(
    site: str,
    username: Optional[str] = None,
    manager: PasswordManager = Depends(get_password_manager),
    token: str = Depends(verify_token)
):
    """
    パスワードエントリの取得

    Args:
        site: サイト名
        username: ユーザー名（オプション）
        manager: パスワードマネージャーインスタンス
        token: 認証トークン

    Returns:
        PasswordEntryWithPassword: パスワードエントリ
    """
    try:
        entry_data = manager.get_password(site, username)

        if entry_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"パスワードエントリが見つかりません: {site}"
            )

        return PasswordEntryWithPassword(**entry_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"パスワード取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"パスワード取得エラー: {e}"
        )

@app.get("/passwords", response_model=List[PasswordEntryResponse])
async def list_passwords(
    manager: PasswordManager = Depends(get_password_manager),
    token: str = Depends(verify_token)
):
    """
    パスワードエントリ一覧の取得

    Args:
        manager: パスワードマネージャーインスタンス
        token: 認証トークン

    Returns:
        List[PasswordEntryResponse]: パスワードエントリ一覧
    """
    try:
        entries = manager.list_entries()

        response_entries = []
        for entry in entries:
            response_entries.append(PasswordEntryResponse(
                id=entry.get('id'),
                site=entry.get('site'),
                username=entry.get('username'),
                notes=entry.get('notes', ''),
                created_at=entry.get('created_at'),
                updated_at=entry.get('updated_at')
            ))

        return response_entries

    except Exception as e:
        logger.error(f"パスワード一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"パスワード一覧取得エラー: {e}"
        )

@app.delete("/passwords/{site}", response_model=APIResponse)
async def delete_password(
    site: str,
    username: Optional[str] = None,
    manager: PasswordManager = Depends(get_password_manager),
    token: str = Depends(verify_token)
):
    """
    パスワードエントリの削除

    Args:
        site: サイト名
        username: ユーザー名（オプション）
        manager: パスワードマネージャーインスタンス
        token: 認証トークン

    Returns:
        APIResponse: 削除結果
    """
    try:
        success = manager.delete_password(site, username)

        if success:
            return APIResponse(
                success=True,
                message="パスワードエントリが正常に削除されました",
                data={
                    "site": site,
                    "username": username
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"削除対象のパスワードエントリが見つかりません: {site}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"パスワード削除エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"パスワード削除エラー: {e}"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """グローバル例外ハンドラー"""
    logger.error(f"予期しないエラー: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "内部サーバーエラー",
            "detail": str(exc)
        }
    )

def create_app() -> FastAPI:
    """
    FastAPI アプリケーションの作成

    Returns:
        FastAPI: 設定済みアプリケーション
    """
    return app

if __name__ == "__main__":
    try:
        print("=== パスワードマネージャー API サーバー ===")
        print("サーバー起動中...")

        # 環境変数の確認
        host = os.getenv("API_HOST", "127.0.0.1")
        port = int(os.getenv("API_PORT", "8000"))

        print(f"サーバーアドレス: http://{host}:{port}")
        print(f"API ドキュメント: http://{host}:{port}/docs")
        print("認証トークン: MASTER_PASSWORD 環境変数を設定してください")
        print("API トークン: API_TOKEN 環境変数を設定してください")

        # サーバー起動
        uvicorn.run(
            "server:app",
            host=host,
            port=port,
            reload=True,  # 開発時のみ
            log_level="info"
        )

    except KeyboardInterrupt:
        print("\nサーバーを停止しました")
    except Exception as e:
        logger.error(f"サーバー起動エラー: {e}")
        print(f"エラー: {e}")
        sys.exit(1)
