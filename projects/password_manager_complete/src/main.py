#!/usr/bin/env python3
"""
完全なパスワードマネージャー メインエントリーポイント
すべてのimport文、docstring、エラーハンドリングを含む

Created by Ollama MCP Agent
"""

import sys
import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

# プロジェクトルートをpathに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ローカルモジュールのインポート
try:
    from src.database import DatabaseManager
    from src.encryption import EncryptionManager
    from src.models import PasswordEntry
except ImportError as e:
    print(f"モジュールインポートエラー: {e}")
    print("必要なモジュールが見つかりません。")
    sys.exit(1)

def setup_logging() -> logging.Logger:
    """
    ログ設定のセットアップ
    
    Returns:
        logging.Logger: 設定済みロガー
    """
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('data/password_manager.log')
            ]
        )
        return logging.getLogger(__name__)
    except Exception as e:
        print(f"ログ設定エラー: {e}")
        # 基本的なロガーを返す
        return logging.getLogger(__name__)

class PasswordManager:
    """
    完全なパスワードマネージャークラス
    
    パスワードの暗号化保存、検索、管理機能を提供する
    """
    
    def __init__(self, db_path: str = "data/passwords.db", master_password: str = None):
        """
        パスワードマネージャーの初期化
        
        Args:
            db_path (str): データベースファイルのパス
            master_password (str): マスターパスワード
            
        Raises:
            RuntimeError: 初期化に失敗した場合
        """
        try:
            self.logger = setup_logging()
            self.logger.info("パスワードマネージャー初期化開始")
            
            # データディレクトリの作成
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # データベースマネージャーの初期化
            self.db_manager = DatabaseManager(db_path)
            
            # 暗号化マネージャーの初期化
            if master_password is None:
                master_password = self._get_master_password()
            self.encryption_manager = EncryptionManager(master_password)
            
            self.logger.info("パスワードマネージャー初期化完了")
            
        except Exception as e:
            self.logger.error(f"初期化エラー: {e}")
            raise RuntimeError(f"初期化エラー: {e}")
    
    def _get_master_password(self) -> str:
        """
        マスターパスワードの取得
        
        Returns:
            str: マスターパスワード
        """
        try:
            import getpass
            return getpass.getpass("マスターパスワードを入力してください: ")
        except Exception as e:
            self.logger.warning(f"マスターパスワード入力エラー: {e}")
            return "default_master_password"  # 開発用デフォルト
    
    def add_password(self, site: str, username: str, password: str, notes: str = "") -> bool:
        """
        パスワードエントリの追加
        
        Args:
            site (str): サイト名
            username (str): ユーザー名
            password (str): パスワード
            notes (str): 備考
            
        Returns:
            bool: 追加成功時True
        """
        try:
            self.logger.info(f"パスワード追加開始: {site}")
            
            # パスワードの暗号化
            encrypted_password = self.encryption_manager.encrypt(password)
            
            # エントリの作成
            entry = PasswordEntry(
                site=site,
                username=username,
                encrypted_password=encrypted_password,
                notes=notes
            )
            
            # データベースに追加
            result = self.db_manager.add_entry(entry)
            
            if result:
                self.logger.info(f"パスワード追加成功: {site}")
            else:
                self.logger.error(f"パスワード追加失敗: {site}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"パスワード追加エラー: {e}")
            return False
    
    def get_password(self, site: str, username: str = None) -> Optional[Dict[str, Any]]:
        """
        パスワードの取得
        
        Args:
            site (str): サイト名
            username (str, optional): ユーザー名
            
        Returns:
            Optional[Dict[str, Any]]: パスワード情報、見つからない場合None
        """
        try:
            self.logger.info(f"パスワード取得開始: {site}")
            
            # データベースから検索
            entry = self.db_manager.get_entry(site, username)
            
            if entry is None:
                self.logger.warning(f"パスワードが見つかりません: {site}")
                return None
            
            # パスワードの復号化
            decrypted_password = self.encryption_manager.decrypt(entry.encrypted_password)
            
            result = {
                'site': entry.site,
                'username': entry.username,
                'password': decrypted_password,
                'notes': entry.notes,
                'created_at': entry.created_at,
                'updated_at': entry.updated_at
            }
            
            self.logger.info(f"パスワード取得成功: {site}")
            return result
            
        except Exception as e:
            self.logger.error(f"パスワード取得エラー: {e}")
            return None
    
    def list_entries(self) -> List[Dict[str, Any]]:
        """
        全パスワードエントリの一覧取得
        
        Returns:
            List[Dict[str, Any]]: パスワードエントリのリスト
        """
        try:
            self.logger.info("パスワード一覧取得開始")
            
            entries = self.db_manager.list_entries()
            result = []
            
            for entry in entries:
                result.append({
                    'id': entry.id,
                    'site': entry.site,
                    'username': entry.username,
                    'notes': entry.notes,
                    'created_at': entry.created_at,
                    'updated_at': entry.updated_at
                })
            
            self.logger.info(f"パスワード一覧取得成功: {len(result)}件")
            return result
            
        except Exception as e:
            self.logger.error(f"パスワード一覧取得エラー: {e}")
            return []
    
    def delete_password(self, site: str, username: str = None) -> bool:
        """
        パスワードエントリの削除
        
        Args:
            site (str): サイト名
            username (str, optional): ユーザー名
            
        Returns:
            bool: 削除成功時True
        """
        try:
            self.logger.info(f"パスワード削除開始: {site}")
            
            result = self.db_manager.delete_entry(site, username)
            
            if result:
                self.logger.info(f"パスワード削除成功: {site}")
            else:
                self.logger.error(f"パスワード削除失敗: {site}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"パスワード削除エラー: {e}")
            return False

def main():
    """
    メイン関数
    
    Returns:
        int: 終了ステータス
    """
    try:
        print("=== パスワードマネージャー ===")
        print("初期化中...")
        
        # パスワードマネージャーの初期化
        manager = PasswordManager()
        
        print("パスワードマネージャーが正常に起動しました")
        print("使用方法:")
        print("  - API サーバー: python api/server.py")
        print("  - CLI ツール: python cli/manager.py --help")
        print("  - テスト実行: python -m pytest tests/")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n中断されました")
        return 1
    except Exception as e:
        print(f"エラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())