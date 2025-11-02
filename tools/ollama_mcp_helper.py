#!/usr/bin/env python3
"""
Ollama MCP 実装補助ツール

Ollamaでエラーなしで動作するMCP実装をサポートするための
補助ツール、サンプルコード、DB調べもの機能を提供します。
"""

import sqlite3
import json
import os
from typing import Dict, List, Any
from datetime import datetime

class OllamaMCPHelper:
    """Ollama MCP実装補助クラス"""
    
    def __init__(self, db_path: str = "data/ollama_mcp_helper.db"):
        """
        初期化
        
        Args:
            db_path: ヘルパーDB のパス
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """ヘルパーデータベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS mcp_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    pattern_name TEXT NOT NULL,
                    description TEXT,
                    code_template TEXT,
                    requirements TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS ollama_tips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tip_category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    example_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS common_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    solution TEXT NOT NULL,
                    prevention_tip TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def add_mcp_pattern(self, category: str, pattern_name: str, 
                       description: str, code_template: str, 
                       requirements: str = ""):
        """MCPパターンをDBに追加"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO mcp_patterns 
                (category, pattern_name, description, code_template, requirements)
                VALUES (?, ?, ?, ?, ?)
            """, (category, pattern_name, description, code_template, requirements))
    
    def get_mcp_patterns(self, category: str = None) -> List[Dict[str, Any]]:
        """MCPパターンを取得"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if category:
                cursor = conn.execute(
                    "SELECT * FROM mcp_patterns WHERE category = ? ORDER BY created_at DESC",
                    (category,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM mcp_patterns ORDER BY category, created_at DESC"
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def add_ollama_tip(self, tip_category: str, title: str, 
                      content: str, example_code: str = ""):
        """Ollama使用のコツをDBに追加"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ollama_tips 
                (tip_category, title, content, example_code)
                VALUES (?, ?, ?, ?)
            """, (tip_category, title, content, example_code))
    
    def get_ollama_tips(self, category: str = None) -> List[Dict[str, Any]]:
        """Ollama使用のコツを取得"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if category:
                cursor = conn.execute(
                    "SELECT * FROM ollama_tips WHERE tip_category = ? ORDER BY created_at DESC",
                    (category,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM ollama_tips ORDER BY tip_category, created_at DESC"
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def add_common_error(self, error_type: str, error_message: str,
                        solution: str, prevention_tip: str = ""):
        """よくあるエラーと解決策をDBに追加"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO common_errors 
                (error_type, error_message, solution, prevention_tip)
                VALUES (?, ?, ?, ?)
            """, (error_type, error_message, solution, prevention_tip))
    
    def search_error_solution(self, error_keyword: str) -> List[Dict[str, Any]]:
        """エラーキーワードで解決策を検索"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM common_errors 
                WHERE error_message LIKE ? OR solution LIKE ?
                ORDER BY created_at DESC
            """, (f"%{error_keyword}%", f"%{error_keyword}%"))
            return [dict(row) for row in cursor.fetchall()]
    
    def generate_password_manager_prompt(self) -> str:
        """Ollama用最適化パスワードマネージャープロンプトを生成"""
        
        # 基本要件
        base_requirements = """
# Ollama MCP パスワードマネージャー実装

## 重要: エラーなし実装要件
- すべての関数に完全なdocstringを含める
- try-except文でエラーハンドリングを徹底
- 型ヒントを必ず使用
- import文を明確に記述
- クラス・関数定義を完全に実装

## 技術仕様
"""

        # パターンから推奨構造を取得
        patterns = self.get_mcp_patterns("password_manager")
        if patterns:
            structure_info = "\n".join([
                f"### {p['pattern_name']}\n{p['description']}\n```python\n{p['code_template']}\n```\n"
                for p in patterns[:3]  # 最大3つのパターンを含める
            ])
        else:
            structure_info = """
### 基本構造
- src/: メインロジック
- api/: FastAPI エンドポイント  
- cli/: コマンドラインインターフェース
- tests/: テストファイル
"""

        # Ollamaのコツを取得
        tips = self.get_ollama_tips("mcp_implementation")
        tips_info = ""
        if tips:
            tips_info = "\n## Ollama実装のコツ\n" + "\n".join([
                f"- **{tip['title']}**: {tip['content']}"
                for tip in tips[:5]
            ])

        # エラー防止情報
        error_prevention = """
## エラー防止チェックリスト
1. ✅ 全関数にdocstring（\"\"\"三重引用符\"\"\"）
2. ✅ try-except文によるエラーハンドリング
3. ✅ from typing import List, Dict, Optional等の型ヒント
4. ✅ if __name__ == "__main__": での実行制御
5. ✅ import文の明確な記述
6. ✅ クラス初期化メソッド__init__の完全実装
"""

        return f"""
{base_requirements}

{structure_info}

{tips_info}

{error_prevention}

## 実装指示
SQLite、FastAPI、Click、cryptographyを使用して、以下のファイルを生成してください：

1. **src/main.py** - メインエントリーポイント
2. **src/models.py** - データモデル（完全なdocstring付き）
3. **src/database.py** - DB操作（エラーハンドリング完備）
4. **src/encryption.py** - 暗号化機能（try-except完備）
5. **api/server.py** - FastAPIサーバー
6. **cli/manager.py** - CLIツール
7. **tests/test_basic.py** - 基本テスト

各ファイルは独立して動作し、モジュールエラーが発生しないよう実装してください。
"""

