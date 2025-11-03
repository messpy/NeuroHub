#!/usr/bin/env python3
"""
MCP生成品質改善ツール
agent_mcp.pyの生成品質向上・import文自動追加・構文チェック強化
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import importlib.util


class CodeAnalyzer:
    """コード解析・品質改善クラス"""

    STANDARD_LIBRARIES = {
        'os', 'sys', 'json', 'time', 'datetime', 're', 'pathlib', 'typing',
        'collections', 'itertools', 'functools', 'argparse', 'logging',
        'sqlite3', 'hashlib', 'secrets', 'base64', 'tempfile', 'shutil',
        'subprocess', 'threading', 'asyncio', 'unittest', 'dataclasses'
    }

    COMMON_IMPORTS = {
        'Path': 'from pathlib import Path',
        'Dict': 'from typing import Dict',
        'List': 'from typing import List',
        'Optional': 'from typing import Optional',
        'Any': 'from typing import Any',
        'Union': 'from typing import Union',
        'Tuple': 'from typing import Tuple',
        'dataclass': 'from dataclasses import dataclass',
        'Fernet': 'from cryptography.fernet import Fernet',
        'PBKDF2HMAC': 'from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC',
        'hashes': 'from cryptography.hazmat.primitives import hashes',
        'sqlite3': 'import sqlite3',
        'hashlib': 'import hashlib',
        'secrets': 'import secrets',
        'base64': 'import base64',
        'json': 'import json',
        'os': 'import os',
        'sys': 'import sys',
        'cryptography': 'from cryptography.fernet import Fernet',
        'DatabaseError': 'class DatabaseError(Exception): pass',
        'EncryptionError': 'class EncryptionError(Exception): pass'
    }

    def __init__(self):
        """コード解析器初期化"""
        self.missing_imports = []
        self.syntax_errors = []
        self.quality_issues = []

    def analyze_code(self, code: str) -> Dict[str, List[str]]:
        """コード解析実行"""
        try:
            # 構文解析
            self._check_syntax(code)

            # import文解析
            self._analyze_imports(code)

            # 品質チェック
            self._quality_check(code)

            return {
                'syntax_errors': self.syntax_errors,
                'missing_imports': self.missing_imports,
                'quality_issues': self.quality_issues
            }

        except Exception as e:
            return {
                'syntax_errors': [f"解析エラー: {e}"],
                'missing_imports': [],
                'quality_issues': []
            }

    def _check_syntax(self, code: str) -> None:
        """構文チェック"""
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.syntax_errors.append(f"構文エラー (行{e.lineno}): {e.msg}")
        except Exception as e:
            self.syntax_errors.append(f"構文解析エラー: {e}")

    def _analyze_imports(self, code: str) -> None:
        """import文解析"""
        try:
            # 使用されているが定義されていない名前を検出
            tree = ast.parse(code)

            # 定義された名前を収集
            defined_names = set()
            imported_names = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    defined_names.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    defined_names.add(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_names.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imported_names.add(alias.name)

            # 使用されている名前を検出
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)

            # 不足しているimport文を検出
            undefined_names = used_names - defined_names - imported_names

            for name in undefined_names:
                if name in self.COMMON_IMPORTS:
                    self.missing_imports.append(self.COMMON_IMPORTS[name])
                elif name in self.STANDARD_LIBRARIES:
                    self.missing_imports.append(f"import {name}")

        except Exception as e:
            self.missing_imports.append(f"import解析エラー: {e}")

    def _quality_check(self, code: str) -> None:
        """品質チェック"""
        try:
            # docstringチェック
            if '"""' not in code and "'''" not in code:
                self.quality_issues.append("docstringが不足している可能性があります")

            # エラーハンドリングチェック
            if 'try:' not in code and 'except' not in code:
                self.quality_issues.append("エラーハンドリングが不足している可能性があります")

            # 関数・クラス定義チェック
            if 'def ' not in code and 'class ' not in code:
                self.quality_issues.append("関数またはクラス定義がありません")

            # pass文チェック（不完全実装の可能性）
            pass_count = code.count('pass')
            if pass_count > 2:
                self.quality_issues.append(f"pass文が多すぎます ({pass_count}個) - 不完全実装の可能性")

            # TODO・FIXMEコメントチェック
            todo_count = code.lower().count('todo') + code.lower().count('fixme')
            if todo_count > 0:
                self.quality_issues.append(f"TODO/FIXMEコメントがあります ({todo_count}個)")

        except Exception as e:
            self.quality_issues.append(f"品質チェックエラー: {e}")


