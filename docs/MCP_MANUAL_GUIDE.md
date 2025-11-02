# MCP手動プロンプト実装ガイド

## 🎯 MCPの基本コマンド

### 1. シンプルなプロンプト実行

```bash
# WSL環境で実行
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && python3 -c \"
from agents.llm_agent import LLMAgent, LLMRequest

# LLMエージェント初期化
agent = LLMAgent(provider='ollama')

# プロンプト作成
request = LLMRequest(
    prompt='簡単な計算機プログラムを作成してください。加算、減算、乗算、除算の4つの機能を持つCLIアプリです。',
    system_message='あなたは優秀なPythonプログラマーです。完全に動作するコードを生成してください。',
    request_type='code_generation',
    max_tokens=4000,
    temperature=0.3,
    preferred_provider='ollama'
)

# 実行
response = agent.generate_text(request)
print(response.content)
\""
```

### 2. ファイルから仕様を読み込んで実行

```bash
# 仕様書ファイル作成
cat > /mnt/c/Users/kenny/sandbox/NeuroHub/data/project_plans/my_project_spec.txt << 'EOF'
# プロジェクト仕様

プロジェクト名: todo_cli
説明: SQLiteを使ったTODO管理CLIアプリ

機能:
1. TODO追加 (add コマンド)
2. TODO一覧表示 (list コマンド)
3. TODO完了 (done コマンド)
4. TODO削除 (delete コマンド)

データベース:
- テーブル名: todos
- カラム: id, title, description, status, created_at

CLI引数:
- python todo_cli.py add --title "タスク" --description "説明"
- python todo_cli.py list
- python todo_cli.py done --id 1
- python todo_cli.py delete --id 1
EOF

# Python実行スクリプト
python3 << 'PYTHON_SCRIPT'
from agents.llm_agent import LLMAgent, LLMRequest
from pathlib import Path

# 仕様読み込み
spec_path = Path("/mnt/c/Users/kenny/sandbox/NeuroHub/data/project_plans/my_project_spec.txt")
spec = spec_path.read_text(encoding='utf-8')

# LLMエージェント初期化
agent = LLMAgent(provider='ollama')

# プロンプト作成
prompt = f"""以下の仕様に基づいて、完全に動作するPythonプログラムを生成してください。

{spec}

要件:
1. argparseを使用したCLI実装
2. SQLite3でデータベース操作
3. エラーハンドリング実装
4. 各コマンドの動作確認
5. docstring付きのクラス・メソッド

ファイル構成:
- todo_cli.py: メインプログラム
- test_todo_cli.py: テストコード
"""

request = LLMRequest(
    prompt=prompt,
    system_message="あなたは優秀なPythonプログラマーです。完全に動作するコードを生成してください。",
    request_type='code_generation',
    max_tokens=8000,
    temperature=0.3,
    preferred_provider='ollama'
)

# 実行
response = agent.generate_text(request)

# 結果保存
output_path = Path("/mnt/c/Users/kenny/sandbox/NeuroHub/data/project_plans/todo_cli_response.txt")
output_path.write_text(response.content, encoding='utf-8')

print(f"✅ レスポンス保存: {output_path}")
print(f"プロバイダー: {response.provider}")
print(f"モデル: {response.model}")
print(f"ステータス: {response.status_code}")
PYTHON_SCRIPT
```

### 3. 対話的プロンプト実行

```python
# interactive_mcp.py を作成
from agents.llm_agent import LLMAgent, LLMRequest

def main():
    agent = LLMAgent(provider='ollama')

    print("=" * 80)
    print("MCP 対話的プロンプト実行")
    print("=" * 80)

    while True:
        print("\n何を作成しますか？（'quit'で終了）")
        user_input = input("> ")

        if user_input.lower() == 'quit':
            break

        request = LLMRequest(
            prompt=user_input,
            system_message="あなたは優秀なPythonプログラマーです。",
            request_type='code_generation',
            max_tokens=4000,
            temperature=0.3,
            preferred_provider='ollama'
        )

        print("\n生成中...")
        response = agent.generate_text(request)

        print("\n" + "=" * 80)
        print(response.content)
        print("=" * 80)

if __name__ == "__main__":
    main()
```

## 🎨 プロンプトテンプレート集

### CLI アプリケーション生成

```python
TEMPLATE_CLI_APP = """
以下の仕様でCLIアプリケーションを作成してください。

プロジェクト名: {project_name}
説明: {description}

機能要件:
{features}

技術要件:
- Python 3.12+
- argparse でCLI実装
- {database} でデータ永続化
- エラーハンドリング完備
- テストコード付き

ファイル構成:
- {project_name}.py: メインプログラム
- test_{project_name}.py: pytest テストコード
- README.md: 使用方法
- requirements.txt: 依存関係

各ファイルの内容を完全に実装してください。
"""
```

### Web スクレイパー生成

```python
TEMPLATE_WEB_SCRAPER = """
以下の仕様でWebスクレイパーを作成してください。

対象URL: {target_url}
取得データ: {data_fields}

技術要件:
- requests または BeautifulSoup4 使用
- エラーハンドリング（タイムアウト、404等）
- レート制限対応
- データをCSVまたはJSON形式で保存

実装してください:
1. スクレイピングロジック
2. データ保存機能
3. CLI実行（--url, --output オプション）
4. テストコード
"""
```