def initialize_helper_data():
    """ヘルパーデータの初期化"""
    helper = OllamaMCPHelper()
    
    # MCPパターンの追加
    helper.add_mcp_pattern(
        "password_manager",
        "基本クラス構造",
        "パスワードマネージャーの基本クラス設計パターン",
        """
class PasswordManager:
    '''完全なパスワードマネージャークラス'''
    
    def __init__(self, db_path: str = "passwords.db"):
        '''初期化メソッド'''
        try:
            self.db_path = db_path
            self._setup_database()
        except Exception as e:
            raise RuntimeError(f"初期化エラー: {e}")
    
    def _setup_database(self) -> None:
        '''データベースセットアップ'''
        try:
            # DB初期化処理
            pass
        except Exception as e:
            raise DatabaseError(f"DB設定エラー: {e}")
""",
        "sqlite3, typing"
    )
    
    helper.add_mcp_pattern(
        "password_manager", 
        "エラーハンドリング",
        "Ollama実装でエラーを避けるためのパターン",
        """
def safe_operation(self, data: str) -> Optional[str]:
    '''安全な操作の実装例'''
    try:
        if not data:
            raise ValueError("データが空です")
        
        # メイン処理
        result = self._process_data(data)
        return result
        
    except ValueError as e:
        self.logger.error(f"値エラー: {e}")
        return None
    except Exception as e:
        self.logger.error(f"予期しないエラー: {e}")
        return None
""",
        "logging, typing"
    )
    
    # Ollamaのコツを追加
    helper.add_ollama_tip(
        "mcp_implementation",
        "docstring必須",
        "Ollamaでエラーを避けるため、すべての関数・クラスに完全なdocstringを記述する",
        '''
def example_function(param: str) -> str:
    """
    関数の説明
    
    Args:
        param: パラメータの説明
        
    Returns:
        戻り値の説明
        
    Raises:
        ValueError: エラーの説明
    """
    pass
'''
    )
    
    helper.add_ollama_tip(
        "mcp_implementation",
        "型ヒント完備",
        "from typing import List, Dict, Optional, Any を使用し、すべての引数と戻り値に型を指定する",
        "from typing import List, Dict, Optional, Any, Union"
    )
    
    # 共通エラーと解決策を追加
    helper.add_common_error(
        "MCP実装",
        "関数またはクラス定義がありません", 
        "すべての関数定義で def キーワードを使用し、クラス定義で class キーワードを使用する。コロン(:)を忘れずに記述する",
        "class MyClass: と def my_function(): の形式を確認"
    )
    
    helper.add_common_error(
        "MCP実装",
        "docstringが不足している可能性があります",
        "三重引用符（\"\"\"）を使用してdocstringを追加する。関数・クラスの直後に配置する",
        "def function():\\n    \"\"\"関数の説明\"\"\"\\n    pass の形式"
    )
    
    helper.add_common_error(
        "MCP実装", 
        "エラーハンドリングが不足している可能性があります",
        "try-except文を使用してエラーハンドリングを追加する。適切な例外クラスを指定する",
        "重要な処理はtry-except文で囲み、ログ出力も追加"
    )
    
    print("✅ Ollama MCP ヘルパーデータの初期化完了")
    return helper

if __name__ == "__main__":
    helper = initialize_helper_data()
    
    print("\n📋 利用可能なMCPパターン:")
    patterns = helper.get_mcp_patterns()
    for pattern in patterns:
        print(f"  - {pattern['pattern_name']}: {pattern['description']}")
    
    print("\n💡 Ollama実装のコツ:")
    tips = helper.get_ollama_tips()
    for tip in tips:
        print(f"  - {tip['title']}: {tip['content']}")
    
    print("\n🔧 Ollama最適化プロンプト生成...")
    prompt = helper.generate_password_manager_prompt()
    
    # プロンプトをファイルに保存
    with open("ollama_mcp_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)
    
    print("✅ ollama_mcp_prompt.txt に最適化プロンプトを保存しました")