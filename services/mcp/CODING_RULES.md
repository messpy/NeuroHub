# MCPコーディングルール（詳細版）

サンプル
## 📋 基本方針

1. **標準ライブラリ優先**: 外部依存を最小限に
2. **argparse必須**: すべてのCLIに`--test`オプション実装
3. **エラー回避**: 5回連続同じエラー時に手法変更
4. **自動テスト対応**: `input()`禁止、タイムアウト回避

## 🚫 絶対禁止事項

### 1. input()の使用

❌ **NG例**:
```python
age = int(input("年齢を入力: "))
```

✅ **OK例**:
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--name", type=str, required=True)
parser.add_argument("--age", type=int, required=True)
parser.add_argument("--test", action="store_true", help="テストモード")
args = parser.parse_args()

if args.test:
    # テストデータ使用
    test_cases = [
        {"name": "太郎", "age": 20},
        {"name": "花子", "age": 25}
    ]
    for case in test_cases:
        process(case["name"], case["age"])
else:
    process(args.name, args.age)
```

### 2. 危険なシステムコマンド

❌ **絶対禁止**:
```python
os.system("rm -rf /")  # 絶対NG
os.system("sudo apt install")  # 絶対NG
```

✅ **推奨**:
```python
from pathlib import Path

# ファイル削除
file_path = Path("data.txt")
if file_path.exists():
    file_path.unlink()

# ディレクトリ削除
dir_path = Path("temp_dir")
if dir_path.exists():
    import shutil
    shutil.rmtree(dir_path)
```

### 3. 手動--help検知

❌ **NG例**:
```python
if "--help" in sys.argv or "-h" in sys.argv:
    print("ヘルプ表示")
    sys.exit(0)
```

✅ **OK例**:
```python
# argparseが自動的に--help, -hを処理
parser = argparse.ArgumentParser(description="アプリ説明")
# 他の引数定義...
```

## ✅ 必須実装パターン

### 1. 標準CLIテンプレート

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
アプリケーション説明
"""

import argparse
import sys
import logging
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_tests():
    """テストモード実行"""
    logger.info("テスト開始")
    
    test_cases = [
        {"input": "test1", "expected": "result1"},
        {"input": "test2", "expected": "result2"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        try:
            result = main_process(case["input"])
            assert result == case["expected"], f"テスト{i}失敗"
            logger.info(f"✅ テスト{i} 成功")
        except Exception as e:
            logger.error(f"❌ テスト{i} 失敗: {e}")
            return False
    
    logger.info("✅ 全テスト成功")
    return True


def main_process(data):
    """メイン処理"""
    # 実装
    return data


def run_application(args):
    """アプリケーション実行"""
    try:
        result = main_process(args.input)
        logger.info(f"結果: {result}")
    except Exception as e:
        logger.error(f"エラー: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="アプリケーション説明",
        epilog="使用例: python main.py --input data --test"
    )
    
    # 必須オプション
    parser.add_argument("--test", action="store_true", 
                       help="テストモード（自動テスト用）")
    
    # アプリ固有オプション
    parser.add_argument("--input", type=str, help="入力データ")
    parser.add_argument("--output", type=str, help="出力先")
    parser.add_argument("--verbose", action="store_true", help="詳細出力")
    
    args = parser.parse_args()
    
    # ログレベル調整
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        if args.test:
            success = run_tests()
            sys.exit(0 if success else 1)
        else:
            run_application(args)
    except KeyboardInterrupt:
        logger.info("\n中断されました")
        sys.exit(0)
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 2. データベース操作テンプレート

```python
import sqlite3
from pathlib import Path
from typing import List, Dict, Any


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path: str = "data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect()
    
    def _connect(self):
        """データベース接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """クエリ実行"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """全レコード取得"""
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def fetch_one(self, query: str, params: tuple = ()) -> Dict[str, Any]:
        """1レコード取得"""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def close(self):
        """接続終了"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 使用例
