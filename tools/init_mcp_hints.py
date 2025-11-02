#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP用ヒントデータベース初期データ投入スクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.agent_db import DatabaseAgent


def load_initial_hints():
    """初期ヒントデータ投入"""
    agent = DatabaseAgent()

    print("=" * 60)
    print("MCP用ヒントDB 初期データ投入")
    print("=" * 60)

    # データベースカテゴリのヒント
    database_hints = [
        {
            "keyword": "SQLite CRUD操作",
            "hint_text": "SQLiteCRAUDクラスを使用してデータベース操作を行う。select_where, insert, update_where, delete_whereが基本。",
            "example_code": """from services.db.sqlite_craud import SQLiteCRAUD

db = SQLiteCRAUD("neurohub.db")
# 検索
users = db.select_where("users", where={"active": 1})
# 挿入
db.insert("users", {"name": "John", "email": "john@example.com"})
# 更新
db.update_where("users", {"active": 0}, {"id": 1})""",
            "tags": "database,sqlite,crud",
            "priority": 10
        },
        {
            "keyword": "テーブルスキーマ取得",
            "hint_text": "DatabaseAgentを使用してテーブル構造を確認できる。",
            "example_code": """from agents.agent_db import DatabaseAgent

agent = DatabaseAgent()
schema = agent.get_table_schema("neurohub.db", "users")
print(schema['columns'])  # カラム情報
print(schema['sample_data'])  # サンプルデータ""",
            "tags": "database,schema",
            "priority": 8
        },
        {
            "keyword": "DBトランザクション",
            "hint_text": "SQLiteCRAUDのconnectコンテキストマネージャーを使用して複数操作をトランザクション化。",
            "example_code": """db = SQLiteCRAUD("neurohub.db")
with db.connect() as con:
    con.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    con.execute("INSERT INTO logs (action) VALUES (?)", ("user_added",))
    # commit is automatic""",
            "tags": "database,transaction",
            "priority": 7
        }
    ]

    # CLIカテゴリのヒント
    cli_hints = [
        {
            "keyword": "argparseで引数パース",
            "hint_text": "argparseを使用してCLIツールの引数を定義。サブコマンド、位置引数、オプション引数を設定可能。",
            "example_code": """import argparse

parser = argparse.ArgumentParser(description="My CLI Tool")
parser.add_argument("input", help="Input file")
parser.add_argument("--output", "-o", help="Output file", default="out.txt")
parser.add_argument("--verbose", "-v", action="store_true")

args = parser.parse_args()
print(f"Input: {args.input}, Output: {args.output}")""",
            "tags": "cli,argparse",
            "priority": 9
        },
        {
            "keyword": "サブコマンド実装",
            "hint_text": "argparseのsubparsersを使用して、gitのようなサブコマンド形式のCLIを実装。",
            "example_code": """parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")

# add サブコマンド
add_parser = subparsers.add_parser("add", help="Add item")
add_parser.add_argument("name")

# delete サブコマンド
del_parser = subparsers.add_parser("delete", help="Delete item")
del_parser.add_argument("id", type=int)

args = parser.parse_args()
if args.command == "add":
    print(f"Adding {args.name}")""",
            "tags": "cli,argparse,subcommand",
            "priority": 8
        },
        {
            "keyword": "CLIカラー出力",
            "hint_text": "coloramaを使用してCLI出力に色を付ける。",
            "example_code": """from colorama import init, Fore, Style

init(autoreset=True)

print(f"{Fore.GREEN}成功: タスク完了{Style.RESET_ALL}")
print(f"{Fore.RED}エラー: ファイルが見つかりません{Style.RESET_ALL}")
print(f"{Fore.YELLOW}警告: 設定が不完全です{Style.RESET_ALL}")""",
            "tags": "cli,color,colorama",
            "priority": 6
        }
    ]

    # Webカテゴリのヒント
    web_hints = [
        {
            "keyword": "requestsで HTTPリクエスト",
            "hint_text": "requestsライブラリでHTTP GET/POSTを実行。JSONレスポンスはresponse.json()で取得。",
            "example_code": """import requests

# GET
response = requests.get("https://api.example.com/users")
users = response.json()

# POST
data = {"name": "John", "email": "john@example.com"}
response = requests.post("https://api.example.com/users", json=data)
print(response.status_code)""",
            "tags": "web,http,requests",
            "priority": 9
        },
        {
            "keyword": "BeautifulSoupでスクレイピング",
            "hint_text": "BeautifulSoup4を使用してHTML/XMLをパース。",
            "example_code": """import requests
from bs4 import BeautifulSoup

response = requests.get("https://example.com")
soup = BeautifulSoup(response.text, "html.parser")

# 要素検索
title = soup.find("title").text
links = [a["href"] for a in soup.find_all("a", href=True)]""",
            "tags": "web,scraping,beautifulsoup",
            "priority": 8
        },
        {
            "keyword": "FastAPI REST API",
            "hint_text": "FastAPIで簡単にREST APIを作成。自動ドキュメント生成、型チェック付き。",
            "example_code": """from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    name: str
    email: str

@app.get("/users")
def get_users():
    return [{"id": 1, "name": "Alice"}]

@app.post("/users")
def create_user(user: User):
    return {"id": 2, **user.dict()}""",
            "tags": "web,api,fastapi",
            "priority": 10
        }
    ]

    # LLM/MCPカテゴリのヒント
    mcp_hints = [
        {
            "keyword": "LLMAgentで生成",
            "hint_text": "LLMAgentを使用してコード生成。プロンプトはシステムメッセージ+ユーザープロンプトの組み合わせ。",
            "example_code": """from agents.agent_llm import LLMAgent, LLMRequest

agent = LLMAgent(provider='ollama', model='qwen2.5-coder:3b')
request = LLMRequest(
    prompt="FizzBuzzプログラムを作成してください",
    system_message="あなたは優秀なPythonプログラマーです",
    temperature=0.3,
    max_tokens=2000
)
response = agent.generate_text(request)
print(response.content)""",
            "tags": "llm,mcp,codegen",
            "priority": 10
        },
        {
            "keyword": "プロンプトテンプレート",
            "hint_text": "効果的なプロンプトテンプレートを使用してコード品質を向上。",
            "example_code": """TEMPLATE = '''
あなたは優秀なソフトウェアエンジニアです。

## タスク
{task_description}

## 要件
- Python 3.10以上
- 型ヒント必須
- docstring必須
- エラーハンドリング必須

## 出力形式
Pythonコードのみ出力してください。
'''

prompt = TEMPLATE.format(task_description="Todo管理CLIツール")""",
            "tags": "llm,mcp,prompt",
            "priority": 9
        },
        {
            "keyword": "MCPヒント活用",
            "hint_text": "DatabaseAgentのMCP機能でヒントを検索・活用。",
            "example_code": """from agents.agent_db import DatabaseAgent

agent = DatabaseAgent()

# ヒント検索
hints = agent.search_hints(keyword="SQLite")
for hint in hints:
    print(f"{hint['keyword']}: {hint['hint_text']}")

# ヒント追加
agent.add_mcp_hint(
    category="custom",
    keyword="My Pattern",
    hint_text="説明",
    example_code="コード例"
)""",
            "tags": "mcp,hints,database",
            "priority": 8
        }
    ]

    # 全ヒントを投入
    all_hints = [
        ("database", database_hints),
        ("cli", cli_hints),
        ("web", web_hints),
        ("mcp", mcp_hints)
    ]

    total = 0
    for category, hints in all_hints:
        print(f"\n[{category.upper()}カテゴリ]")
        for hint in hints:
            success = agent.add_mcp_hint(
                category=category,
                **hint
            )
            if success:
                print(f"  ✓ {hint['keyword']}")
                total += 1
            else:
                print(f"  ✗ {hint['keyword']} (失敗)")

    print(f"\n合計 {total} 件のヒントを追加しました。")

    # コードスニペットも追加
    print("\n" + "=" * 60)
    print("コードスニペット追加")
    print("=" * 60)

    snippets = [
        {
            "name": "sqlite_crud_basic",
            "code": """from services.db.sqlite_craud import SQLiteCRAUD

db = SQLiteCRAUD("database.db")
# SELECT
results = db.select_where("table_name", where={"active": 1}, limit=10)
# INSERT
db.insert("table_name", {"name": "value", "status": "active"})
# UPDATE
db.update_where("table_name", {"status": "inactive"}, {"id": 1})
# DELETE
db.delete_where("table_name", {"id": 1})""",
            "description": "SQLiteCRAUD基本操作",
            "category": "database",
            "tags": "sqlite,crud"
        },
        {
            "name": "cli_argparse_template",
            "code": """#!/usr/bin/env python3
import argparse

def main():
    parser = argparse.ArgumentParser(description="CLI Tool")
    parser.add_argument("input", help="Input file")
    parser.add_argument("--output", "-o", default="output.txt")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        print(f"Processing {args.input} -> {args.output}")

    # Your code here

if __name__ == "__main__":
    main()""",
            "description": "CLIツールのargparseテンプレート",
            "category": "cli",
            "tags": "cli,argparse,template"
        },
        {
            "name": "llm_code_generation",
            "code": """from agents.agent_llm import LLMAgent, LLMRequest

agent = LLMAgent(provider='ollama')
request = LLMRequest(
    prompt="タスクの説明",
    system_message="あなたは優秀なプログラマーです",
    temperature=0.3,
    max_tokens=3000
)
response = agent.generate_text(request)
code = response.content

# 生成されたコードをファイルに保存
with open("generated.py", "w") as f:
    f.write(code)""",
            "description": "LLMでコード生成",
            "category": "mcp",
            "tags": "llm,codegen"
        }
    ]

    snippet_count = 0
    for snippet in snippets:
        success = agent.add_code_snippet(**snippet)
        if success:
            print(f"  ✓ {snippet['name']}")
            snippet_count += 1
        else:
            print(f"  ✗ {snippet['name']} (失敗)")

    print(f"\n合計 {snippet_count} 件のスニペットを追加しました。")

    # 統計情報表示
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)

    tables = agent.list_tables(agent.mcp_hints_db)
    print(f"テーブル: {', '.join(tables)}")

    all_hints = agent.search_hints(limit=100)
    print(f"ヒント総数: {len(all_hints)}")

    for cat in ["database", "cli", "web", "mcp"]:
        cat_hints = agent.search_hints(category=cat, limit=100)
        print(f"  - {cat}: {len(cat_hints)}件")

    print(f"\nMCP用ヒントDBパス: {agent.mcp_hints_db}")
    print("初期データ投入完了！")


if __name__ == "__main__":
    load_initial_hints()
