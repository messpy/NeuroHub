#!/usr/bin/env python3
"""
Git Agent Helper - 1ファイルずつコミットのデモ
"""
import subprocess
import sys
import os
from pathlib import Path

def run_git_command(cmd):
    """Gitコマンドを実行"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path.cwd())
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def commit_single_file(file_path, message):
    """1つのファイルをコミット"""
    print(f"🔍 コミット対象: {file_path}")
    print(f"📝 メッセージ: {message}")

    # ファイルをステージング
    rc, out, err = run_git_command(f'git add "{file_path}"')
    if rc != 0:
        print(f"❌ Add失敗: {err}")
        return False

    # コミット
    rc, out, err = run_git_command(f'git commit -m "{message}"')
    if rc != 0:
        print(f"❌ Commit失敗: {err}")
        return False

    print(f"✅ コミット成功: {file_path}")
    return True

def demo_commits():
    """重要なファイルを順番にコミット"""
    commits = [
        ("agents/__init__.py", "Add agents package initialization file"),
        ("docs/MCP_GUIDE.md", "Add comprehensive MCP system documentation"),
        ("simple_mcp_test.py", "Add simple MCP testing tool without LLM dependency"),
        ("mcp_status.py", "Add MCP system status monitoring tool"),
        ("services/llm/llm_cli.py", "Fix LLM CLI provider calling with proper module execution"),
    ]

    print("🚀 Git Agent Helper - 1ファイルずつコミットデモ")
    print("=" * 50)

    for file_path, message in commits:
        if Path(file_path).exists():
            if commit_single_file(file_path, message):
                print()
            else:
                print(f"⚠️  {file_path} のコミットをスキップ\n")
        else:
            print(f"⚠️  {file_path} が存在しません\n")

    print("📊 最終状態確認:")
    rc, out, err = run_git_command("git status --porcelain")
    if out:
        remaining = len(out.strip().split('\n'))
        print(f"   残り {remaining} ファイル")
    else:
        print("   全てコミット済み")

if __name__ == "__main__":
    demo_commits()
