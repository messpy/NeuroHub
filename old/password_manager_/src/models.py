"""
データモデル定義
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()

class User(Base):
    """ユーザーテーブル（マスターパスワード管理）"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    master_password_hash = Column(String(255), nullable=False)
    salt = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class PasswordEntry(Base):
    """パスワードエントリテーブル"""
    __tablename__ = "password_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    service_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    encrypted_password = Column(LargeBinary, nullable=False)
    encryption_nonce = Column(LargeBinary, nullable=False)
    url = Column(String(500), nullable=True)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydanticスキーマ
class UserCreate(BaseModel):
    """ユーザー作成スキーマ"""
    username: str = Field(..., min_length=3, max_length=50)
    master_password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    """ユーザーログインスキーマ"""
    username: str
    master_password: str

class PasswordEntryCreate(BaseModel):
    """パスワードエントリ作成スキーマ"""
    service_name: str = Field(..., min_length=1, max_length=100)
    username: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    password: str = Field(..., min_length=1)
    url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)

class PasswordEntryUpdate(BaseModel):
    """パスワードエントリ更新スキーマ"""
    service_name: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = None
    url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)

class PasswordEntryResponse(BaseModel):
    """パスワードエントリレスポンススキーマ"""
    id: int
    service_name: str
    username: Optional[str]
    email: Optional[str]
    password: str  # 復号化済み
    url: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PasswordGenerate(BaseModel):
    """パスワード生成スキーマ"""
    length: int = Field(16, ge=8, le=128)
    include_uppercase: bool = True
    include_lowercase: bool = True
    include_numbers: bool = True
    include_special: bool = True
    exclude_ambiguous: bool = True

class Token(BaseModel):
    """トークンスキーマ"""
    access_token: str
    token_type: str
