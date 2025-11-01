#!/usr/bin/env python3
"""
Git Status Helper - 分かりやすいGit状態表示
"""
import subprocess
import sys
from pathlib import Path

def run_git_command(cmd):
    """Gitコマンドを実行"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path.cwd())
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def show_git_status():
    """分かりやすいGit状態表示"""
    print("📊 Git Status Helper")
    print("=" * 50)
    
    # Git状態取得
    rc, output, err = run_git_command("git status --porcelain")
    if rc != 0:
        print(f"❌ Git error: {err}")
        return
    
    if not output:
        print("✅ 変更なし - すべてコミット済み")
        return
    
    lines = output.split('\n')
    modified = []
    untracked = []
    staged = []
    
    for line in lines:
        if not line.strip():
            continue
        
        status = line[:2]
        filename = line[3:].strip()
        
        if status.startswith(' M'):
            modified.append(filename)
        elif status.startswith('??'):
            untracked.append(filename)
        elif status.startswith('A') or status.startswith('M'):
            staged.append(filename)
    
    print(f"📁 合計ファイル数: {len(lines)}")
    print()
    
    if staged:
        print(f"✅ コミット準備済み ({len(staged)}個):")
        for f in staged[:10]:  # 最初の10個だけ表示
            print(f"   📄 {f}")
        if len(staged) > 10:
            print(f"   ... 他 {len(staged) - 10} ファイル")
        print()
    
    if modified:
        print(f"✏️  変更済みファイル ({len(modified)}個):")
        for f in modified[:10]:
            print(f"   📝 {f}")
        if len(modified) > 10:
            print(f"   ... 他 {len(modified) - 10} ファイル")
        print()
    
    if untracked:
        print(f"🆕 新規ファイル ({len(untracked)}個):")
        for f in untracked[:10]:
            print(f"   📄 {f}")
        if len(untracked) > 10:
            print(f"   ... 他 {len(untracked) - 10} ファイル")
    
    print("\n💡 次のステップ:")
    print("   1️⃣  重要なファイルから順番に:")
    print("      git add <ファイル名>")
    print("      git commit -m 'メッセージ'")
    print("   2️⃣  または Git Agent使用:")
    print("      python3 agents/git_agent.py --interactive")

def show_important_files():
    """重要ファイルの優先順位を表示"""
    priority_files = [
        ("agents/__init__.py", "高", "エージェントパッケージ初期化"),
        ("services/llm/llm_cli.py", "高", "LLM CLI修正"),
        ("docs/MCP_GUIDE.md", "中", "MCP包括ドキュメント"),
        ("simple_mcp_test.py", "中", "MCPテストツール"),
        ("mcp_status.py", "中", "MCP状況監視"),
        ("config/config.yaml", "低", "設定ファイル"),
    ]
    
    print("\n🎯 推奨コミット順序:")
    for file, priority, desc in priority_files:
        if Path(file).exists():
            print(f"   {priority:>2} 🔸 {file:<25} - {desc}")

if __name__ == "__main__":
    show_git_status()
    show_important_files()