#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Manager - ユーザー情報管理
"""

import os
import json
import sqlite3
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .sqlite_craud import SQLiteCRAUD
from .llm_history_schema import LLM_HISTORY_SCHEMA, LLM_HISTORY_INDICES


class UserManager:
    """ユーザー情報管理クラス"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "neurohub.db"

        self.db_path = str(db_path)
        self.crud = SQLiteCRAUD(self.db_path)
        self._init_tables()

    def _init_tables(self):
        """テーブル初期化"""
        try:
            # ユーザーテーブル作成
            self.crud.execute_sql(LLM_HISTORY_SCHEMA["users"])

            # インデックス作成
            for index_sql in LLM_HISTORY_INDICES["users"]:
                self.crud.execute_sql(index_sql)

        except Exception as e:
            print(f"テーブル初期化エラー: {e}")

    def create_user(self, username: str, email: str = None, full_name: str = None,
                   preferred_provider: str = "ollama") -> str:
        """新規ユーザー作成"""
        try:
            user_id = self._generate_user_id(username)

            user_data = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "full_name": full_name,
                "preferred_provider": preferred_provider,
                "provider_config": json.dumps({}),
                "settings": json.dumps({"theme": "dark", "language": "ja"}),
                "api_keys": json.dumps({}),
                "usage_stats": json.dumps({"requests": 0, "tokens": 0}),
                "last_login": datetime.now().isoformat(),
                "is_active": 1
            }

            self.crud.insert("users", user_data)
            print(f"✅ ユーザー作成成功: {username} (ID: {user_id})")
            return user_id

        except Exception as e:
            print(f"❌ ユーザー作成エラー: {e}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザー情報取得"""
        try:
            users = self.crud.select_where("users", where={"user_id": user_id})
            if users:
                user = users[0]
                # JSON文字列をデコード
                user["provider_config"] = json.loads(user["provider_config"] or "{}")
                user["settings"] = json.loads(user["settings"] or "{}")
                user["api_keys"] = json.loads(user["api_keys"] or "{}")
                user["usage_stats"] = json.loads(user["usage_stats"] or "{}")
                return user
            return None
        except Exception as e:
            print(f"❌ ユーザー取得エラー: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """ユーザー名でユーザー情報取得"""
        try:
            users = self.crud.select_where("users", where={"username": username})
            if users:
                return self.get_user(users[0]["user_id"])
            return None
        except Exception as e:
            print(f"❌ ユーザー取得エラー: {e}")
            return None

    def update_user_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """ユーザー設定更新"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False

            # 既存設定とマージ
            current_settings = user["settings"]
            current_settings.update(settings)

            self.crud.update_where(
                "users",
                {"settings": json.dumps(current_settings), "updated_at": datetime.now().isoformat()},
                {"user_id": user_id}
            )
            return True
        except Exception as e:
            print(f"❌ ユーザー設定更新エラー: {e}")
            return False

    def update_provider_config(self, user_id: str, provider_config: Dict[str, Any]) -> bool:
        """プロバイダー設定更新"""
        try:
            self.crud.update_where(
                "users",
                {"provider_config": json.dumps(provider_config), "updated_at": datetime.now().isoformat()},
                {"user_id": user_id}
            )
            return True
        except Exception as e:
            print(f"❌ プロバイダー設定更新エラー: {e}")
            return False

    def update_usage_stats(self, user_id: str, requests: int = 0, tokens: int = 0) -> bool:
        """使用統計更新"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False

            stats = user["usage_stats"]
            stats["requests"] = stats.get("requests", 0) + requests
            stats["tokens"] = stats.get("tokens", 0) + tokens
            stats["last_updated"] = datetime.now().isoformat()

            self.crud.update_where(
                "users",
                {"usage_stats": json.dumps(stats), "updated_at": datetime.now().isoformat()},
                {"user_id": user_id}
            )
            return True
        except Exception as e:
            print(f"❌ 使用統計更新エラー: {e}")
            return False

    def update_last_login(self, user_id: str) -> bool:
        """最終ログイン時刻更新"""
        try:
            self.crud.update_where(
                "users",
                {"last_login": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
                {"user_id": user_id}
            )
            return True
        except Exception as e:
            print(f"❌ 最終ログイン更新エラー: {e}")
            return False

    def list_users(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """ユーザー一覧取得"""
        try:
            where = {"is_active": 1} if active_only else {}
            users = self.crud.select_where("users", where=where, order_by="created_at DESC")

            # 簡略版（機密情報除外）
            result = []
            for user in users:
                result.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "preferred_provider": user["preferred_provider"],
                    "last_login": user["last_login"],
                    "created_at": user["created_at"]
                })
            return result
        except Exception as e:
            print(f"❌ ユーザー一覧取得エラー: {e}")
            return []

    def _generate_user_id(self, username: str) -> str:
        """ユーザーID生成"""
        timestamp = str(int(datetime.now().timestamp()))
        raw = f"{username}_{timestamp}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """現在のユーザー取得（環境変数やデフォルトから）"""
        try:
            # 環境変数から取得を試行
            username = os.environ.get("NEUROHUB_USER", "default_user")

            user = self.get_user_by_username(username)
            if not user:
                # デフォルトユーザーを作成
                print(f"デフォルトユーザー '{username}' を作成中...")
                user_id = self.create_user(
                    username=username,
                    email=f"{username}@localhost",
                    full_name="Default User",
                    preferred_provider="ollama"
                )
                user = self.get_user(user_id)

            return user
        except Exception as e:
            print(f"❌ 現在ユーザー取得エラー: {e}")
            return None
