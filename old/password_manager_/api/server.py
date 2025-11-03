"""
FastAPI REST APIサーバー
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
import logging
import sys
import os

# パッケージパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.password_manager import PasswordManager
from src.models import (
    UserCreate, UserLogin, PasswordEntryCreate, PasswordEntryUpdate,
    PasswordEntryResponse, PasswordGenerate, Token
)
from src.config import Config

logger = logging.getLogger(__name__)

# FastAPIアプリケーション初期化
app = FastAPI(
    title="Secure Password Manager API",
    description="セキュアなパスワードマネージャーのREST API",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切な制限を設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT認証設定
security = HTTPBearer()
JWT_SECRET = Config.SECRET_KEY
JWT_ALGORITHM = "HS256"

# グローバル変数でセッション管理
user_sessions: Dict[str, PasswordManager] = {}

def create_access_token(username: str) -> str:
    """JWTアクセストークンを作成"""
    expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """現在のユーザーを取得"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークン"
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンが期限切れです"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークン"
        )

def get_password_manager(username: str = Depends(get_current_user)) -> PasswordManager:
    """パスワードマネージャーインスタンスを取得"""
    if username not in user_sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションが見つかりません。再ログインしてください。"
        )

    pm = user_sessions[username]
    if not pm.is_logged_in():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ログインが必要です"
        )

    return pm

@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate) -> Dict[str, str]:
    """新しいユーザーを登録"""
    pm = PasswordManager()

    success = pm.create_user(user_data.username, user_data.master_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザー登録に失敗しました。ユーザー名が既に存在している可能性があります。"
        )

    return {"message": "ユーザー登録が完了しました"}

@app.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin) -> Token:
    """ユーザーログイン"""
    pm = PasswordManager()

    success = pm.login(user_data.username, user_data.master_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません"
        )

    # セッションを保存
    user_sessions[user_data.username] = pm

    # JWTトークンを生成
    access_token = create_access_token(user_data.username)

    return Token(access_token=access_token, token_type="bearer")

@app.post("/auth/logout")
async def logout(username: str = Depends(get_current_user)) -> Dict[str, str]:
    """ユーザーログアウト"""
    if username in user_sessions:
        user_sessions[username].logout()
        del user_sessions[username]

    return {"message": "ログアウトが完了しました"}

@app.get("/passwords", response_model=List[PasswordEntryResponse])
async def get_passwords(search: Optional[str] = None,
                       pm: PasswordManager = Depends(get_password_manager)) -> List[Dict[str, Any]]:
    """パスワード一覧を取得"""
    entries = pm.get_passwords(search)
    return entries

@app.post("/passwords", status_code=status.HTTP_201_CREATED)
async def create_password(password_data: PasswordEntryCreate,
                         pm: PasswordManager = Depends(get_password_manager)) -> Dict[str, Any]:
    """新しいパスワードエントリを作成"""
    entry_id = pm.add_password(
        service_name=password_data.service_name,
        username=password_data.username,
        email=password_data.email,
        password=password_data.password,
        url=password_data.url,
        notes=password_data.notes
    )

    if entry_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="パスワードエントリの作成に失敗しました"
        )

    return {"id": entry_id, "message": "パスワードエントリが作成されました"}

@app.get("/passwords/{entry_id}", response_model=PasswordEntryResponse)
async def get_password(entry_id: int,
                      pm: PasswordManager = Depends(get_password_manager)) -> Dict[str, Any]:
    """単一のパスワードエントリを取得"""
    entry = pm.get_password(entry_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="パスワードエントリが見つかりません"
        )

    return entry

@app.put("/passwords/{entry_id}")
async def update_password(entry_id: int,
                         password_data: PasswordEntryUpdate,
                         pm: PasswordManager = Depends(get_password_manager)) -> Dict[str, str]:
    """パスワードエントリを更新"""
    # Noneでない値のみを更新対象にする
    updates = {k: v for k, v in password_data.dict().items() if v is not None}

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新するフィールドが指定されていません"
        )

    success = pm.update_password(entry_id, **updates)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="パスワードエントリが見つからないか、更新に失敗しました"
        )

    return {"message": "パスワードエントリが更新されました"}

@app.delete("/passwords/{entry_id}")
async def delete_password(entry_id: int,
                         pm: PasswordManager = Depends(get_password_manager)) -> Dict[str, str]:
    """パスワードエントリを削除"""
    success = pm.delete_password(entry_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="パスワードエントリが見つからないか、削除に失敗しました"
        )

    return {"message": "パスワードエントリが削除されました"}

@app.post("/passwords/generate")
async def generate_password(gen_params: PasswordGenerate,
                           pm: PasswordManager = Depends(get_password_manager)) -> Dict[str, str]:
    """セキュアなパスワードを生成"""
    password = pm.generate_password(
        length=gen_params.length,
        include_uppercase=gen_params.include_uppercase,
        include_lowercase=gen_params.include_lowercase,
        include_numbers=gen_params.include_numbers,
        include_special=gen_params.include_special,
        exclude_ambiguous=gen_params.exclude_ambiguous
    )

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="パスワード生成に失敗しました"
        )

    return {"password": password}

@app.get("/stats")
async def get_stats(pm: PasswordManager = Depends(get_password_manager)) -> Dict[str, Any]:
    """統計情報を取得"""
    stats = pm.get_stats()
    if "error" in stats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=stats["error"]
        )

    return stats

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """ヘルスチェック"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn

    # ログ設定
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=Config.LOG_FORMAT
    )

    logger.info("Starting Secure Password Manager API Server")

    uvicorn.run(
        "api.server:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
        log_level=Config.LOG_LEVEL.lower()
    )
