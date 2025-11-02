"""
MCP改善機能テストスクリプト
"""
import subprocess
import sys
from pathlib import Path

def test_mcp_rules():
    """MCPルールファイルの存在確認"""
    print("=" * 80)
    print("1. MCPルールファイル確認")
    print("=" * 80)
    
    rules_file = Path("docs/MCP_CODING_RULES.md")
    if rules_file.exists():
        print(f"✅ {rules_file} が存在します")
        with open(rules_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'input()' in content and '禁止' in content:
                print("✅ input()禁止ルールが含まれています")
            if 'argparse' in content:
                print("✅ argparseルールが含まれています")
        return True
    else:
        print(f"❌ {rules_file} が見つかりません")
        return False

def test_modelfile_generator():
    """Modelfile生成機能のテスト"""
    print("\n" + "=" * 80)
    print("2. Modelfile生成機能テスト")
    print("=" * 80)
    
    try:
        from services.llm.modelfile_generator import ModelfileGenerator
        
        generator = ModelfileGenerator()
        print("✅ ModelfileGeneratorをインポート成功")
        
        # MCP Modelfile生成テスト
        modelfile_path = generator.generate_mcp_modelfile(
            output_name="test_mcp_assistant"
        )
        
        if modelfile_path.exists():
            print(f"✅ Modelfile生成成功: {modelfile_path}")
            with open(modelfile_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'input()は絶対に使用しない' in content:
                    print("✅ input()禁止がModelfileに含まれています")
                if 'argparse' in content:
                    print("✅ argparseがModelfileに含まれています")
            return True
        else:
            print(f"❌ Modelfile生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def test_debugger_improvements():
    """デバッガー改善の確認"""
    print("\n" + "=" * 80)
    print("3. デバッガー改善確認")
    print("=" * 80)
    
    debugger_file = Path("services/mcp/auto_debugger.py")
    if not debugger_file.exists():
        print(f"❌ {debugger_file} が見つかりません")
        return False
    
    with open(debugger_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        checks = [
            ("同じエラーが5回連続", "5回連続終了ロジック"),
            ("input()を使用しています", "input()検出ロジック"),
            ("argparseまたは非対話モード", "argparse推奨メッセージ"),
        ]
        
        all_ok = True
        for check_str, desc in checks:
            if check_str in content:
                print(f"✅ {desc}が実装されています")
            else:
                print(f"❌ {desc}が見つかりません")
                all_ok = False
        
        return all_ok

def test_project_generator_improvements():
    """プロジェクト生成改善の確認"""
    print("\n" + "=" * 80)
    print("4. プロジェクト生成改善確認")
    print("=" * 80)
    
    generator_file = Path("services/mcp/auto_project_generator.py")
    if not generator_file.exists():
        print(f"❌ {generator_file} が見つかりません")
        return False
    
    with open(generator_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        checks = [
            ("input()は絶対に使用禁止", "input()禁止指示"),
            ("--test, --help オプションを必ず実装", "必須オプション指示"),
            ("argparseでコマンドライン引数", "argparse推奨"),
        ]
        
        all_ok = True
        for check_str, desc in checks:
            if check_str in content:
                print(f"✅ {desc}が実装されています")
            else:
                print(f"❌ {desc}が見つかりません")
                all_ok = False
        
        return all_ok

def main():
    """メインテスト実行"""
    print("\n🧪 MCP改善機能テスト開始\n")
    
    results = []
    
    results.append(("MCPルールファイル", test_mcp_rules()))
    results.append(("Modelfile生成機能", test_modelfile_generator()))
    results.append(("デバッガー改善", test_debugger_improvements()))
    results.append(("プロジェクト生成改善", test_project_generator_improvements()))
    
    print("\n" + "=" * 80)
    print("📊 テスト結果サマリー")
    print("=" * 80)
    
    for name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 全テスト成功!")
    else:
        print("⚠️ 一部のテストが失敗しました")
    print("=" * 80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
