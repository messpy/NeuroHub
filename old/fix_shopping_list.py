#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
買い物リストアプリの自動デバッグスクリプト
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from services.mcp.auto_debugger import AutoDebugger

def main():
    print("🔧 買い物リストアプリ自動デバッグ開始...")
    print("⚙️ エラーが完全に解決されるまで継続します\n")

    debugger = AutoDebugger(provider="ollama")  # ollamaで修正

    # 修正対象ファイル（絶対パス）
    target_file = Path(__file__).parent / "generated_projects" / "買い物リスト_cli" / "main.py"
    target_file = target_file.resolve()

    print(f"📁 対象ファイル: {target_file}\n")

    # 自動デバッグ実行
    result = debugger.test_and_fix_code(
        code_file=target_file,
        project_name="買い物リスト"
    )

    print("\n" + "=" * 60)
    print("🎯 デバッグ結果")
    print("=" * 60)
    print(f"✅ 成功: {result.success}")
    print(f"🔄 試行回数: {result.iterations}")

    if result.success:
        print(f"💾 最終コード長: {len(result.final_code)}")
        print("\n✅ 修正完了！ファイルが更新されました。")
        print(f"\n🎯 実行してみてください:")
        print(f"  python {target_file} --help")
    else:
        print(f"\n❌ 修正失敗")
        if result.error_message:
            print(f"エラー: {result.error_message[:300]}...")

    print("=" * 60)

if __name__ == "__main__":
    main()
