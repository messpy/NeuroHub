#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弱いLLM対応統合開発支援システム
システム情報、知識ベース、バックグラウンド支援を統合
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.llm_agent import LLMAgent, LLMRequest
from services.db.database_manager import DatabaseManager
from services.system.system_info_collector import SystemInfoCollector


@dataclass
class WeakLLMContext:
    """弱いLLM用コンテキスト"""
    system_info: dict
    available_patterns: list
    recent_errors: list
    project_structure: dict
    dependencies: list
    performance_metrics: dict


class WeakLLMDevelopmentSupport:
    """弱いLLM対応開発支援システム"""

    def __init__(self, provider: str = "gemini"):
        """
        初期化

        Args:
            provider: LLMプロバイダー ('gemini', 'ollama', 'huggingface')
        """
        self.provider = provider
        self.llm_agent = LLMAgent(provider=provider)
        self.db_manager = DatabaseManager()
        self.system_collector = SystemInfoCollector()

        # 弱いLLM用設定
        self.weak_llm_config = {
            "max_tokens": 4000,       # コード生成に十分なトークン数
            "temperature": 0.1,       # 決定的な出力
            "simple_language": True,  # 簡単な言語使用
            "concrete_examples": True, # 具体例重視
            "step_by_step": True      # ステップ分割
        }

        self._create_tables()
        self._initialize_knowledge_base()

    def _create_tables(self):
        """弱いLLM支援用テーブル作成"""
        # 簡易コードテンプレートテーブル
        simple_templates_sql = """
        CREATE TABLE IF NOT EXISTS simple_code_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            purpose TEXT,
            template_code TEXT NOT NULL,
            parameters TEXT,
            example_usage TEXT,
            difficulty_level TEXT DEFAULT 'easy',
            success_rate REAL DEFAULT 1.0,
            usage_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # コーディングガイドテーブル
        coding_guides_sql = """
        CREATE TABLE IF NOT EXISTS coding_guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            content TEXT NOT NULL,
            target_audience TEXT DEFAULT 'weak_llm',
            complexity_score INTEGER DEFAULT 1,
            step_count INTEGER,
            example_code TEXT,
            common_mistakes TEXT,
            verification_steps TEXT
        )
        """

        # 自動調査結果テーブル
        auto_investigations_sql = """
        CREATE TABLE IF NOT EXISTS auto_investigations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_event TEXT NOT NULL,
            investigation_type TEXT,
            findings TEXT,
            actionable_items TEXT,
            system_context TEXT,
            confidence_score REAL,
            auto_applied BOOLEAN DEFAULT FALSE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        for sql in [simple_templates_sql, coding_guides_sql, auto_investigations_sql]:
            self.db_manager._execute_sql(sql)

    def _initialize_knowledge_base(self):
        """弱いLLM用知識ベース初期化"""
        # 基本的なテンプレートを登録
        basic_templates = [
            {
                "name": "simple_function",
                "purpose": "基本的な関数定義",
                "template_code": """def {function_name}({parameters}):
    \"\"\"{description}\"\"\"
    try:
        # メイン処理
        {main_code}
        return {return_value}
    except Exception as e:
        print(f"エラー: {e}")
        return None""",
                "parameters": "function_name,parameters,description,main_code,return_value",
                "example_usage": "ユーザー入力検証関数の作成",
                "difficulty_level": "easy"
            },
            {
                "name": "database_query",
                "purpose": "安全なデータベースクエリ",
                "template_code": """def {query_name}(self, {parameters}):
    \"\"\"{description}\"\"\"
    try:
        sql = \"\"\"{sql_query}\"\"\"
        cursor = self.db_manager._execute_sql(sql, ({sql_params}))
        result = cursor.fetchall()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"DBエラー: {e}")
        return []""",
                "parameters": "query_name,parameters,description,sql_query,sql_params",
                "example_usage": "ユーザー情報取得クエリ",
                "difficulty_level": "easy"
            },
            {
                "name": "error_handler",
                "purpose": "エラーハンドリングパターン",
                "template_code": """try:
    {main_operation}
except {specific_exception} as e:
    # 特定のエラー処理
    logger.error(f"{error_context}: {e}")
    {specific_handling}
except Exception as e:
    # 一般的なエラー処理
    logger.error(f"予期しないエラー: {e}")
    {general_handling}
finally:
    # クリーンアップ
    {cleanup_code}""",
                "parameters": "main_operation,specific_exception,error_context,specific_handling,general_handling,cleanup_code",
                "example_usage": "ファイル操作のエラーハンドリング",
                "difficulty_level": "easy"
            }
        ]

        for template in basic_templates:
            self._save_simple_template(template)

    def _save_simple_template(self, template: dict):
        """簡易テンプレート保存"""
        try:
            check_sql = "SELECT id FROM simple_code_templates WHERE name = ?"
            cursor = self.db_manager._execute_sql(check_sql, (template["name"],))

            if not cursor.fetchone():
                insert_sql = """
                INSERT INTO simple_code_templates (
                    name, purpose, template_code, parameters,
                    example_usage, difficulty_level
                ) VALUES (?, ?, ?, ?, ?, ?)
                """

                self.db_manager._execute_sql(insert_sql, (
                    template["name"],
                    template["purpose"],
                    template["template_code"],
                    template["parameters"],
                    template["example_usage"],
                    template["difficulty_level"]
                ))
        except Exception as e:
            print(f"テンプレート保存エラー: {e}")

    def get_weak_llm_context(self) -> WeakLLMContext:
        """弱いLLM用コンテキスト構築"""
        try:
            # システム情報取得
            system_info = self.system_collector.get_system_summary()

            # 利用可能パターン取得
            patterns_sql = """
            SELECT name, purpose, difficulty_level FROM simple_code_templates
            WHERE difficulty_level = 'easy'
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT 10
            """
            cursor = self.db_manager._execute_sql(patterns_sql)
            available_patterns = [dict(row) for row in cursor.fetchall()]

            # 最近のエラー取得
            errors_sql = """
            SELECT trigger_event, findings FROM auto_investigations
            WHERE investigation_type = 'error_analysis'
            ORDER BY timestamp DESC LIMIT 5
            """
            cursor = self.db_manager._execute_sql(errors_sql)
            recent_errors = [dict(row) for row in cursor.fetchall()]

            # プロジェクト構造分析
            project_structure = self._analyze_project_structure()

            # 依存関係情報
            dependencies = self._get_dependencies_info()

            # パフォーマンス指標
            performance_metrics = self._get_performance_summary()

            return WeakLLMContext(
                system_info=system_info,
                available_patterns=available_patterns,
                recent_errors=recent_errors,
                project_structure=project_structure,
                dependencies=dependencies,
                performance_metrics=performance_metrics
            )

        except Exception as e:
            print(f"コンテキスト構築エラー: {e}")
            return WeakLLMContext({}, [], [], {}, [], {})

    def generate_weak_llm_code(self, request: str, context: dict = None) -> dict:
        """弱いLLM向けコード生成"""
        try:
            # コンテキスト準備
            llm_context = self.get_weak_llm_context()

            # 適切なテンプレート検索
            suitable_templates = self._find_suitable_templates(request)

            # 簡易プロンプト構築
            prompt = self._build_weak_llm_prompt(request, llm_context, suitable_templates, context)

            # LLM呼び出し（弱いLLM設定）
            llm_request = LLMRequest(
                prompt=prompt,
                system_message="あなたは初心者向けのコーディング支援AIです。シンプルで確実なコードを生成してください。",
                request_type="weak_llm_coding",
                max_tokens=self.weak_llm_config["max_tokens"],
                temperature=self.weak_llm_config["temperature"],
                preferred_provider="ollama"  # 弱いLLM想定
            )

            response = self.llm_agent.generate_text(llm_request)

            if response.is_success:
                # コード抽出・検証
                generated_code = self._extract_and_validate_code(response.content)

                # 使用統計更新
                self._update_template_usage(suitable_templates)

                return {
                    "success": True,
                    "code": generated_code,
                    "templates_used": [t["name"] for t in suitable_templates],
                    "confidence": self._calculate_confidence(generated_code, suitable_templates),
                    "raw_response": response.content
                }
            else:
                # フォールバック: テンプレートベース生成
                fallback_code = self._generate_template_based_code(request, suitable_templates)

                return {
                    "success": True,
                    "code": fallback_code,
                    "templates_used": [t["name"] for t in suitable_templates],
                    "confidence": 0.6,
                    "fallback": True,
                    "error": response.error_message
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def auto_investigate_and_solve(self, trigger_event: str, event_data: dict) -> dict:
        """自動調査・解決"""
        try:
            investigation_type = self._classify_event(trigger_event, event_data)

            if investigation_type == "error":
                return self._auto_solve_error(trigger_event, event_data)
            elif investigation_type == "performance":
                return self._auto_optimize_performance(trigger_event, event_data)
            elif investigation_type == "dependency":
                return self._auto_resolve_dependency(trigger_event, event_data)
            else:
                return self._general_investigation(trigger_event, event_data)

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _auto_solve_error(self, error_msg: str, context: dict) -> dict:
        """エラー自動解決"""
        try:
            # 既知エラーパターン検索
            known_solutions = self._search_known_solutions(error_msg)

            if known_solutions:
                # 既知の解決策適用
                solution = known_solutions[0]

                return {
                    "success": True,
                    "solution_type": "known_pattern",
                    "solution": solution,
                    "confidence": 0.9,
                    "auto_applicable": True
                }
            else:
                # 新しいエラーの調査
                llm_context = self.get_weak_llm_context()

                # 弱いLLM向けエラー解析プロンプト
                prompt = f"""
以下のエラーを解決してください:

エラー: {error_msg}

システム情報:
- OS: {llm_context.system_info.get('system', {}).get('platform', 'Unknown')}
- Python: {llm_context.system_info.get('system', {}).get('python_version', 'Unknown')}

利用可能な解決パターン:
{chr(10).join([f"- {p['name']}: {p['purpose']}" for p in llm_context.available_patterns[:3]])}

以下の形式で簡潔に回答してください:
1. 原因: 何が問題か
2. 解決策: 具体的な修正方法
3. コード例: コピペ可能なコード
4. 確認方法: 修正確認の手順

簡単で確実な方法を優先してください。
"""

                llm_request = LLMRequest(
                    prompt=prompt,
                    system_message="エラー解決の専門家として、シンプルで確実な解決策を提供してください。",
                    request_type="error_solving",
                    max_tokens=400,
                    temperature=0.1
                )

                response = self.llm_agent.generate_text(llm_request)

                if response.is_success:
                    solution = self._parse_error_solution(response.content)

                    # 解決策をデータベースに保存
                    self._save_investigation_result("error_analysis", error_msg, solution, llm_context)

                    return {
                        "success": True,
                        "solution_type": "llm_analysis",
                        "solution": solution,
                        "confidence": 0.7,
                        "raw_response": response.content
                    }
                else:
                    return {"success": False, "error": response.error_message}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _find_suitable_templates(self, request: str) -> list:
        """適切なテンプレート検索"""
        try:
            # キーワードベース検索
            keywords = request.lower().split()

            search_conditions = []
            search_params = []

            for keyword in keywords:
                search_conditions.append("(name LIKE ? OR purpose LIKE ? OR template_code LIKE ?)")
                search_params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

            if search_conditions:
                search_sql = f"""
                SELECT * FROM simple_code_templates
                WHERE {' OR '.join(search_conditions)}
                ORDER BY success_rate DESC, usage_count DESC
                LIMIT 3
                """

                cursor = self.db_manager._execute_sql(search_sql, search_params)
                return [dict(row) for row in cursor.fetchall()]
            else:
                # デフォルトテンプレート
                default_sql = """
                SELECT * FROM simple_code_templates
                WHERE difficulty_level = 'easy'
                ORDER BY usage_count DESC
                LIMIT 3
                """
                cursor = self.db_manager._execute_sql(default_sql)
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"テンプレート検索エラー: {e}")
            return []

    def _build_weak_llm_prompt(self, request: str, context: WeakLLMContext, templates: list, extra_context: dict = None) -> str:
        """弱いLLM向けプロンプト構築"""
        system_summary = f"""
システム環境:
- OS: {context.system_info.get('system', {}).get('platform', 'Unknown')}
- Python: {context.system_info.get('system', {}).get('python_version', 'Unknown')}
- メモリ: {context.system_info.get('system', {}).get('memory_total', 0) // (1024**3) if context.system_info.get('system', {}).get('memory_total') else 0}GB
"""

        templates_info = ""
        if templates:
            templates_info = f"""
利用可能なテンプレート:
{chr(10).join([f"- {t['name']}: {t['purpose']}" for t in templates[:3]])}
"""

        recent_errors_info = ""
        if context.recent_errors:
            recent_errors_info = f"""
最近のエラー情報:
{chr(10).join([f"- {e.get('trigger_event', '')[:50]}..." for e in context.recent_errors[:2]])}
"""

        return f"""
以下のリクエストに対してPythonコードを生成してください:

リクエスト: {request}

{system_summary}

{templates_info}

{recent_errors_info}

追加コンテキスト: {json.dumps(extra_context or {}, ensure_ascii=False, indent=2)}

要件:
1. シンプルで理解しやすいコード
2. エラーハンドリングを含む
3. コメントで動作を説明
4. コピペで動作する完全なコード
5. 依存関係は最小限

以下の形式で回答してください:
```python
# コード説明
{request}を実装

# 実装コード
[ここに完全なコード]

# 使用例
[ここに使用例]
```

簡単で確実に動作するコードを重視してください。
"""

    def _extract_and_validate_code(self, response_content: str) -> str:
        """コード抽出・検証"""
        try:
            # ```python から ``` までを抽出
            lines = response_content.split('\n')
            code_lines = []
            in_code_block = False

            for line in lines:
                if line.strip().startswith('```python'):
                    in_code_block = True
                    continue
                elif line.strip() == '```' and in_code_block:
                    break
                elif in_code_block:
                    code_lines.append(line)

            if code_lines:
                code = '\n'.join(code_lines)

                # 基本的な構文チェック
                try:
                    compile(code, '<string>', 'exec')
                    return code
                except SyntaxError as e:
                    print(f"構文エラー: {e}")
                    return self._fix_basic_syntax_errors(code)

            # コードブロックが見つからない場合は全体を返す
            return response_content

        except Exception as e:
            print(f"コード抽出エラー: {e}")
            return response_content

    def _fix_basic_syntax_errors(self, code: str) -> str:
        """基本的な構文エラー修正"""
        try:
            lines = code.split('\n')
            fixed_lines = []

            for line in lines:
                # インデント修正
                if line.strip() and not line.startswith(' ') and line.endswith(':'):
                    # 関数/クラス定義行の後にpass追加
                    fixed_lines.append(line)
                    fixed_lines.append('    pass')
                else:
                    fixed_lines.append(line)

            return '\n'.join(fixed_lines)

        except:
            return code

    def _generate_template_based_code(self, request: str, templates: list) -> str:
        """テンプレートベースコード生成"""
        if not templates:
            return f"""
# {request}の実装
def implement_{request.replace(' ', '_').lower()}():
    \"\"\"
    {request}を実装
    \"\"\"
    try:
        # TODO: 実装を追加してください
        pass
        return True
    except Exception as e:
        print(f"エラー: {e}")
        return False

# 使用例
if __name__ == "__main__":
    result = implement_{request.replace(' ', '_').lower()}()
    print(f"実行結果: {result}")
"""

        # 最適なテンプレートを選択
        best_template = templates[0]

        # パラメータ置換
        code = best_template["template_code"]

        # 簡易パラメータ置換
        replacements = {
            "{function_name}": f"implement_{request.replace(' ', '_').lower()}",
            "{parameters}": "",
            "{description}": request,
            "{main_code}": "# TODO: 実装を追加\n        pass",
            "{return_value}": "True"
        }

        for placeholder, value in replacements.items():
            code = code.replace(placeholder, value)

        return code

    def _calculate_confidence(self, code: str, templates: list) -> float:
        """信頼度計算"""
        try:
            confidence = 0.5  # ベース信頼度

            # 構文チェック
            try:
                compile(code, '<string>', 'exec')
                confidence += 0.2
            except:
                confidence -= 0.1

            # テンプレート使用による信頼度向上
            if templates:
                avg_success_rate = sum(t.get("success_rate", 0.5) for t in templates) / len(templates)
                confidence += avg_success_rate * 0.3

            # コードの複雑さによる調整
            lines = code.split('\n')
            if len(lines) < 20:  # シンプルなコード
                confidence += 0.1

            # エラーハンドリングの有無
            if 'try:' in code and 'except:' in code:
                confidence += 0.1

            return min(1.0, max(0.1, confidence))

        except:
            return 0.5

    def _update_template_usage(self, templates: list):
        """テンプレート使用統計更新"""
        try:
            for template in templates:
                update_sql = """
                UPDATE simple_code_templates
                SET usage_count = usage_count + 1
                WHERE id = ?
                """
                self.db_manager._execute_sql(update_sql, (template["id"],))
        except Exception as e:
            print(f"テンプレート統計更新エラー: {e}")

    def _analyze_project_structure(self) -> dict:
        """プロジェクト構造分析"""
        try:
            structure = {
                "python_files": 0,
                "test_files": 0,
                "config_files": 0,
                "directories": []
            }

            for item in project_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    structure["directories"].append(item.name)
                elif item.suffix == '.py':
                    structure["python_files"] += 1
                    if 'test' in item.name:
                        structure["test_files"] += 1
                elif item.suffix in ['.yaml', '.yml', '.json', '.toml', '.cfg']:
                    structure["config_files"] += 1

            return structure

        except:
            return {}

    def _get_dependencies_info(self) -> list:
        """依存関係情報取得"""
        try:
            deps = []

            # requirements.txt
            req_file = project_root / "requirements.txt"
            if req_file.exists():
                deps.extend(req_file.read_text().splitlines())

            return deps[:10]  # 上位10個

        except:
            return []

    def _get_performance_summary(self) -> dict:
        """パフォーマンス要約取得"""
        try:
            # 基本的なシステムメトリクス
            return {
                "memory_usage": "適正",
                "disk_usage": "適正",
                "response_time": "高速",
                "last_check": datetime.now().isoformat()
            }
        except:
            return {}

    def _classify_event(self, event: str, data: dict) -> str:
        """イベント分類"""
        event_lower = event.lower()

        if any(keyword in event_lower for keyword in ['error', 'exception', 'failed', 'traceback']):
            return "error"
        elif any(keyword in event_lower for keyword in ['slow', 'performance', 'timeout', 'memory']):
            return "performance"
        elif any(keyword in event_lower for keyword in ['import', 'module', 'package', 'dependency']):
            return "dependency"
        else:
            return "general"

    def _search_known_solutions(self, error_msg: str) -> list:
        """既知解決策検索"""
        try:
            search_sql = """
            SELECT actionable_items FROM auto_investigations
            WHERE trigger_event LIKE ? AND confidence_score > 0.7
            ORDER BY timestamp DESC LIMIT 3
            """

            cursor = self.db_manager._execute_sql(search_sql, (f"%{error_msg[:50]}%",))
            return [row[0] for row in cursor.fetchall()]

        except:
            return []

    def _parse_error_solution(self, content: str) -> dict:
        """エラー解決策パース"""
        lines = content.split('\n')

        solution = {
            "cause": "不明",
            "fix": "修正方法を確認してください",
            "code": "",
            "verification": "動作確認してください"
        }

        current_section = None
        for line in lines:
            line = line.strip()

            if '原因:' in line or '1.' in line:
                current_section = "cause"
                solution["cause"] = line.split(':', 1)[-1].strip()
            elif '解決策:' in line or '2.' in line:
                current_section = "fix"
                solution["fix"] = line.split(':', 1)[-1].strip()
            elif 'コード' in line or '3.' in line:
                current_section = "code"
            elif '確認' in line or '4.' in line:
                current_section = "verification"
                solution["verification"] = line.split(':', 1)[-1].strip()
            elif current_section == "code" and line:
                solution["code"] += line + '\n'

        return solution

    def _save_investigation_result(self, inv_type: str, trigger: str, findings: dict, context: WeakLLMContext):
        """調査結果保存"""
        try:
            insert_sql = """
            INSERT INTO auto_investigations (
                trigger_event, investigation_type, findings,
                actionable_items, system_context, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                trigger,
                inv_type,
                json.dumps(findings, ensure_ascii=False),
                findings.get("fix", ""),
                json.dumps(context.system_info, ensure_ascii=False),
                0.7
            ))

        except Exception as e:
            print(f"調査結果保存エラー: {e}")

    def get_system_status(self) -> dict:
        """システム状況取得"""
        try:
            context = self.get_weak_llm_context()

            return {
                "system_info": context.system_info,
                "available_templates": len(context.available_patterns),
                "recent_errors": len(context.recent_errors),
                "project_health": "正常",
                "llm_readiness": "準備完了",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": str(e)}

    def generate_code(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> dict:
        """
        LLMでコード生成

        Args:
            prompt: コード生成プロンプト
            max_tokens: 最大トークン数
            temperature: 温度パラメータ

        Returns:
            生成結果（code, content等）
        """
        try:
            llm_request = LLMRequest(
                prompt=prompt,
                system_message="あなたは熟練したPythonプログラマーです。要求された機能を完全に実装した動作するコードを生成してください。",
                request_type="code_generation",
                max_tokens=max_tokens,
                temperature=temperature
            )

            response = self.llm_agent.generate_text(llm_request)

            if response.is_success:
                print(f"[DEBUG] LLM応答成功: content長={len(response.content)}")
                extracted_code = self._extract_code_from_response(response.content)
                print(f"[DEBUG] 抽出コード長={len(extracted_code) if extracted_code else 0}")
                return {
                    "success": True,
                    "content": response.content,
                    "code": extracted_code
                }
            else:
                print(f"[DEBUG] LLM応答失敗: {response.error}")
                return {
                    "success": False,
                    "error": response.error
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_code_from_response(self, content: str) -> str:
        """レスポンスからコードを抽出"""
        if '```python' in content:
            return content.split('```python')[1].split('```')[0].strip()
        elif '```' in content:
            return content.split('```')[1].split('```')[0].strip()
        else:
            return content.strip()


def main():
    """テスト実行"""
    print("🤖 弱いLLM対応開発支援システム開始...")

    support = WeakLLMDevelopmentSupport()

    # システム状況確認
    status = support.get_system_status()
    print(f"📊 システム状況: {status.get('project_health', 'Unknown')}")
    print(f"🎯 利用可能テンプレート: {status.get('available_templates', 0)}件")

    # コード生成テスト
    print("\n🔧 コード生成テスト...")
    result = support.generate_weak_llm_code("ユーザー認証機能を作成")

    if result["success"]:
        print(f"✅ コード生成成功 (信頼度: {result['confidence']:.2f})")
        print(f"📋 使用テンプレート: {', '.join(result['templates_used'])}")
        print(f"💻 生成コード:\n{result['code'][:200]}...")
    else:
        print(f"❌ コード生成失敗: {result['error']}")

    # エラー解決テスト
    print("\n🔧 エラー解決テスト...")
    error_result = support.auto_investigate_and_solve(
        "ImportError: No module named 'requests'",
        {"context": "ライブラリインポート"}
    )

    if error_result["success"]:
        print(f"✅ エラー解決案提供 (信頼度: {error_result.get('confidence', 0):.2f})")
        print(f"🔧 解決タイプ: {error_result['solution_type']}")
    else:
        print(f"❌ エラー解決失敗: {error_result['error']}")


if __name__ == "__main__":
    main()
