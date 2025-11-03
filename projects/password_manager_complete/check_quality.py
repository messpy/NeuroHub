#!/usr/bin/env python3
"""
Ollama MCP パスワードマネージャー品質チェック

生成されたコードの品質（関数定義、docstring、エラーハンドリング）を検証
"""

import ast
import os
import sys
from pathlib import Path

def check_code_quality(project_path: str):
    """コード品質チェック実行"""
    print("=== Ollama MCP パスワードマネージャー品質チェック ===")

    project_path = Path(project_path)
    python_files = list(project_path.rglob("*.py"))

    total_functions = 0
    total_classes = 0
    total_docstrings = 0
    total_try_except = 0
    total_type_hints = 0

    print(f"📁 プロジェクトパス: {project_path}")
    print(f"📄 Python ファイル数: {len(python_files)}")
    print("-" * 60)

    for file_path in python_files:
        rel_path = file_path.relative_to(project_path)
        print(f"📄 {rel_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)

            # 関数・クラスの解析
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

            # docstring チェック
            functions_with_docs = [f for f in functions if ast.get_docstring(f)]
            classes_with_docs = [c for c in classes if ast.get_docstring(c)]
            docstrings = len(functions_with_docs) + len(classes_with_docs)

            # try-except チェック
            try_blocks = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]

            # 型ヒントチェック
            type_hints = 0
            for func in functions:
                if func.returns:  # 戻り値の型ヒント
                    type_hints += 1
                for arg in func.args.args:
                    if arg.annotation:  # 引数の型ヒント
                        type_hints += 1

            print(f"   ✅ 関数: {len(functions)}")
            print(f"   ✅ クラス: {len(classes)}")
            print(f"   📝 docstring: {docstrings}/{len(functions)+len(classes)}")
            print(f"   🛡️ try-except: {len(try_blocks)}")
            print(f"   🏷️ 型ヒント: {type_hints}")

            # 統計累計
            total_functions += len(functions)
            total_classes += len(classes)
            total_docstrings += docstrings
            total_try_except += len(try_blocks)
            total_type_hints += type_hints

        except Exception as e:
            print(f"   ❌ パースエラー: {e}")

        print()

    # 総合統計
    print("=" * 60)
    print("📊 総合統計")
    print("-" * 60)
    print(f"📁 ファイル数: {len(python_files)}")
    print(f"⚙️ 総関数数: {total_functions}")
    print(f"🏛️ 総クラス数: {total_classes}")
    print(f"📝 docstring数: {total_docstrings}")
    print(f"🛡️ try-except数: {total_try_except}")
    print(f"🏷️ 型ヒント数: {total_type_hints}")

    # 品質指標
    total_definitions = total_functions + total_classes
    if total_definitions > 0:
        docstring_rate = (total_docstrings / total_definitions) * 100
        print(f"📈 docstring率: {docstring_rate:.1f}%")

    print("\n🎯 品質評価:")

    # 関数・クラス定義チェック
    if total_definitions > 0:
        print("   ✅ 関数・クラス定義あり")
    else:
        print("   ⚠️ 関数・クラス定義なし")

    # docstring チェック
    if total_definitions > 0 and (total_docstrings / total_definitions) >= 0.8:
        print("   ✅ docstring充実 (80%以上)")
    elif total_docstrings > 0:
        print("   ⚠️ docstring不足 (80%未満)")
    else:
        print("   ⚠️ docstring不足")

    # エラーハンドリングチェック
    if total_try_except >= 5:
        print("   ✅ エラーハンドリング充実")
    elif total_try_except > 0:
        print("   ⚠️ エラーハンドリング不足")
    else:
        print("   ⚠️ エラーハンドリングなし")

    # 型ヒントチェック
    if total_type_hints >= total_functions:
        print("   ✅ 型ヒント充実")
    elif total_type_hints > 0:
        print("   ⚠️ 型ヒント不足")
    else:
        print("   ⚠️ 型ヒントなし")

    print("\n🎉 品質チェック完了")

    # 警告解消状況
    issues_fixed = 0
    if total_definitions > 0:
        issues_fixed += 1
    if total_docstrings > 0:
        issues_fixed += 1
    if total_try_except > 0:
        issues_fixed += 1

    print(f"✅ 解消された警告: {issues_fixed}/3")

    return {
        'files': len(python_files),
        'functions': total_functions,
        'classes': total_classes,
        'docstrings': total_docstrings,
        'try_except': total_try_except,
        'type_hints': total_type_hints,
        'quality_score': issues_fixed / 3 * 100
    }

if __name__ == "__main__":
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    stats = check_code_quality(project_path)

    # 品質スコアに基づく終了コード
    if stats['quality_score'] >= 100:
        print("🏆 優秀な品質です！")
        sys.exit(0)
    elif stats['quality_score'] >= 66:
        print("👍 良好な品質です")
        sys.exit(0)
    else:
        print("📈 改善の余地があります")
        sys.exit(1)
