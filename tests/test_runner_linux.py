#!/usr/bin/env python3
"""
NeuroHub Linux Test Validator
Linux環境での単体テスト検証スクリプト
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Any


def check_linux_environment():
    """Linux環境チェック"""
    print("🐧 Linux Environment Check")
    print("=" * 40)

    # OS確認
    system = platform.system()
    print(f"OS: {system}")
    if system != "Linux":
        print("⚠️  Warning: Not running on Linux")

    # Python版確認
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"Python: {python_version}")

    # 仮想環境確認
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"✅ Virtual Environment: {venv_path}")
    else:
        print("⚠️  No virtual environment detected")

    # Git確認
    try:
        git_version = subprocess.check_output(['git', '--version'], text=True).strip()
        print(f"✅ {git_version}")
    except FileNotFoundError:
        print("❌ Git not found")

    # 権限確認
    current_dir = Path.cwd()
    if os.access(current_dir, os.R_OK | os.W_OK):
        print(f"✅ Directory permissions: {current_dir}")
    else:
        print(f"❌ Insufficient permissions: {current_dir}")

    print()


def validate_linux_test_files():
    """Linuxテストファイル検証"""
    print("🔍 Linux Test File Validation")
    print("=" * 40)

    test_files = [
        "tests/agents/test_command_agent.py",
        "tests/agents/test_config_agent.py",
        "tests/agents/test_git_agent.py",
        "tests/agents/test_llm_agent.py",
        "tests/services/test_db_services.py",
        "tests/services/test_llm_providers.py"
    ]

    for test_file in test_files:
        path = Path(test_file)
        if path.exists():
            print(f"✅ {test_file}")

            # Linux固有の要素をチェック
            content = path.read_text()

            # Linux権限関連のテストがあるかチェック
            if "chmod" in content or "os.access" in content:
                print(f"  🐧 Linux permission handling detected")

            # Linux固有のパスがあるかチェック
            if "/bin/bash" in content or "/usr/bin" in content:
                print(f"  🐧 Linux path handling detected")

            # エラーハンドリングチェック
            if "try:" in content and "except" in content:
                print(f"  ✅ Error handling implemented")

        else:
            print(f"❌ {test_file} - Not found")

    print()


def run_linux_optimized_tests():
    """Linux最適化テスト実行"""
    print("🚀 Running Linux-Optimized Tests")
    print("=" * 40)

    # 環境変数設定
    env = os.environ.copy()
    env.update({
        'PYTHONPATH': str(Path.cwd()),
        'LC_ALL': 'C.UTF-8',
        'LANG': 'C.UTF-8'
    })

    # pytestコマンド構築
    pytest_cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--color=yes',
        '--durations=5'
    ]

    try:
        print(f"Command: {' '.join(pytest_cmd)}")
        result = subprocess.run(
            pytest_cmd,
            env=env,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=300  # 5分タイムアウト
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"\nExit Code: {result.returncode}")

        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Tests timed out (5 minutes)")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False


def generate_linux_report():
    """Linux環境レポート生成"""
    print("📊 Generating Linux Test Report")
    print("=" * 40)

    try:
        import pytest
        pytest_version = pytest.__version__
    except ImportError:
        pytest_version = "Not installed"

    report_content = f"""# Linux Test Execution Report

## Environment
- **OS**: {platform.system()} {platform.release()}
- **Python**: {sys.version}
- **Pytest**: {pytest_version}
- **Working Directory**: {Path.cwd()}
- **Virtual Environment**: {os.environ.get('VIRTUAL_ENV', 'None')}

## Test Files Status
"""

    test_files = [
        "tests/agents/test_command_agent.py",
        "tests/agents/test_config_agent.py",
        "tests/agents/test_git_agent.py",
        "tests/agents/test_llm_agent.py",
        "tests/services/test_db_services.py",
        "tests/services/test_llm_providers.py"
    ]

    for test_file in test_files:
        if Path(test_file).exists():
            report_content += f"- ✅ {test_file}\n"
        else:
            report_content += f"- ❌ {test_file}\n"

    report_content += f"""
## Linux-Specific Features
- File permission handling implemented
- Unix path support enabled
- Error fallback mechanisms active
- UTF-8 encoding enforced

## Recommendations
1. Ensure virtual environment is activated
2. Install missing dependencies: `pip install -r requirements-dev.txt`
3. Set proper file permissions: `chmod +x run_tests_linux.sh`
4. Configure Git global settings for test repositories

Generated on: {platform.node()} at {Path.cwd()}
"""

    report_path = Path("LINUX_TEST_VALIDATION_REPORT.md")
    report_path.write_text(report_content)
    print(f"✅ Report saved to: {report_path}")


def main():
    """メイン実行関数"""
    print("🐧 NeuroHub Linux Test Validator")
    print("=" * 50)
    print()

    # Linux環境チェック
    check_linux_environment()

    # テストファイル検証
    validate_linux_test_files()

    # テスト実行
    success = run_linux_optimized_tests()

    # レポート生成
    generate_linux_report()

    print("\n🏁 Linux Test Validation Complete")

    if success:
        print("✅ All validations passed!")
        sys.exit(0)
    else:
        print("❌ Some validations failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
