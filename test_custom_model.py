"""
カスタムOllamaモデル（neurohub-db-assistant）を使ってコード生成テスト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm_agent import LLMAgent, LLMRequest
import subprocess

print("=" * 80)
print("🤖 カスタムOllamaモデルでコード生成テスト")
print("=" * 80)
print("モデル: neurohub-db-light (軽量版)")
print("説明: READMEのDatabaseManagerサンプルコードを事前学習済み")
print("-" * 80)

# カスタムモデルを直接ollamaコマンドで使用する関数
def generate_with_custom_model(prompt: str, model_name: str = "neurohub-db-light"):
    """カスタムOllamaモデルでコード生成"""
    try:
        # WSL経由でollamaコマンド実行
        cmd = ["wsl", "ollama", "run", model_name, prompt]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120
        )

        if result.returncode == 0:
            return {"success": True, "content": result.stdout}
        else:
            return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "タイムアウト"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# テストケース（1つだけに簡略化）
test_cases = [
    {
        "name": "テスト: 基本的なCRUD操作",
        "prompt": "productsテーブル(id, name, price)を作成して、2件の商品を追加して、全件取得して表示するコードを書いて"
    }
]

results = []

for i, test in enumerate(test_cases, 1):
    print(f"\n{'=' * 80}")
    print(f"📝 {test['name']}")
    print("=" * 80)
    print(f"プロンプト: {test['prompt']}")
    print("-" * 80)

    # コード生成
    print("🤖 コード生成中...")
    result = generate_with_custom_model(test['prompt'])

    if result['success']:
        # コードブロックから抽出
        content = result['content']
        if '```python' in content:
            start = content.find('```python') + len('```python')
            end = content.find('```', start)
            generated_code = content[start:end].strip()
        else:
            generated_code = content.strip()

        print("\n✅ 生成成功!")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # ファイルに保存
        output_file = f"generated_code_test{i}.py"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f'"""\n{test["name"]}\n{test["prompt"]}\n"""\n\n')
            f.write(generated_code)
        print(f"\n💾 {output_file} に保存しました")

        # 実行してみる
        try:
            print(f"\n🚀 生成されたコードを実行します...")
            print("-" * 80)
            exec(generated_code)
            print("-" * 80)
            print("✅ 実行成功!")
            results.append({"test": test['name'], "status": "成功"})
        except Exception as e:
            print(f"❌ 実行エラー: {e}")
            results.append({"test": test['name'], "status": f"エラー: {e}"})
    else:
        print(f"\n❌ 生成失敗: {result.get('error', '不明なエラー')}")
        results.append({"test": test['name'], "status": f"生成失敗: {result.get('error', '不明なエラー')}"})

# 結果サマリー
print("\n" + "=" * 80)
print("📊 テスト結果サマリー")
print("=" * 80)
for i, result in enumerate(results, 1):
    status_icon = "✅" if result['status'] == "成功" else "❌"
    print(f"{status_icon} {result['test']}: {result['status']}")

print("\n" + "=" * 80)
print("🎉 全テスト完了!")
print("=" * 80)