### データベース操作ツール生成

```python
TEMPLATE_DB_TOOL = """
以下の仕様でデータベース操作ツールを作成してください。

データベース: {db_type}  # SQLite, MySQL, PostgreSQL
テーブル名: {table_name}
スキーマ:
{schema}

機能:
1. CRUD操作（Create, Read, Update, Delete）
2. 検索機能（条件指定）
3. データインポート/エクスポート
4. バックアップ機能

CLI実行例:
- python db_tool.py create --data '{"name": "test"}'
- python db_tool.py read --id 1
- python db_tool.py update --id 1 --data '{"name": "updated"}'
- python db_tool.py delete --id 1
- python db_tool.py export --output data.json

完全に動作するコードを生成してください。
"""
```

## 🚀 実践例

### Example 1: カレンダーアプリ作成

```bash
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && python3 << 'EOF'
from agents.llm_agent import LLMAgent, LLMRequest

agent = LLMAgent(provider='ollama')

prompt = '''
カレンダーアプリを作成してください。

機能:
1. 予定追加（日時、タイトル、説明）
2. 予定一覧表示（月別、週別、日別）
3. 予定編集
4. 予定削除
5. リマインダー機能

データベース:
- SQLiteで events テーブル
- カラム: id, title, description, start_time, end_time, reminder, created_at

CLI例:
python calendar_cli.py add --title "会議" --start "2025-11-03 10:00" --end "2025-11-03 11:00"
python calendar_cli.py list --month 11
python calendar_cli.py delete --id 1

完全実装をお願いします。
'''

request = LLMRequest(
    prompt=prompt,
    system_message='あなたは優秀なPythonプログラマーです。',
    max_tokens=8000,
    temperature=0.3
)

response = agent.generate_text(request)

# 保存
from pathlib import Path
Path('data/project_plans/calendar_response.txt').write_text(response.content)
print('✅ 生成完了')
EOF
"
```

### Example 2: ファイル整理ツール

```bash
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && python3 << 'EOF'
from agents.llm_agent import LLMAgent, LLMRequest

agent = LLMAgent(provider='ollama')

prompt = '''
ファイル整理ツールを作成してください。

機能:
1. 指定ディレクトリ内のファイルを拡張子別に分類
2. 重複ファイル検出（ハッシュ値比較）
3. ファイルサイズ集計
4. 古いファイル検出（指定日数以上）
5. ドライラン機能（実際に移動せず確認のみ）

CLI例:
python file_organizer.py organize --dir /path/to/dir --dry-run
python file_organizer.py duplicates --dir /path/to/dir
python file_organizer.py cleanup --dir /path/to/dir --days 365

完全実装をお願いします。
'''

request = LLMRequest(prompt=prompt, max_tokens=8000)
response = agent.generate_text(request)

from pathlib import Path
Path('data/project_plans/file_organizer_response.txt').write_text(response.content)
print('✅ 生成完了')
EOF
"
```

## 🔧 高度な使い方

### 1. チャンク処理付きプロンプト

```python
from agents.llm_agent import LLMAgent, LLMRequest

agent = LLMAgent(provider='ollama')

# 大きなプロジェクトは分割して生成
prompts = [
    "Part 1: データベース設計とモデルクラスを作成",
    "Part 2: CLI引数解析とメインロジックを作成",
    "Part 3: テストコードとREADMEを作成"
]

responses = []
for i, prompt_part in enumerate(prompts, 1):
    print(f"\n=== Part {i} 生成中... ===")
    request = LLMRequest(prompt=prompt_part, max_tokens=4000)
    response = agent.generate_text(request)
    responses.append(response.content)

# 統合
final_code = "\n\n".join(responses)
```

### 2. エラーリトライ付き実行

```python
from agents.llm_agent import LLMAgent, LLMRequest
import time

def generate_with_retry(prompt, max_retries=3):
    agent = LLMAgent(provider='ollama')

    for attempt in range(max_retries):
        try:
            request = LLMRequest(prompt=prompt, max_tokens=4000)
            response = agent.generate_text(request)

            if response.status_code == 200:
                return response
            else:
                print(f"エラー: {response.error}, リトライ {attempt + 1}/{max_retries}")
                time.sleep(2)
        except Exception as e:
            print(f"例外発生: {e}, リトライ {attempt + 1}/{max_retries}")
            time.sleep(2)

    return None
```

## 💡 ベストプラクティス

1. **明確な仕様**: データベーススキーマ、CLI例、機能リストを具体的に
2. **段階的生成**: 大きなプロジェクトは機能ごとに分割
3. **テスト重視**: 必ずテストコード生成を依頼
4. **エラーハンドリング**: 例外処理の実装を明示的に要求
5. **ドキュメント**: README、使用例、API仕様を同時生成

## 📝 保存先

生成したコードは以下に保存：
- `data/project_plans/`: 仕様書、プロンプト、レスポンス
- `generated_projects/`: 実装コード
