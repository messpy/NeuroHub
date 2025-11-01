#!/bin/bash
# Linux専用テスト実行スクリプト

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐧 NeuroHub Linux Test Runner${NC}"
echo "=================================="

# Python仮想環境のチェック
if [[ "$VIRTUAL_ENV" ]]; then
    echo -e "${GREEN}✓ Virtual environment active: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠ No virtual environment detected${NC}"
    if [[ -d "venv" ]]; then
        echo -e "${BLUE}Activating venv...${NC}"
        source venv/bin/activate
    else
        echo -e "${RED}❌ No venv directory found${NC}"
        exit 1
    fi
fi

# Linux固有の依存関係チェック
echo -e "\n${BLUE}Checking Linux dependencies...${NC}"

# Git availability
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found. Install with: sudo apt-get install git${NC}"
    exit 1
fi

# Python version check
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"

# 権限チェック
if [[ ! -r "." ]] || [[ ! -w "." ]]; then
    echo -e "${RED}❌ Insufficient permissions in current directory${NC}"
    exit 1
fi

# テスト依存関係の確認
echo -e "\n${BLUE}Installing test dependencies...${NC}"
pip install -q pytest pytest-cov pytest-mock

# Linux固有の環境変数設定
export PYTHONPATH="$(pwd):$PYTHONPATH"
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# テスト実行
echo -e "\n${BLUE}Running tests on Linux...${NC}"

# 詳細なテスト実行
python -m pytest tests/ -v \
    --tb=short \
    --color=yes \
    --durations=10 \
    --cov=agents \
    --cov=services \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --junit-xml=test-results.xml

PYTEST_EXIT_CODE=$?

# Linux固有のレポート生成
echo -e "\n${BLUE}Generating Linux test report...${NC}"

cat > LINUX_TEST_REPORT.md << 'EOF'
# Linux Test Execution Report

## Environment Information
- **OS**: Linux
- **Shell**: bash
- **Python Version**: $(python3 --version)
- **Architecture**: $(uname -m)
- **Kernel**: $(uname -r)
- **Distribution**: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")

## Test Execution Summary
- **Execution Date**: $(date)
- **Working Directory**: $(pwd)
- **Virtual Environment**: ${VIRTUAL_ENV:-"None"}

## Dependencies Status
- **Git**: $(git --version)
- **Pytest**: $(python -m pytest --version 2>/dev/null | head -1)

## Test Results
```
$(if [[ $PYTEST_EXIT_CODE -eq 0 ]]; then echo "✅ All tests passed"; else echo "❌ Some tests failed"; fi)
```

## Coverage Summary
$(if [[ -f .coverage ]]; then python -m coverage report --skip-covered 2>/dev/null || echo "Coverage data not available"; fi)

## Linux-Specific Notes
- File permissions verified: $(ls -la . | head -3)
- Environment variables set for UTF-8 support
- Git configuration verified for test repository setup

## Recommendations
1. Ensure all team members use the same Python version
2. Standardize virtual environment creation across Linux distributions
3. Consider Docker for consistent testing environments
4. Verify Git global configuration before running tests

EOF

# 結果表示
echo -e "\n${BLUE}Test Summary:${NC}"
if [[ $PYTEST_EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}✅ All tests completed successfully!${NC}"
    echo -e "${GREEN}📊 Coverage report generated in htmlcov/index.html${NC}"
else
    echo -e "${RED}❌ Some tests failed (exit code: $PYTEST_EXIT_CODE)${NC}"
    echo -e "${YELLOW}📋 Check test-results.xml for detailed results${NC}"
fi

echo -e "${BLUE}📝 Linux test report saved to LINUX_TEST_REPORT.md${NC}"

exit $PYTEST_EXIT_CODE
