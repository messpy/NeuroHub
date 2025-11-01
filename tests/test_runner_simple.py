#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_runner_simple.py - シンプルなテスト実行器
依存関係の問題を回避してテストの構文と基本的な実行をチェック
"""

import sys
import os
import importlib.util
from pathlib import Path

def run_simple_test_check():
    """テストファイルの基本チェックを実行"""
    print("🧪 NeuroHub Simple Test Check")
    print("=" * 50)

    # プロジェクトルートを設定
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    test_files = [
        "tests/agents/test_git_agent.py",
        "tests/agents/test_llm_agent.py",
        "tests/agents/test_config_agent.py",
        "tests/agents/test_command_agent.py",
        "tests/services/test_llm_providers.py",
        "tests/services/test_db_services.py"
    ]

    results = {}

    for test_file in test_files:
        print(f"\n📁 Checking {test_file}...")

        try:
            # ファイル存在チェック
            file_path = project_root / test_file
            if not file_path.exists():
                results[test_file] = {"status": "ERROR", "message": "File not found"}
                continue

            # 構文チェック
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            try:
                compile(content, str(file_path), 'exec')
                print(f"  ✅ Syntax OK")
            except SyntaxError as e:
                results[test_file] = {"status": "SYNTAX_ERROR", "message": str(e)}
                print(f"  ❌ Syntax Error: {e}")
                continue

            # インポートテスト（安全）
            try:
                spec = importlib.util.spec_from_file_location("test_module", file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules["test_module"] = module
                    spec.loader.exec_module(module)
                    print(f"  ✅ Import OK")

                    # テスト関数カウント
                    test_functions = [name for name in dir(module) if name.startswith('test_') or hasattr(getattr(module, name, None), '__name__')]
                    classes_with_tests = []
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if hasattr(attr, '__name__') and attr_name.startswith('Test'):
                            class_tests = [method for method in dir(attr) if method.startswith('test_')]
                            if class_tests:
                                classes_with_tests.append((attr_name, len(class_tests)))

                    print(f"  📊 Test classes: {len(classes_with_tests)}")
                    for class_name, test_count in classes_with_tests:
                        print(f"     - {class_name}: {test_count} tests")

                    results[test_file] = {
                        "status": "OK",
                        "test_classes": len(classes_with_tests),
                        "total_tests": sum(count for _, count in classes_with_tests)
                    }

            except Exception as e:
                results[test_file] = {"status": "IMPORT_ERROR", "message": str(e)}
                print(f"  ⚠️ Import Warning: {e}")

        except Exception as e:
            results[test_file] = {"status": "ERROR", "message": str(e)}
            print(f"  ❌ Error: {e}")

    # サマリー表示
    print("\n" + "=" * 50)
    print("📊 TEST CHECK SUMMARY")
    print("=" * 50)

    total_files = len(test_files)
    ok_files = len([f for f, r in results.items() if r.get("status") == "OK"])
    error_files = len([f for f, r in results.items() if r.get("status") != "OK"])

    print(f"Total Test Files: {total_files}")
    print(f"✅ OK: {ok_files}")
    print(f"❌ Errors/Warnings: {error_files}")

    total_test_count = sum(r.get("total_tests", 0) for r in results.values() if r.get("status") == "OK")
    print(f"📝 Total Test Methods: {total_test_count}")

    # エラー詳細
    if error_files > 0:
        print(f"\n🔍 ERROR DETAILS:")
        for file, result in results.items():
            if result.get("status") != "OK":
                print(f"  ❌ {file}: {result.get('status')} - {result.get('message', 'Unknown error')}")

    # 成功詳細
    if ok_files > 0:
        print(f"\n✅ SUCCESSFUL FILES:")
        for file, result in results.items():
            if result.get("status") == "OK":
                print(f"  ✅ {file}: {result.get('test_classes', 0)} classes, {result.get('total_tests', 0)} tests")

if __name__ == "__main__":
    run_simple_test_check()
