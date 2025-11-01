#!/bin/bash
# テスト実行用の簡易スクリプト

cd /mnt/c/Users/kenny/sandbox/NeuroHub
source venv_linux/bin/activate
export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub

echo "=== モジュールインポートテスト ==="
python3 -c "import agents.git_agent; print('✅ Git Agent import successful')"
python3 -c "import agents; print('✅ Agents package import successful')"

echo "=== 単体テスト実行 ==="
python3 -m pytest tests/agents/test_git_agent.py::TestGitAgentCLI::test_cli_multiple_options -v
