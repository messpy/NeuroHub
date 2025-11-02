#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弱いLLM統合開発支援システム - テストスクリプト
システム情報収集、知識ベース構築、コーディング支援の統合テスト
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.llm_agent import LLMAgent
except ImportError:
    # LLMAgentが使用できない場合のダミークラス
    class LLMAgent:
        def __init__(self):
            pass
from services.db.database_manager import DatabaseManager


class WeakLLMIntegratedSupport:
    """弱いLLM統合開発支援システム"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.llm_agent = LLMAgent()
        self._create_knowledge_tables()
        self._initialize_basic_knowledge()

    def _create_knowledge_tables(self):
        """知識ベーステーブル作成"""
        # 基本コーディングパターンテーブル
        patterns_sql = """
        CREATE TABLE IF NOT EXISTS weak_llm_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            code_template TEXT,
            parameters TEXT,
            example TEXT,
            difficulty INTEGER DEFAULT 1,
            success_rate REAL DEFAULT 1.0,
            usage_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # エラー解決パターンテーブル
        error_solutions_sql = """
        CREATE TABLE IF NOT EXISTS error_solutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_pattern TEXT NOT NULL,
            error_type TEXT,
            solution_steps TEXT,
            code_fix TEXT,
            prevention_tips TEXT,
            confidence REAL DEFAULT 0.8,
            tested BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # システム知識テーブル
        system_knowledge_sql = """
        CREATE TABLE IF NOT EXISTS system_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            category TEXT,
            content TEXT,
            tags TEXT,
            source TEXT,
            confidence REAL DEFAULT 0.9,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        for sql in [patterns_sql, error_solutions_sql, system_knowledge_sql]:
            self.db_manager._execute_sql(sql)

    def _initialize_basic_knowledge(self):
        """基本知識初期化"""
        # 基本パターン登録
        basic_patterns = [
            {
                "name": "simple_function",
                "category": "function",
                "description": "基本的な関数テンプレート",
                "code_template": '''def {function_name}({params}):
    """
    {description}

    Args:
        {params}: パラメータ説明

    Returns:
        {return_type}: 戻り値説明
    """
    try:
        # メイン処理
        {main_code}
        return {return_value}
    except Exception as e:
        print(f"エラー: {e}")
        return None''',
                "parameters": "function_name,params,description,main_code,return_value,return_type",
                "example": "ファイル読み込み関数"
            },
            {
                "name": "class_template",
                "category": "class",
                "description": "基本的なクラステンプレート",
                "code_template": '''class {class_name}:
    """
    {description}
    """

    def __init__(self, {init_params}):
        """初期化"""
        {init_code}

    def {method_name}(self, {method_params}):
        """
        {method_description}
        """
        try:
            {method_code}
            return True
        except Exception as e:
            print(f"エラー: {e}")
            return False''',
                "parameters": "class_name,description,init_params,init_code,method_name,method_params,method_description,method_code",
                "example": "データ管理クラス"
            },
            {
                "name": "database_query",
                "category": "database",
                "description": "安全なデータベースクエリ",
                "code_template": '''def {query_name}(self, {params}):
    """
    {description}
    """
    try:
        sql = """{sql_query}"""
        cursor = self.db_manager._execute_sql(sql, ({sql_params}))
        {result_processing}
        return result
    except Exception as e:
        print(f"データベースエラー: {e}")
        return {error_return}''',
                "parameters": "query_name,params,description,sql_query,sql_params,result_processing,error_return",
                "example": "ユーザー情報取得"
            }
        ]

        for pattern in basic_patterns:
            self._save_pattern(pattern)

        # 基本エラー解決策
        error_solutions = [
            {
                "error_pattern": "ImportError",
                "error_type": "import",
                "solution_steps": json.dumps([
                    "1. 必要なパッケージをインストール: pip install パッケージ名",
                    "2. 仮想環境を確認: venv\\Scripts\\activate",
                    "3. パッケージ名のスペルチェック",
                    "4. Pythonパスの確認"
                ]),
                "code_fix": '''# パッケージインストール確認
import subprocess
import sys

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import {package_name}
except ImportError:
    print("パッケージをインストール中...")
    install_package("{package_name}")
    import {package_name}''',
                "prevention_tips": "requirements.txtで依存関係管理"
            },
            {
                "error_pattern": "FileNotFoundError",
                "error_type": "file",
                "solution_steps": json.dumps([
                    "1. ファイルパスの確認",
                    "2. ファイルの存在確認",
                    "3. 権限の確認",
                    "4. 相対パス vs 絶対パスの確認"
                ]),
                "code_fix": '''from pathlib import Path

def safe_file_operation(file_path):
    """安全なファイル操作"""
    path = Path(file_path)

    if not path.exists():
        print(f"ファイルが存在しません: {file_path}")
        return None

    if not path.is_file():
        print(f"ファイルではありません: {file_path}")
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")
        return None''',
                "prevention_tips": "pathlib使用、存在確認、例外処理"
            }
        ]

        for solution in error_solutions:
            self._save_error_solution(solution)

        # システム知識
        system_knowledge = [
            {
                "topic": "Python基本構文",
                "category": "python",
                "content": json.dumps({
                    "variables": "変数 = 値",
                    "functions": "def 関数名(引数): return 戻り値",
                    "classes": "class クラス名: def __init__(self): pass",
                    "loops": "for item in list: / while condition:",
                    "conditions": "if condition: elif condition: else:",
                    "exceptions": "try: except Exception as e: finally:"
                }),
                "tags": "python,syntax,basic"
            },
            {
                "topic": "データベース操作",
                "category": "database",
                "content": json.dumps({
                    "select": "SELECT * FROM table WHERE condition",
                    "insert": "INSERT INTO table (col1, col2) VALUES (?, ?)",
                    "update": "UPDATE table SET col1 = ? WHERE condition",
                    "delete": "DELETE FROM table WHERE condition",
                    "join": "SELECT * FROM table1 JOIN table2 ON table1.id = table2.id",
                    "safety": "常にパラメータ化クエリを使用"
                }),
                "tags": "database,sql,crud"
            },
            {
                "topic": "エラーハンドリング",
                "category": "error_handling",
                "content": json.dumps({
                    "basic": "try-except-finally構文",
                    "specific": "特定の例外をキャッチ: except ValueError:",
                    "logging": "import logging; logging.error(message)",
                    "reraise": "例外の再発生: raise",
                    "custom": "カスタム例外: class MyError(Exception): pass",
                    "best_practices": "具体的な例外処理、ログ記録、適切なクリーンアップ"
                }),
                "tags": "error,exception,handling,debugging"
            }
        ]

        for knowledge in system_knowledge:
            self._save_system_knowledge(knowledge)

    def _save_pattern(self, pattern):
        """パターン保存"""
        try:
            check_sql = "SELECT id FROM weak_llm_patterns WHERE name = ?"
            cursor = self.db_manager._execute_sql(check_sql, (pattern["name"],))

            if not cursor.fetchone():
                insert_sql = """
                INSERT INTO weak_llm_patterns (
                    name, category, description, code_template, parameters, example
                ) VALUES (?, ?, ?, ?, ?, ?)
                """

                self.db_manager._execute_sql(insert_sql, (
                    pattern["name"],
                    pattern["category"],
                    pattern["description"],
                    pattern["code_template"],
                    pattern["parameters"],
                    pattern["example"]
                ))
        except Exception as e:
            print(f"パターン保存エラー: {e}")

    def _save_error_solution(self, solution):
        """エラー解決策保存"""
        try:
            check_sql = "SELECT id FROM error_solutions WHERE error_pattern = ?"
            cursor = self.db_manager._execute_sql(check_sql, (solution["error_pattern"],))

            if not cursor.fetchone():
                insert_sql = """
                INSERT INTO error_solutions (
                    error_pattern, error_type, solution_steps, code_fix, prevention_tips
                ) VALUES (?, ?, ?, ?, ?)
                """

                self.db_manager._execute_sql(insert_sql, (
                    solution["error_pattern"],
                    solution["error_type"],
                    solution["solution_steps"],
                    solution["code_fix"],
                    solution["prevention_tips"]
                ))
        except Exception as e:
            print(f"エラー解決策保存エラー: {e}")

    def _save_system_knowledge(self, knowledge):
        """システム知識保存"""
        try:
            check_sql = "SELECT id FROM system_knowledge WHERE topic = ?"
            cursor = self.db_manager._execute_sql(check_sql, (knowledge["topic"],))

            if not cursor.fetchone():
                insert_sql = """
                INSERT INTO system_knowledge (
                    topic, category, content, tags, source
                ) VALUES (?, ?, ?, ?, ?)
                """

                self.db_manager._execute_sql(insert_sql, (
                    knowledge["topic"],
                    knowledge["category"],
                    knowledge["content"],
                    knowledge["tags"],
                    "initial_setup"
                ))
        except Exception as e:
            print(f"システム知識保存エラー: {e}")

    def generate_simple_code(self, request: str) -> dict:
        """簡単なコード生成"""
        try:
            # 適切なパターン検索
            patterns = self._find_patterns(request)

            if patterns:
                # テンプレートベース生成
                result = self._generate_from_template(request, patterns[0])

                # 使用統計更新
                self._update_pattern_usage(patterns[0]["id"])

                return {
                    "success": True,
                    "code": result["code"],
                    "explanation": result["explanation"],
                    "template_used": patterns[0]["name"],
                    "confidence": 0.9
                }
            else:
                # 基本的なコード生成
                basic_code = self._generate_basic_code(request)

                return {
                    "success": True,
                    "code": basic_code,
                    "explanation": f"{request}の基本実装",
                    "template_used": "basic",
                    "confidence": 0.6
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def solve_error(self, error_message: str) -> dict:
        """エラー解決"""
        try:
            # 既知エラーパターン検索
            solutions = self._find_error_solutions(error_message)

            if solutions:
                solution = solutions[0]

                return {
                    "success": True,
                    "error_type": solution["error_type"],
                    "steps": json.loads(solution["solution_steps"]),
                    "code_fix": solution["code_fix"],
                    "prevention": solution["prevention_tips"],
                    "confidence": solution["confidence"]
                }
            else:
                # 基本的なエラー解決ガイド
                basic_solution = self._generate_basic_error_solution(error_message)

                return {
                    "success": True,
                    "error_type": "unknown",
                    "steps": basic_solution["steps"],
                    "code_fix": basic_solution["code"],
                    "prevention": "適切なエラーハンドリングを実装",
                    "confidence": 0.5
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_knowledge(self, topic: str) -> dict:
        """知識検索"""
        try:
            search_sql = """
            SELECT * FROM system_knowledge
            WHERE topic LIKE ? OR content LIKE ? OR tags LIKE ?
            ORDER BY confidence DESC
            LIMIT 5
            """

            search_term = f"%{topic}%"
            cursor = self.db_manager._execute_sql(search_sql, (search_term, search_term, search_term))
            results = cursor.fetchall()

            if results:
                knowledge_items = []
                for row in results:
                    knowledge_items.append({
                        "topic": row[1],
                        "category": row[2],
                        "content": json.loads(row[3]) if row[3].startswith('{') else row[3],
                        "tags": row[4],
                        "confidence": row[6]
                    })

                return {
                    "success": True,
                    "knowledge": knowledge_items,
                    "count": len(knowledge_items)
                }
            else:
                return {
                    "success": False,
                    "message": "関連する知識が見つかりませんでした"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _find_patterns(self, request: str) -> list:
        """パターン検索"""
        try:
            keywords = request.lower().split()

            search_conditions = []
            search_params = []

            for keyword in keywords:
                search_conditions.append("(name LIKE ? OR description LIKE ? OR category LIKE ?)")
                search_params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

            if search_conditions:
                search_sql = f"""
                SELECT * FROM weak_llm_patterns
                WHERE {' OR '.join(search_conditions)}
                ORDER BY success_rate DESC, usage_count DESC
                LIMIT 3
                """

                cursor = self.db_manager._execute_sql(search_sql, search_params)
                return [dict(row) for row in cursor.fetchall()]

            return []

        except Exception as e:
            print(f"パターン検索エラー: {e}")
            return []

    def _find_error_solutions(self, error_message: str) -> list:
        """エラー解決策検索"""
        try:
            search_sql = """
            SELECT * FROM error_solutions
            WHERE ? LIKE '%' || error_pattern || '%'
            ORDER BY confidence DESC
            LIMIT 3
            """

            cursor = self.db_manager._execute_sql(search_sql, (error_message,))
            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"エラー解決策検索エラー: {e}")
            return []

    def _generate_from_template(self, request: str, pattern: dict) -> dict:
        """テンプレートからコード生成"""
        try:
            template = pattern["code_template"]

            # 簡易パラメータ置換
            replacements = self._extract_parameters(request, pattern)

            code = template
            for placeholder, value in replacements.items():
                code = code.replace(f"{{{placeholder}}}", value)

            return {
                "code": code,
                "explanation": f"{pattern['description']}を使用して{request}を実装"
            }

        except Exception as e:
            return {
                "code": f"# エラー: {e}\n# TODO: {request}を実装してください",
                "explanation": "テンプレート生成でエラーが発生しました"
            }

    def _extract_parameters(self, request: str, pattern: dict) -> dict:
        """パラメータ抽出"""
        # 簡易実装
        request_words = request.lower().split()

        replacements = {
            "function_name": f"handle_{request_words[0] if request_words else 'process'}",
            "class_name": f"{request_words[0].capitalize() if request_words else 'Handler'}Manager",
            "params": "data",
            "description": request,
            "main_code": "# TODO: メイン処理を実装\n        pass",
            "return_value": "True",
            "return_type": "bool",
            "init_params": "config=None",
            "init_code": "self.config = config or {}",
            "method_name": "process",
            "method_params": "data",
            "method_description": f"{request}を処理",
            "method_code": "# TODO: 処理を実装\n            pass",
            "query_name": "get_data",
            "sql_query": "SELECT * FROM table WHERE condition = ?",
            "sql_params": "condition_value",
            "result_processing": "result = cursor.fetchall()",
            "error_return": "[]"
        }

        return replacements

    def _generate_basic_code(self, request: str) -> str:
        """基本コード生成"""
        function_name = f"handle_{request.replace(' ', '_').lower()}"

        return f'''def {function_name}():
    """
    {request}を実装
    """
    try:
        # TODO: {request}の具体的な実装
        print("処理開始: {request}")

        # メイン処理
        result = None  # ここに処理結果を設定

        print("処理完了")
        return result

    except Exception as e:
        print(f"エラーが発生しました: {{e}}")
        return None

# 使用例
if __name__ == "__main__":
    result = {function_name}()
    print(f"実行結果: {{result}}")'''

    def _generate_basic_error_solution(self, error_message: str) -> dict:
        """基本エラー解決策生成"""
        steps = [
            "1. エラーメッセージを詳細に確認",
            "2. エラーが発生した行を特定",
            "3. 変数の値を確認",
            "4. 適切な例外処理を追加"
        ]

        code = '''try:
    # エラーが発生したコード
    pass
except Exception as e:
    print(f"エラー詳細: {e}")
    print(f"エラータイプ: {type(e).__name__}")
    # 適切な処理を追加'''

        return {
            "steps": steps,
            "code": code
        }

    def _update_pattern_usage(self, pattern_id: int):
        """パターン使用統計更新"""
        try:
            update_sql = """
            UPDATE weak_llm_patterns
            SET usage_count = usage_count + 1
            WHERE id = ?
            """
            self.db_manager._execute_sql(update_sql, (pattern_id,))
        except Exception as e:
            print(f"統計更新エラー: {e}")

    def get_system_status(self) -> dict:
        """システム状況取得"""
        try:
            # パターン数
            patterns_sql = "SELECT COUNT(*) FROM weak_llm_patterns"
            cursor = self.db_manager._execute_sql(patterns_sql)
            pattern_count = cursor.fetchone()[0]

            # エラー解決策数
            solutions_sql = "SELECT COUNT(*) FROM error_solutions"
            cursor = self.db_manager._execute_sql(solutions_sql)
            solution_count = cursor.fetchone()[0]

            # 知識数
            knowledge_sql = "SELECT COUNT(*) FROM system_knowledge"
            cursor = self.db_manager._execute_sql(knowledge_sql)
            knowledge_count = cursor.fetchone()[0]

            return {
                "status": "正常",
                "patterns": pattern_count,
                "solutions": solution_count,
                "knowledge": knowledge_count,
                "ready": True,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "エラー",
                "error": str(e),
                "ready": False
            }


def main():
    """メイン実行・テスト"""
    print("🤖 弱いLLM統合開発支援システム - テスト実行")
    print("=" * 60)

    # システム初期化
    support = WeakLLMIntegratedSupport()

    # システム状況確認
    status = support.get_system_status()
    print(f"📊 システム状況: {status['status']}")
    print(f"📦 コードパターン: {status['patterns']}件")
    print(f"🔧 エラー解決策: {status['solutions']}件")
    print(f"📚 知識ベース: {status['knowledge']}件")
    print()

    # コード生成テスト
    print("🔧 コード生成テスト...")
    requests = [
        "ユーザー認証機能",
        "ファイル読み込み",
        "データベース検索",
        "エラーログ記録"
    ]

    for request in requests:
        result = support.generate_simple_code(request)
        if result["success"]:
            print(f"✅ {request}: {result['template_used']}テンプレート使用 (信頼度: {result['confidence']:.1f})")
        else:
            print(f"❌ {request}: {result['error']}")
    print()

    # エラー解決テスト
    print("🔧 エラー解決テスト...")
    errors = [
        "ImportError: No module named 'requests'",
        "FileNotFoundError: [Errno 2] No such file or directory",
        "AttributeError: 'NoneType' object has no attribute 'split'",
        "SyntaxError: invalid syntax"
    ]

    for error in errors:
        result = support.solve_error(error)
        if result["success"]:
            print(f"✅ {error[:30]}...: {result['error_type']}タイプ (信頼度: {result['confidence']:.1f})")
        else:
            print(f"❌ {error[:30]}...: {result['error']}")
    print()

    # 知識検索テスト
    print("🔧 知識検索テスト...")
    topics = [
        "Python基本",
        "データベース",
        "エラーハンドリング",
        "ファイル操作"
    ]

    for topic in topics:
        result = support.get_knowledge(topic)
        if result["success"]:
            print(f"✅ {topic}: {result['count']}件の知識を発見")
        else:
            print(f"❌ {topic}: {result.get('message', result.get('error', 'Unknown'))}")
    print()

    # 詳細テスト例
    print("🎯 詳細テスト例...")
    code_result = support.generate_simple_code("ユーザーパスワード検証")
    if code_result["success"]:
        print("生成されたコード:")
        print("-" * 40)
        print(code_result["code"][:300] + "...")
        print("-" * 40)

    error_result = support.solve_error("ImportError: No module named 'pandas'")
    if error_result["success"]:
        print("エラー解決手順:")
        for i, step in enumerate(error_result["steps"], 1):
            print(f"  {step}")

    print()
    print("🎉 テスト完了!")
    print(f"💾 データベース: {Path(support.db_manager.db_path).absolute()}")


if __name__ == "__main__":
    main()
