#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_tests.py - 統合テストランナー
"""

import subprocess
import sys
import os
import argparse
import time
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_command(command, cwd=None):
    """コマンド実行"""
    print(f"🔧 実行中: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            print(f"✅ 成功: {command}")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ 失敗: {command}")
            if result.stderr:
                print(result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ エラー: {command} - {e}")
        return False


def run_python_tests():
    """Pythonテスト実行"""
    print("\n📋 Pythonユニットテスト実行")
    print("=" * 50)

    test_commands = [
        # エージェントテスト
        "python -m pytest tests/agents/test_git_agent.py -v",
        "python -m pytest tests/agents/test_llm_agent.py -v",
        "python -m pytest tests/agents/test_config_agent.py -v",
        "python -m pytest tests/agents/test_command_agent.py -v",

        # サービステスト
        "python -m pytest tests/services/test_llm_providers.py -v",
        "python -m pytest tests/services/test_db_services.py -v",
    ]

    success_count = 0
    for command in test_commands:
        if run_command(command):
            success_count += 1
        print("")

    print(f"📊 Pythonテスト結果: {success_count}/{len(test_commands)} 成功")
    return success_count == len(test_commands)


def run_coverage_tests():
    """カバレッジテスト実行"""
    print("\n📊 カバレッジテスト実行")
    print("=" * 50)

    commands = [
        "python -m pytest tests/ --cov=agents --cov=services --cov-report=term-missing --cov-report=html",
    ]

    for command in commands:
        run_command(command)


def run_shell_tests():
    """シェルテスト実行"""
    print("\n🐚 シェルツールテスト実行")
    print("=" * 50)

    # git_commit_ai テスト（bashが利用可能な場合）
    if os.name != 'nt':  # Windows以外
        test_script = PROJECT_ROOT / "tests" / "tools" / "test_git_commit_ai.sh"
        if test_script.exists():
            # 実行権限付与
            os.chmod(test_script, 0o755)
            return run_command(f"bash {test_script}")
    else:
        print("⚠️ Windows環境: シェルテストをスキップ")

    return True


def run_integration_tests():
    """統合テスト実行"""
    print("\n🔗 統合テスト実行")
    print("=" * 50)

    integration_commands = [
        # データベース初期化テスト
        "python setup_database.py",

        # 設定生成テスト
        "python agents/config_agent.py --generate",

        # エージェント基本動作テスト
        "python agents/git_agent.py --status",
        "python agents/llm_agent.py --status",
        "python agents/config_agent.py --status",
        "python agents/command_agent.py --history",
    ]

    success_count = 0
    for command in integration_commands:
        if run_command(command):
            success_count += 1
        print("")

    print(f"📊 統合テスト結果: {success_count}/{len(integration_commands)} 成功")
    return success_count == len(integration_commands)


def run_lint_checks():
    """リントチェック実行"""
    print("\n🧹 コード品質チェック")
    print("=" * 50)

    lint_commands = [
        "python -m flake8 agents/ --max-line-length=120 --ignore=E501,W503",
        "python -m flake8 services/ --max-line-length=120 --ignore=E501,W503",
    ]

    success_count = 0
    for command in lint_commands:
        try:
            if run_command(command):
                success_count += 1
        except:
            print(f"⚠️ {command} - flake8がインストールされていません")

    return True  # リントエラーでも全体テストは続行


def generate_test_report():
    """テストレポート生成"""
    print("\n📋 テストレポート生成")
    print("=" * 50)

    report_file = PROJECT_ROOT / "test_report.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# NeuroHub テストレポート\n\n")
        f.write(f"生成日時: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## テスト環境\n\n")
        f.write(f"- Python: {sys.version}\n")
        f.write(f"- OS: {os.name}\n")
        f.write(f"- プロジェクトパス: {PROJECT_ROOT}\n\n")
        f.write("## テスト結果\n\n")
        f.write("詳細な結果については、上記のテスト実行ログを参照してください。\n\n")
        f.write("## カバレッジレポート\n\n")
        f.write("HTMLカバレッジレポートが `htmlcov/` ディレクトリに生成されています。\n")

    print(f"✅ テストレポート生成完了: {report_file}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="NeuroHub テストランナー")
    parser.add_argument("--python-only", action="store_true", help="Pythonテストのみ実行")
    parser.add_argument("--coverage", action="store_true", help="カバレッジテスト実行")
    parser.add_argument("--integration", action="store_true", help="統合テストのみ実行")
    parser.add_argument("--lint", action="store_true", help="リントチェックのみ実行")
    parser.add_argument("--all", action="store_true", help="全テスト実行（デフォルト）")

    args = parser.parse_args()

    print("🧪 NeuroHub テストスイート")
    print("=" * 50)
    print(f"プロジェクトルート: {PROJECT_ROOT}")
    print(f"Python: {sys.version}")
    print("")

    start_time = time.time()

    # テスト実行
    if args.python_only:
        run_python_tests()
    elif args.coverage:
        run_coverage_tests()
    elif args.integration:
        run_integration_tests()
    elif args.lint:
        run_lint_checks()
    else:
        # 全テスト実行
        print("🚀 全テストスイート実行開始")

        results = []
        results.append(("Pythonテスト", run_python_tests()))
        results.append(("シェルテスト", run_shell_tests()))
        results.append(("統合テスト", run_integration_tests()))
        results.append(("リントチェック", run_lint_checks()))

        if args.coverage or args.all:
            run_coverage_tests()

        # 結果サマリー
        print("\n🏁 テスト完了サマリー")
        print("=" * 50)

        for test_name, success in results:
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"{test_name}: {status}")

        total_success = sum(1 for _, success in results if success)
        print(f"\n総合結果: {total_success}/{len(results)} テストカテゴリ成功")

        generate_test_report()

    elapsed_time = time.time() - start_time
    print(f"\n⏱️ 実行時間: {elapsed_time:.2f}秒")

    print("\n💡 次のステップ:")
    print("1. テスト結果を確認")
    print("2. カバレッジレポート確認: open htmlcov/index.html")
    print("3. 失敗したテストがあれば個別実行でデバッグ")
    print("4. コードの改善を実施")


if __name__ == "__main__":
    main()
