"""ollamaにサンプルコードを参照させてDB操作を実行させるテスト"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_llm import LLMAgent, LLMRequest
from pathlib import Path

# READMEのサンプルコードを読み込む
readme_path = Path("generated_projects/テキストエディタ_cli/README.md")
with open(readme_path, 'r', encoding='utf-8') as f:
    readme_content = f.read()

# データベース操作部分を抽出
db_sample_start = readme_content.find("### データベース操作のサンプル")
db_sample_end = readme_content.find("### ファイル操作のサンプル")
db_sample = readme_content[db_sample_start:db_sample_end]

print("=" * 80)
print("🤖 Ollamaにサンプルコードを参照させてDB操作を実行させるテスト")
print("=" * 80)

# LLMエージェント初期化
llm = LLMAgent(provider="ollama")

# プロンプト作成
prompt = f"""以下のREADMEに記載されているDatabaseManagerクラスのサンプルコードを参照して、
次のデータベース操作を実行するPythonコードを生成してください。

{db_sample}

【実行する操作】
1. テーブル作成: users テーブル (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)
2. INSERT: 3人のユーザーを追加
   - ('太郎', 25)
   - ('花子', 30)
   - ('次郎', 28)
3. UPDATE: '太郎'の年齢を26に更新
4. SELECT: 全ユーザーを取得してprint表示（表形式で見やすく）

【要件】
- READMEのDatabaseManagerクラスをそのまま使用してください
- データベースファイル名は 'ollama_test.db' にしてください
- 各操作の前に何をしているか日本語でprint出力してください
- 最後にデータベースをcloseしてください
- コードブロック内にコメントも含めてください
- 実行可能な完全なPythonコードのみを出力してください（説明文は不要）

必ずコードブロック ```python で囲んで出力してください。"""

print("\n🤖 Ollamaにコード生成を依頼中...")
print("-" * 80)

# LLMRequestオブジェクトを作成
request = LLMRequest(
    prompt=prompt,
    system_message="あなたは優秀なPythonプログラマーです。サンプルコードを参照して実行可能なコードを生成してください。",
    request_type="code_generation",
    max_tokens=4000,
    temperature=0.3
)

result = llm.generate_text(request)

if result.is_success:
    # コードブロックから抽出
    content = result.content
    if '```python' in content:
        start = content.find('```python') + len('```python')
        end = content.find('```', start)
        generated_code = content[start:end].strip()
    else:
        generated_code = content.strip()
    print("\n✅ コード生成成功!")
    print("=" * 80)
    print("生成されたコード:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # 生成されたコードをファイルに保存
    output_file = "ollama_db_test.py"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(generated_code)
    print(f"\n💾 コードを {output_file} に保存しました")

    # 生成されたコードを実行
    print("\n🚀 生成されたコードを実行します...")
    print("=" * 80)
    exec(generated_code)
    print("=" * 80)
    print("\n✅ 実行完了!")

else:
    print(f"\n❌ コード生成失敗: {result.error_message or '不明なエラー'}")

print("\n" + "=" * 80)
print("🎉 テスト完了!")
print("=" * 80)
