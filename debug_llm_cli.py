#!/usr/bin/env python3
"""
debug_llm_cli.py - LLM CLIの詳細デバッグ
"""
import sys
import os
import subprocess
sys.path.insert(0, '/mnt/c/Users/kenny/sandbox/NeuroHub')
os.environ['PYTHONPATH'] = '/mnt/c/Users/kenny/sandbox/NeuroHub'
os.environ['OLLAMA_HOST'] = 'http://127.0.0.1:11434'

def test_llm_cli_provider_call():
    """LLM CLIがプロバイダを呼び出す方法をテスト"""

    # LLM CLIと同じ方法でプロバイダを呼び出し
    provider = "ollama"
    model = "qwen2.5:1.5b-instruct"
    prompt = "Return exactly: PONG"

    llm_dir = "/mnt/c/Users/kenny/sandbox/NeuroHub/services/llm"
    impl = f"{llm_dir}/provider_ollama.py"

    cmd = [sys.executable, impl, "--model", model, prompt]
    print(f"Testing command: {' '.join(cmd)}")

    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=llm_dir)
        print(f"Return code: {p.returncode}")
        print(f"Stdout: {p.stdout}")
        print(f"Stderr: {p.stderr}")

        if p.returncode == 0:
            print("✅ プロバイダ呼び出し成功")
        else:
            print("❌ プロバイダ呼び出し失敗")

    except Exception as e:
        print(f"❌ エラー: {e}")

def test_llm_cli_direct():
    """LLM CLI自体を直接テスト"""

    llm_cli = "/mnt/c/Users/kenny/sandbox/NeuroHub/services/llm/llm_cli.py"
    cmd = [sys.executable, llm_cli, "--smart", "Return exactly: PONG"]

    env = os.environ.copy()
    env['LLM_SMART_ORDER'] = 'ollama,huggingface,gemini'

    print(f"Testing LLM CLI: {' '.join(cmd)}")

    try:
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        print(f"Return code: {p.returncode}")
        print(f"Stdout: {p.stdout}")
        print(f"Stderr: {p.stderr}")

        if p.returncode == 0:
            print("✅ LLM CLI 成功")
        else:
            print("❌ LLM CLI 失敗")

    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    print("🔍 LLM CLI デバッグテスト")
    print("=" * 50)

    print("\n1. プロバイダ直接呼び出しテスト:")
    test_llm_cli_provider_call()

    print("\n2. LLM CLI直接テスト:")
    test_llm_cli_direct()