with DatabaseManager("app.db") as db:
    # テーブル作成
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER
        )
    """)
    
    # データ挿入
    db.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("太郎", 20))
    
    # データ取得
    users = db.fetch_all("SELECT * FROM users")
    for user in users:
        print(f"{user['name']}: {user['age']}歳")
```

### 3. ファイル操作テンプレート

```python
import json
from pathlib import Path
from typing import Any, Dict


def save_json(data: Any, filepath: str):
    """JSON保存"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> Any:
    """JSON読み込み"""
    path = Path(filepath)
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_text(text: str, filepath: str):
    """テキスト保存"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def load_text(filepath: str) -> str:
    """テキスト読み込み"""
    path = Path(filepath)
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# 使用例
data = {"name": "太郎", "age": 20}
save_json(data, "data/user.json")
loaded = load_json("data/user.json")
```

## 🧪 テスト実装ルール

### unittest使用例

```python
import unittest
from main import main_process


class TestMain(unittest.TestCase):
    """メイン処理テスト"""
    
    def setUp(self):
        """テスト前処理"""
        self.test_data = "test"
    
    def tearDown(self):
        """テスト後処理"""
        pass
    
    def test_basic_functionality(self):
        """基本機能テスト"""
        result = main_process(self.test_data)
        self.assertIsNotNone(result)
    
    def test_error_handling(self):
        """エラーハンドリングテスト"""
        with self.assertRaises(ValueError):
            main_process(None)
    
    def test_edge_cases(self):
        """エッジケーステスト"""
        # 空文字列
        result = main_process("")
        self.assertEqual(result, "")
        
        # 長い文字列
        long_text = "a" * 10000
        result = main_process(long_text)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
```

## 📁 プロジェクト構造ルール

```
project_name_cli/
├── main.py                 # メインプログラム
├── test_main.py            # テストコード
├── README.md               # ドキュメント
├── requirements.txt        # 依存関係（必要時のみ）
├── .gitignore              # Git除外設定
├── data/                   # データファイル
│   ├── input/
│   └── output/
├── logs/                   # ログファイル
└── docs/                   # 追加ドキュメント
```

### .gitignore例

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# データ・ログ
data/output/
logs/*.log

# IDE
.vscode/
.idea/
*.swp
```

## 🔍 デバッグガイドライン

### 5回連続エラー回避

```python
MAX_RETRIES = 5
error_history = []

for attempt in range(MAX_RETRIES):
    try:
        result = risky_operation()
        break
    except Exception as e:
        error_history.append(str(e))
        
        if attempt == MAX_RETRIES - 1:
            # 5回失敗時の処理
            logger.error("最大リトライ回数到達")
            logger.error(f"エラー履歴: {error_history}")
            
            # 手法変更
            if all("同じエラー" in err for err in error_history):
                logger.info("手法変更: 別のアプローチを試行")
                result = alternative_approach()
```

## 📚 参考リソース

### 内部ドキュメント
- `docs/MCP_GUIDE.md`: MCP全体ガイド
- `docs/OLLAMA_MODELFILE_GUIDE.md`: Ollamaモデル構築
- `services/mcp/TEMPLATE.md`: プロジェクトテンプレート

### 外部リソース
- Python公式ドキュメント: https://docs.python.org/ja/3/
- argparse: https://docs.python.org/ja/3/library/argparse.html
- pathlib: https://docs.python.org/ja/3/library/pathlib.html

## 🎯 チェックリスト

開発完了前に以下を確認：

- [ ] `input()`を使用していない
- [ ] `argparse`を実装している
- [ ] `--test`オプションがある
- [ ] エラーハンドリング実装済み
- [ ] ロギング実装済み
- [ ] `pathlib`使用（`os.path`は非推奨）
- [ ] 標準ライブラリのみ使用
- [ ] `python -m py_compile main.py` 成功
- [ ] `python main.py --help` タイムアウトなし
- [ ] `python main.py --test` 成功

## 🔄 更新履歴

- **2025-11-02**: 初版作成
  - 詳細テンプレート追加
  - デバッグガイドライン追加