class CodeImprover:
    """コード改善・修正クラス"""

    def __init__(self):
        """コード改善器初期化"""
        self.analyzer = CodeAnalyzer()

    def improve_code(self, code: str) -> Tuple[str, List[str]]:
        """コード改善実行"""
        try:
            improvements = []

            # コード解析
            analysis = self.analyzer.analyze_code(code)

            # import文自動追加
            if analysis['missing_imports']:
                code, import_improvements = self._add_missing_imports(code, analysis['missing_imports'])
                improvements.extend(import_improvements)

            # 構文エラー修正
            if analysis['syntax_errors']:
                code, syntax_improvements = self._fix_syntax_errors(code, analysis['syntax_errors'])
                improvements.extend(syntax_improvements)

            # 品質改善
            if analysis['quality_issues']:
                code, quality_improvements = self._improve_quality(code, analysis['quality_issues'])
                improvements.extend(quality_improvements)

            return code, improvements

        except Exception as e:
            return code, [f"改善エラー: {e}"]

    def _add_missing_imports(self, code: str, missing_imports: List[str]) -> Tuple[str, List[str]]:
        """不足import文追加"""
        try:
            improvements = []

            # 既存のimport文の位置を検出
            lines = code.split('\n')
            import_end_line = 0

            # shebang, encoding, docstringをスキップ
            for i, line in enumerate(lines):
                line_strip = line.strip()
                if (line_strip.startswith('#') or
                    line_strip.startswith('"""') or
                    line_strip.startswith("'''") or
                    line_strip == ''):
                    continue
                elif line_strip.startswith(('import ', 'from ')):
                    import_end_line = i + 1
                else:
                    break

            # 新しいimport文を追加
            unique_imports = list(set(missing_imports))
            import_lines = []

            for import_stmt in unique_imports:
                if import_stmt not in code:  # 重複チェック
                    import_lines.append(import_stmt)
                    improvements.append(f"import文追加: {import_stmt}")

            if import_lines:
                # import文を挿入
                new_lines = (
                    lines[:import_end_line] +
                    import_lines +
                    [''] +  # 空行追加
                    lines[import_end_line:]
                )
                code = '\n'.join(new_lines)

            return code, improvements

        except Exception as e:
            return code, [f"import追加エラー: {e}"]

    def _fix_syntax_errors(self, code: str, syntax_errors: List[str]) -> Tuple[str, List[str]]:
        """構文エラー修正"""
        try:
            improvements = []

            # 基本的な構文エラー修正
            if any("invalid character" in error for error in syntax_errors):
                # 不正文字の削除
                code = re.sub(r'[^\x00-\x7F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '', code)
                improvements.append("不正文字削除")

            if any("unexpected EOF" in error for error in syntax_errors):
                # 不完全なブロックの修正
                if not code.strip().endswith(':'):
                    code += '\n    pass'
                    improvements.append("不完全ブロック修正")

            return code, improvements

        except Exception as e:
            return code, [f"構文修正エラー: {e}"]

    def _improve_quality(self, code: str, quality_issues: List[str]) -> Tuple[str, List[str]]:
        """品質改善"""
        try:
            improvements = []

            # pass文を実装に置換
            if "pass文が多すぎます" in str(quality_issues):
                # 簡単なpass文の置換
                code = re.sub(
                    r'def\s+(\w+)\([^)]*\):\s*pass',
                    r'def \1(self, *args, **kwargs):\n        """実装が必要なメソッド"""\n        raise NotImplementedError("実装してください")',
                    code
                )
                improvements.append("pass文を実装可能な形に修正")

            # 基本的なdocstring追加
            if "docstringが不足" in str(quality_issues):
                # クラスdocstring追加
                code = re.sub(
                    r'class\s+(\w+)[^:]*:\s*\n',
                    r'class \1:\n    """\1クラス"""\n    \n',
                    code
                )
                improvements.append("基本docstring追加")

            return code, improvements

        except Exception as e:
            return code, [f"品質改善エラー: {e}"]


def improve_mcp_generated_file(file_path: str) -> Tuple[bool, List[str]]:
    """MCP生成ファイルの改善"""
    try:
        print(f"🔧 ファイル改善開始: {file_path}")

        # ファイル読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            original_code = f.read()

        # コード改善
        improver = CodeImprover()
        improved_code, improvements = improver.improve_code(original_code)

        # 改善されたコードを保存
        if improvements:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(improved_code)

            print(f"✅ ファイル改善完了: {len(improvements)}項目")
            for improvement in improvements:
                print(f"  - {improvement}")
        else:
            print("✅ 改善項目なし - ファイルは既に良好です")

        return True, improvements

    except Exception as e:
        print(f"❌ ファイル改善エラー: {e}")
        return False, [str(e)]


def main():
    """メイン関数 - CLI実行用"""
    import argparse

    parser = argparse.ArgumentParser(description="MCP生成品質改善ツール")
    parser.add_argument("file_path", help="改善対象ファイルパス")
    parser.add_argument("--analyze-only", action="store_true", help="解析のみ実行")

    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"❌ ファイルが見つかりません: {args.file_path}")
        sys.exit(1)

    if args.analyze_only:
        # 解析のみ
        with open(args.file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_code(code)

        print(f"📊 コード解析結果: {args.file_path}")
        print(f"構文エラー: {len(analysis['syntax_errors'])}")
        for error in analysis['syntax_errors']:
            print(f"  ❌ {error}")

        print(f"不足import文: {len(analysis['missing_imports'])}")
        for missing in analysis['missing_imports']:
            print(f"  📦 {missing}")

        print(f"品質問題: {len(analysis['quality_issues'])}")
        for issue in analysis['quality_issues']:
            print(f"  ⚠️ {issue}")
    else:
        # 改善実行
        success, improvements = improve_mcp_generated_file(args.file_path)
        if success:
            print("🎉 改善処理完了")
        else:
            print("❌ 改善処理失敗")
            sys.exit(1)


if __name__ == "__main__":
    main()
