#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP自動デバッグ・最適化システム
生成されたコードを自動テスト、エラー検出、修正を繰り返す
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.llm_agent import LLMAgent, LLMRequest
from services.db.database_manager import DatabaseManager
from services.web.practical_web_searcher import PracticalWebSearcher


@dataclass
class DebugResult:
    """デバッグ結果"""
    success: bool
    error_message: Optional[str]
    fix_applied: bool
    iterations: int
    final_code: str
    execution_output: str


class AutoDebugger:
    """自動デバッグシステム"""

    def __init__(self, provider: str = "ollama"):
        self.provider = provider
        self.llm_agent = LLMAgent(provider=provider)
        self.db_manager = DatabaseManager()
        self.web_searcher = PracticalWebSearcher()
        self.max_iterations = 20  # 最大試行回数を大幅に増加
        self.continuous_mode = True  # エラーが解決されるまで継続

        self._create_debug_tables()

    def _create_debug_tables(self):
        """デバッグ用テーブル作成"""
        sql = """
        CREATE TABLE IF NOT EXISTS debug_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            error_type TEXT,
            error_message TEXT,
            fix_prompt TEXT,
            fix_code TEXT,
            success BOOLEAN,
            iterations INTEGER,
            provider TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db_manager._execute_sql(sql)

        sql2 = """
        CREATE TABLE IF NOT EXISTS successful_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_description TEXT,
            prompt_template TEXT,
            generated_code TEXT,
            success_rate REAL DEFAULT 1.0,
            usage_count INTEGER DEFAULT 1,
            provider TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db_manager._execute_sql(sql2)

    def test_and_fix_code(self, code_file: Path, project_name: str) -> DebugResult:
        """
        コードを自動テスト＆修正（エラーが解決されるまで継続）

        Args:
            code_file: テスト対象のPythonファイル
            project_name: プロジェクト名

        Returns:
            デバッグ結果
        """
        print(f"🔍 自動デバッグ開始: {project_name}")
        print(f"⚙️ 連続モード: エラーが解決されるまで最大{self.max_iterations}回試行")

        current_code = code_file.read_text(encoding='utf-8')
        iterations = 0
        last_error = None
        consecutive_failures = 0  # 連続失敗カウント

        for i in range(self.max_iterations):
            iterations += 1
            print(f"\n🔄 デバッグ試行 {iterations}/{self.max_iterations}")

            # コード実行テスト
            success, error_msg, output = self._execute_code(code_file)

            if success:
                print(f"✅ デバッグ成功！（{iterations}回の試行）")
                self._save_success_pattern(project_name, current_code)
                return DebugResult(
                    success=True,
                    error_message=None,
                    fix_applied=iterations > 1,
                    iterations=iterations,
                    final_code=current_code,
                    execution_output=output
                )

            print(f"❌ エラー検出: {error_msg[:200]}...")

            # 同じエラーが繰り返されているかチェック
            if error_msg == last_error:
                consecutive_failures += 1
                print(f"⚠️ 同じエラーが{consecutive_failures}回連続発生")

                # 5回連続で同じエラーなら終了
                if consecutive_failures >= 5:
                    print(f"\n{'='*60}")
                    print(f"❌ デバッグ中止: 同じエラーが5回連続発生しました")
                    print(f"📝 エラー内容: {error_msg[:200]}...")
                    print(f"💡 ヒント: Web検索、DB、サンプルコードを確認してください")
                    print(f"{'='*60}")
                    self._save_debug_history(project_name, error_msg, False, iterations)
                    return DebugResult(
                        success=False,
                        error_message=error_msg,
                        fix_applied=True,
                        iterations=iterations,
                        final_code=current_code,
                        execution_output=output
                    )

                # 3回連続で同じエラーなら、より詳細な分析を実施
                if consecutive_failures >= 3:
                    print(f"🔍 詳細エラー分析モードに切り替え")
                    # より多くのヒントを収集
                    hints = self._get_detailed_fix_hints(error_msg, project_name, current_code)
                else:
                    hints = self._get_fix_hints(error_msg, project_name)
            else:
                consecutive_failures = 0
                hints = self._get_fix_hints(error_msg, project_name)

            last_error = error_msg

            # コード修正試行（複数回試行）
            fixed_code = None
            for attempt in range(3):  # 修正生成を最大3回試行
                print(f"🔧 修正コード生成試行 {attempt + 1}/3...")
                fixed_code = self._generate_fix(
                    current_code=current_code,
                    error_message=error_msg,
                    hints=hints,
                    project_name=project_name
                )

                if fixed_code and fixed_code != current_code:
                    print(f"✅ 修正コード生成成功")
                    break
                else:
                    print(f"⚠️ 修正コード生成失敗（試行{attempt + 1}）")
                    if attempt < 2:
                        print(f"🔄 再試行中...")

            if fixed_code and fixed_code != current_code:
                # 修正されたコードを保存
                code_file.write_text(fixed_code, encoding='utf-8')
                current_code = fixed_code
                print(f"� コード修正適用完了")
            else:
                # 修正失敗でも継続（最大試行回数まで）
                print(f"⚠️ 修正コード生成失敗、次の試行へ...")
                # 少し異なるアプローチで再試行
                continue

        # 最大試行回数に達した
        print(f"\n{'='*60}")
        print(f"❌ デバッグ失敗: 最大試行回数（{iterations}回）に達しました")
        print(f"📝 最後のエラー: {last_error[:200]}...")
        print(f"{'='*60}")
        self._save_debug_history(project_name, last_error, False, iterations)

        return DebugResult(
            success=False,
            error_message=last_error,
            fix_applied=True,
            iterations=iterations,
            final_code=current_code,
            execution_output=output
        )

    def _execute_code(self, code_file: Path) -> Tuple[bool, Optional[str], str]:
        """
        コードを実行してテスト

        Returns:
            (成功フラグ, エラーメッセージ, 実行出力)
        """
        try:
            # 構文チェック
            print(f"\n🔍 構文チェック実行中...")
            print(f"   コマンド: python -m py_compile {code_file.name}")
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(code_file)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                print(f"❌ 構文チェック失敗")
                print(f"   エラー: {result.stderr[:200]}")
                return False, f"構文エラー: {result.stderr}", result.stderr
            else:
                print(f"✅ 構文チェック成功")

            # 実行テスト（--help）
            print(f"\n🔍 実行テスト中...")
            print(f"   コマンド: python {code_file.name} --help")
            print(f"   作業ディレクトリ: {code_file.parent}")
            result = subprocess.run(
                [sys.executable, str(code_file), '--help'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=code_file.parent
            )

            if result.returncode != 0:
                print(f"❌ 実行テスト失敗 (終了コード: {result.returncode})")
                print(f"   エラー: {result.stderr[:200]}")
                return False, f"実行エラー: {result.stderr}", result.stderr
            else:
                print(f"✅ 実行テスト成功")
                if result.stdout:
                    print(f"   出力: {result.stdout[:150]}...")

            return True, None, result.stdout

        except subprocess.TimeoutExpired:
            print(f"❌ 実行タイムアウト")
            # input()使用を検出
            code_content = code_file.read_text(encoding='utf-8')
            if 'input(' in code_content:
                return False, "実行タイムアウト: input()を使用しています。argparseまたは非対話モードに変更してください", ""
            return False, "実行タイムアウト", ""
        except Exception as e:
            print(f"❌ 実行エラー: {str(e)}")
            return False, f"実行エラー: {str(e)}", ""

    def _get_fix_hints(self, error_msg: str, project_name: str) -> List[str]:
        """エラー修正のヒントを取得"""
        hints = []

        # 1. データベースから過去の成功パターン検索
        db_hints = self._search_db_patterns(error_msg, project_name)
        hints.extend(db_hints)

        # 2. Web検索でヒント取得
        web_hints = self._search_web_solutions(error_msg)
        hints.extend(web_hints)

        # 3. 一般的なエラーパターン
        common_hints = self._get_common_fixes(error_msg)
        hints.extend(common_hints)

        return hints[:5]  # 上位5件

    def _get_detailed_fix_hints(self, error_msg: str, project_name: str, current_code: str) -> List[str]:
        """詳細なエラー分析とヒント取得（同じエラーが繰り返される場合）"""
        hints = []

        print(f"🔍 詳細エラー分析開始...")

        # 1. 基本的なヒント取得
        hints.extend(self._get_fix_hints(error_msg, project_name))

        # 2. エラーメッセージからより詳細な情報を抽出
        if "ArgumentError" in error_msg and "--help" in error_msg:
            hints.append("argparseで--helpを手動で定義しないでください（自動で提供されます）")
            hints.append("--help引数の定義行を削除してください")

        if "NameError" in error_msg and "not defined" in error_msg:
            # 未定義変数を抽出
            import re
            match = re.search(r"name '(\w+)' is not defined", error_msg)
            if match:
                var_name = match.group(1)
                hints.append(f"変数'{var_name}'を使用前に定義してください")
                hints.append(f"グローバル変数として定義するか、関数の引数として渡してください")

        if "構文エラー" in error_msg or "SyntaxError" in error_msg:
            hints.append("Pythonの構文を厳密にチェックしてください")
            hints.append("括弧、クォート、インデントを注意深く確認してください")

        # 3. コードの静的分析
        code_issues = self._analyze_code_structure(current_code)
        hints.extend(code_issues)

        return hints[:10]  # 詳細モードでは上位10件

    def _analyze_code_structure(self, code: str) -> List[str]:
        """コードの構造を分析して問題を検出"""
        issues = []

        lines = code.split('\n')

        # 基本的な静的分析
        for i, line in enumerate(lines, 1):
            # argparseの--help重複チェック
            if 'add_argument' in line and '--help' in line:
                issues.append(f"行{i}: --help引数は削除してください（argparseが自動提供）")

            # 未定義変数の使用をチェック（簡易版）
            if '=' not in line and 'def ' not in line:
                # 変数使用パターン
                import re
                potential_vars = re.findall(r'\b([a-z_][a-z0-9_]*)\b', line.lower())
                # よくある未定義変数
                if 'transactions' in potential_vars and 'transactions' not in code[:code.find(line)]:
                    issues.append(f"行{i}: 変数'transactions'が定義前に使用されている可能性")

        return issues

    def _search_db_patterns(self, error_msg: str, project_name: str) -> List[str]:
        """データベースから成功パターン検索（拡張版）"""
        hints = []

        try:
            # 1. エラータイプを抽出
            error_type = self._extract_error_type(error_msg)

            # 2. 同じエラータイプの成功パターンを検索
            if error_type:
                sql = """
                SELECT DISTINCT project_name, error_message, iterations
                FROM debug_history
                WHERE success = 1
                AND error_message LIKE ?
                ORDER BY created_at DESC
                LIMIT 5
                """
                cursor = self.db_manager._execute_sql(sql, (f"%{error_type}%",))
                patterns = cursor.fetchall()

                for pattern in patterns:
                    hints.append(f"過去の成功例（{pattern[0]}）: {pattern[2]}回で修正成功")

            # 3. 類似プロジェクトの成功パターン（task_typeカラムは存在しないのでスキップ）
            # sql = """
            # SELECT prompt_template, generated_code, success_rate
            # FROM successful_patterns
            # WHERE provider = ?
            # AND task_type LIKE ?
            # ORDER BY success_rate DESC, usage_count DESC
            # LIMIT 3
            # """
            # cursor = self.db_manager._execute_sql(sql, (self.provider, f"%{project_name}%"))
            # patterns = cursor.fetchall()

            # for pattern in patterns:
            #     if pattern[0]:
            #         hints.append(f"成功パターン: {pattern[0][:100]}...")

            # 4. LLM成功履歴から検索
            sql = """
            SELECT request_type, prompt, response_preview
            FROM llm_request_history
            WHERE success = 1
            AND request_type = 'code_fix'
            ORDER BY timestamp DESC
            LIMIT 3
            """
            cursor = self.db_manager._execute_sql(sql, ())
            llm_history = cursor.fetchall()

            for history in llm_history:
                if history[2]:
                    hints.append(f"過去のLLM修正成功例")

            print(f"📊 DB検索: {len(hints)}件のヒント取得")
            return hints

        except Exception as e:
            print(f"DB検索エラー: {e}")
            return []

    def _extract_error_type(self, error_msg: str) -> str:
        """エラーメッセージからエラータイプを抽出"""
        # よくあるPythonエラータイプ
        error_types = [
            'SyntaxError', 'NameError', 'AttributeError', 'TypeError',
            'ValueError', 'ImportError', 'ModuleNotFoundError',
            'KeyError', 'IndexError', 'ArgumentError', 'ZeroDivisionError'
        ]

        for error_type in error_types:
            if error_type in error_msg:
                return error_type

        return ""

    def _search_web_solutions(self, error_msg: str) -> List[str]:
        """エラー解決策を取得（Web検索 + ローカル知識ベース）"""
        hints = []

        try:
            # 1. エラータイプを抽出
            error_type = self._extract_error_type(error_msg)
            print(f"🔍 エラータイプ抽出: {error_type if error_type else '(不明)'}")

            # 2. エラーメッセージから重要な部分を抽出
            error_key = self._extract_error_key(error_msg)
            if error_key:
                print(f"🔍 エラーキー抽出: {error_key[:80]}")

            # 3. まずローカル知識ベース（確実に取得できる）
            local_hints = self._get_local_error_solutions(error_type, error_key)
            if local_hints:
                print(f"📚 ローカル知識ベース: {len(local_hints)}件のヒント")
                for i, hint in enumerate(local_hints[:3], 1):
                    print(f"   {i}. {hint}")
            hints.extend(local_hints)

            # 4. Python公式ドキュメント検索を試行（タイムアウト短く）
            if error_type and len(hints) < 3:
                try:
                    print(f"🔍 Python公式Docs検索: '{error_type}'")
                    python_doc = self.web_searcher._search_python_docs(error_type)
                    if python_doc:
                        print(f"✅ 公式Docs発見: {python_doc.title}")
                        hints.append(f"📚 公式Docs: {python_doc.title}")
                        if python_doc.snippet:
                            hints.append(f"  → {python_doc.snippet[:150]}")
                    else:
                        print(f"⚠️ 公式Docs: 結果なし")
                except Exception as e:
                    print(f"⚠️ 公式Docs検索エラー: {e}")

            # 5. DuckDuckGo検索を試行（タイムアウト短く、失敗しても継続）
            if len(hints) < 5:
                queries = []
                if error_type:
                    queries.append(f"Python {error_type} solution")

                for query in queries[:1]:  # 1クエリのみ
                    try:
                        print(f"🔍 Web検索開始: '{query}'")
                        web_results = self.web_searcher._search_web_simple(query, max_results=2)

                        if web_results:
                            print(f"✅ Web検索: {len(web_results)}件発見")
                            for i, result in enumerate(web_results[:2], 1):
                                print(f"   {i}. [{result.source}] {result.title[:60]}")
                                if result.snippet:
                                    print(f"      > {result.snippet[:100]}...")
                                if result.title:
                                    hints.append(f"🌐 Web: {result.title[:80]}")
                                if result.snippet and len(result.snippet) > 20:
                                    hints.append(f"  → {result.snippet[:120]}")
                        else:
                            print(f"⚠️ Web検索: 結果なし")
                    except Exception as e:
                        print(f"⚠️ Web検索エラー: {str(e)[:100]}")

            print(f"📊 合計ヒント数: {len(hints)}件")
            return hints[:8]

        except Exception as e:
            print(f"❌ Web検索処理エラー: {e}")
            # エラーでもローカル知識ベースを返す
            return self._get_local_error_solutions(self._extract_error_type(error_msg), "")

    def _get_local_error_solutions(self, error_type: str, error_key: str) -> List[str]:
        """ローカル知識ベースからエラー解決策を取得"""
        hints = []

        # エラータイプ別の解決策
        solutions = {
            'ImportError': [
                "💡 不足モジュール: 必要なimport文を追加してください",
                "💡 モジュール名確認: getpass, hide_passwordなどの存在しない関数をimportしていないか確認",
                "💡 標準ライブラリ: randomモジュールはimport randomが必要です",
            ],
            'NameError': [
                "💡 未定義変数: 使用前に変数を定義してください",
                "💡 import文: randomやloggingなどのモジュールをimportしてください",
                "💡 スペルミス: 変数名や関数名のスペルを確認してください",
            ],
            'ArgumentError': [
                "💡 argparse重複: --helpは自動追加されるため、手動追加は不要です",
                "💡 引数定義: add_argumentで同じ引数を複数回定義していないか確認",
                "💡 オプション名: 既存のオプション（--help, --version）との衝突を確認",
            ],
            'AttributeError': [
                "💡 メソッド名: オブジェクトに存在するメソッドを使用してください",
                "💡 モジュール確認: モジュールが正しくimportされているか確認",
            ],
            'SyntaxError': [
                "💡 インデント: Pythonはインデントが重要です",
                "💡 括弧の対応: ()[]{}の開閉を確認してください",
                "💡 クォート: 文字列のクォートを確認してください",
            ],
        }

        if error_type in solutions:
            hints.extend(solutions[error_type])
        else:
            # 一般的なヒント
            hints.extend([
                "💡 エラーメッセージを確認: スタックトレースから問題箇所を特定",
                "💡 import文: 必要なモジュールがimportされているか確認",
                "💡 変数定義: 使用前に変数が定義されているか確認",
            ])

        return hints

    def _extract_error_key(self, error_msg: str) -> str:
        """エラーメッセージから重要なキーワードを抽出"""
        # "name 'xxx' is not defined" -> "xxx is not defined"
        # "conflicting option string: --help" -> "conflicting option string"

        import re

        # パターン1: 'xxx' is not defined
        match = re.search(r"name '(\w+)' is not defined", error_msg)
        if match:
            return f"{match.group(1)} is not defined"

        # パターン2: conflicting option string
        match = re.search(r"(conflicting option string|argument .+?:)", error_msg)
        if match:
            return match.group(1)

        # パターン3: 最初の行を取得
        first_line = error_msg.split('\n')[0]
        if len(first_line) < 100:
            return first_line

        return ""

    def _get_common_fixes(self, error_msg: str) -> List[str]:
        """一般的なエラーの修正方法"""
        common_fixes = {
            "SyntaxError": [
                "インデントを確認",
                "括弧の対応を確認",
                "クォートの対応を確認"
            ],
            "NameError": [
                "変数名のスペルミスを確認",
                "import文を追加",
                "変数の定義を確認"
            ],
            "AttributeError": [
                "メソッド名のスペルミスを確認",
                "オブジェクトの型を確認",
                "Noneチェックを追加"
            ],
            "ImportError": [
                "モジュール名を確認",
                "標準ライブラリのインポートパスを確認",
                "相対インポートを絶対インポートに変更"
            ]
        }

        for error_type, fixes in common_fixes.items():
            if error_type in error_msg:
                return fixes

        return ["コードの構造を見直す"]

    def _generate_fix(self, current_code: str, error_message: str,
                     hints: List[str], project_name: str) -> Optional[str]:
        """LLMでエラー修正コードを生成"""

        hints_text = "\n".join(f"- {hint}" for hint in hints)

        # input()タイムアウトの場合は具体的な修正例を追加
        extra_instructions = ""
        if "input()" in error_message or "タイムアウト" in error_message:
            if "input(" in current_code:
                extra_instructions = """
【重要】input()使用によるタイムアウトを検出しました。以下のように修正してください：

❌ 悪い例（input()使用）:
```python
while True:
    expression = input("Enter expression: ")
    result = eval(expression)
```

✅ 良い例（argparse使用）:
```python
import argparse

def main():
    parser = argparse.ArgumentParser(description="計算機")
    parser.add_argument("--expression", type=str, help="計算式")
    parser.add_argument("--test", action="store_true", help="テストモード")
    args = parser.parse_args()

    if args.test:
        # テストケース実行
        test_expressions = ["2+2", "10*5", "100/4"]
        for expr in test_expressions:
            result = eval(expr)
            print(f"{expr} = {result}")
    elif args.expression:
        result = eval(args.expression)
        print(f"Result: {result}")
```

必ずargparseを使用して、--testオプションと--expressionオプションを実装してください。
"""

        prompt = f"""
以下のPythonコードにエラーがあります。修正してください。

【エラー内容】
{error_message}

【修正のヒント】
{hints_text}
{extra_instructions}

【現在のコード】
```python
{current_code}
```

【要求】
- エラーを修正した完全なコードを出力
- input()は使用禁止。必ずargparseを使用
- --help, --test, --expressionなどのオプションを実装
- コードの機能は保持する
- 標準ライブラリのみ使用
- コードブロック以外の説明は不要

修正されたコードのみを出力してください：
"""

        try:
            llm_request = LLMRequest(
                prompt=prompt,
                system_message="あなたは熟練したPythonデバッガーです。エラーを分析して修正してください。",
                request_type="code_fix",
                max_tokens=2000,
                temperature=0.2
            )

            print(f"\n{'='*60}")
            print(f"🤖 LLM修正プロンプト送信 ({self.provider})")
            print(f"{'='*60}")
            print(f"📝 プロンプト長: {len(prompt)}文字")
            print(f"🔧 エラー内容: {error_message[:100]}...")
            print(f"💡 ヒント数: {len(hints)}件")

            response = self.llm_agent.generate_text(llm_request)

            if response.is_success:
                print(f"\n{'='*60}")
                print(f"✅ LLM応答受信")
                print(f"{'='*60}")
                print(f"📊 応答長: {len(response.content)}文字")
                print(f"\n🤖 LLMの思考プロセス:")
                print(f"{'-'*60}")
                # 最初の500文字を表示
                display_content = response.content[:500]
                print(display_content)
                if len(response.content) > 500:
                    print(f"\n... (残り {len(response.content) - 500}文字)")
                print(f"{'-'*60}\n")

                fixed_code = self._extract_code(response.content)

                if fixed_code:
                    print(f"✅ コード抽出成功: {len(fixed_code)}文字")
                    # 抽出されたコードの最初の部分を表示
                    print(f"\n📝 抽出されたコード（最初の300文字）:")
                    print(f"{'-'*60}")
                    print(fixed_code[:300])
                    if len(fixed_code) > 300:
                        print(f"... (残り {len(fixed_code) - 300}文字)")
                    print(f"{'-'*60}")

                    # input()が残っているか確認
                    if 'input(' in fixed_code:
                        print(f"⚠️ 警告: 抽出されたコードにinput()が残っています")
                else:
                    print(f"⚠️ コード抽出失敗")

                return fixed_code
            else:
                print(f"\n❌ LLM修正失敗: {response.error}")
                return None

        except Exception as e:
            print(f"\n❌ 修正生成エラー: {e}")
            return None

    def _extract_code(self, content: str) -> str:
        """レスポンスからコードを抽出"""
        if '```python' in content:
            return content.split('```python')[1].split('```')[0].strip()
        elif '```' in content:
            return content.split('```')[1].split('```')[0].strip()
        else:
            return content.strip()

    def _save_success_pattern(self, project_name: str, code: str):
        """成功パターンをDB保存"""
        try:
            sql = """
            INSERT INTO successful_patterns
            (task_description, generated_code, provider)
            VALUES (?, ?, ?)
            """
            self.db_manager._execute_sql(sql, (project_name, code, self.provider))
            print(f"💾 成功パターン保存: {project_name}")
        except Exception as e:
            print(f"保存エラー: {e}")

    def _save_debug_history(self, project_name: str, error_msg: str,
                           success: bool, iterations: int):
        """デバッグ履歴を保存"""
        try:
            sql = """
            INSERT INTO debug_history
            (project_name, error_message, success, iterations, provider)
            VALUES (?, ?, ?, ?, ?)
            """
            self.db_manager._execute_sql(
                sql,
                (project_name, error_msg, success, iterations, self.provider)
            )
        except Exception as e:
            print(f"履歴保存エラー: {e}")


def main():
    """テスト実行"""
    debugger = AutoDebugger(provider="ollama")

    # テストファイル
    test_file = Path("generated_projects/test_cli/main.py")

    if test_file.exists():
        result = debugger.test_and_fix_code(test_file, "test_cli")
        print(f"\n結果: {'成功' if result.success else '失敗'}")
        print(f"試行回数: {result.iterations}")
    else:
        print("テストファイルが見つかりません")


if __name__ == "__main__":
    main()
