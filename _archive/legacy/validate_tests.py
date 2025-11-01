# NeuroHub Test Validation Script
# This script validates the test environment setup

import os
import sys
import subprocess
from pathlib import Path

def check_test_files():
    """Check if all required test files exist"""
    print("📁 Checking test file structure...")

    test_files = [
        "tests/agents/test_git_agent.py",
        "tests/agents/test_llm_agent.py",
        "tests/agents/test_config_agent.py",
        "tests/agents/test_command_agent.py",
        "tests/services/test_llm_providers.py",
        "tests/services/test_db_services.py",
        "tests/tools/test_git_commit_ai.sh"
    ]

    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
        else:
            print(f"✅ {test_file}")

    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False

    print("✅ All test files found")
    return True

def check_config_files():
    """Check if configuration files exist"""
    print("\n⚙️  Checking configuration files...")

    config_files = [
        "setup.cfg",
        "requirements-dev.txt",
        ".github/workflows/test.yml"
    ]

    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")
        else:
            print(f"❌ Missing: {config_file}")

def check_source_files():
    """Check if source files exist for testing"""
    print("\n📦 Checking source files...")

    source_files = [
        "agents/git_agent.py",
        "agents/llm_agent.py",
        "agents/config_agent.py",
        "agents/command_agent.py",
        "services/llm/provider_gemini.py",
        "services/llm/provider_ollama.py",
        "services/llm/provider_huggingface.py",
        "services/db/llm_history_manager.py",
        "tools/git_commit_ai"
    ]

    for source_file in source_files:
        if Path(source_file).exists():
            print(f"✅ {source_file}")
        else:
            print(f"⚠️  Not found: {source_file}")

def validate_test_syntax():
    """Validate Python test file syntax"""
    print("\n🔍 Validating test file syntax...")

    test_files = [
        "tests/agents/test_git_agent.py",
        "tests/agents/test_llm_agent.py",
        "tests/agents/test_config_agent.py",
        "tests/agents/test_command_agent.py",
        "tests/services/test_llm_providers.py",
        "tests/services/test_db_services.py"
    ]

    for test_file in test_files:
        if Path(test_file).exists():
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), test_file, 'exec')
                print(f"✅ {test_file} - syntax OK")
            except SyntaxError as e:
                print(f"❌ {test_file} - syntax error: {e}")
            except Exception as e:
                print(f"⚠️  {test_file} - error: {e}")

def main():
    """Main validation function"""
    print("🧪 NeuroHub Test Environment Validation")
    print("=" * 50)

    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    all_checks_passed = True

    # Run checks
    if not check_test_files():
        all_checks_passed = False

    check_config_files()
    check_source_files()
    validate_test_syntax()

    print("\n" + "=" * 50)
    if all_checks_passed:
        print("✅ Test environment validation completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Install dependencies: pip install -r requirements-dev.txt")
        print("   2. Run tests: pytest tests/ -v")
        print("   3. Run with coverage: pytest tests/ --cov=agents --cov=services")
        print("   4. Run all tests: python run_tests.py --all")
    else:
        print("❌ Some issues found in test environment setup")
        sys.exit(1)

if __name__ == "__main__":
    main()
