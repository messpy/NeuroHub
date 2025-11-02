# MCP自動コード生成ルール

## 📋 概要

このドキュメントは、MCP（Model Context Protocol）自動プロジェクト生成システムで使用するコーディングルールとベストプラクティスを定義します。

## 🚫 禁止事項

### 1. input()の使用禁止

**理由**: 自動テスト時にタイムアウトが発生する

❌ **禁止**:
```python
while True:
    user_input = input("Enter value: ")
    process(user_input)
```

✅ **推奨** (argparse使用):
```python
import argparse

def main():
    parser = argparse.ArgumentParser(description="アプリ説明")
    parser.add_argument("--value", type=str, help="値を入力")
    parser.add_argument("--test", action="store_true", help="テストモード")
    args = parser.parse_args()
    
    if args.test:
        # テストケース実行
        test_values = ["test1", "test2", "test3"]
        for value in test_values:
            process(value)
    elif args.value:
        process(args.value)
```

### 2. 危険なコマンドの実行禁止

**理由**: システムの安全性を確保する

❌ **絶対禁止**:
- `rm` コマンド（ファイル削除）
- `sudo` コマンド（管理者権限実行）
- `os.system()` による直接のシェルコマンド実行
- `subprocess` で rm, sudo を実行

✅ **推奨**:
- Pythonの標準ライブラリを使用（pathlib, os.remove, shutil など）
- ファイル削除が必要な場合は `pathlib.Path.unlink()` または `os.remove()`
- 権限変更が必要な場合は明示的にドキュメント化

### 3. 外部ライブラリの使用制限

**理由**: 依存関係管理の複雑化を避ける

- ✅ 標準ライブラリのみ使用
- ❌ pip installが必要なライブラリは避ける
- 例外: 明示的に必要な場合のみ requirements.txt に記載

### 4. --helpの手動定義禁止

**理由**: argparseが自動生成するため不要

❌ **禁止**:
```python
if args.help:
    print("ヘルプメッセージ")
```

✅ **推奨**:
```python
# argparseが自動的に--help, -hを処理
parser = argparse.ArgumentParser(description="説明")
```

## ✅ 必須実装項目

### 1. argparseの実装

すべてのCLIアプリケーションに必須：

```python
import argparse

def main():
    parser = argparse.ArgumentParser(description="アプリケーションの説明")
    
    # 最低限必要なオプション
    parser.add_argument("--test", action="store_true", 
                       help="テストモード（自動テスト用）")
    
    # アプリ固有のオプション
    parser.add_argument("--input", type=str, help="入力値")
    parser.add_argument("--output", type=str, help="出力先")
    parser.add_argument("--verbose", action="store_true", help="詳細出力")
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
    else:
        run_application(args)

if __name__ == "__main__":
    main()
```

### 2. エラーハンドリング

```python
try:
    # メイン処理
    result = process_data(data)
except FileNotFoundError as e:
    print(f"ファイルが見つかりません: {e}")
    sys.exit(1)
except ValueError as e:
    print(f"値エラー: {e}")
    sys.exit(1)
except Exception as e:
    print(f"予期しないエラー: {e}")
    sys.exit(1)
```

### 3. ロギング

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("処理開始")
logger.error("エラー発生")
```

## 🛠️ 推奨ツール・パターン

### 1. データベース操作

READMEのDatabaseManagerクラスを使用：

```python
from pathlib import Path
import sqlite3

class DatabaseManager:
    def __init__(self, db_path='data.db'):
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()
    
    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor
    
    def fetch_all(self, query, params=()):
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def close(self):
        if self.conn:
            self.conn.close()
```

### 2. ファイル操作

Pathlibを使用：

```python
from pathlib import Path
import json

def save_json(data, filepath):
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filepath):
    path = Path(filepath)
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

### 3. コマンドライン実行パターン

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from pathlib import Path

def run_tests():
    """テストモード実行"""
    print("テスト実行中...")
    # テストケース実装
    pass

def run_application(args):
    """メインアプリケーション実行"""
    # メイン処理実装
    pass

def main():
    parser = argparse.ArgumentParser(
        description="アプリケーション説明",
        epilog="使用例: python main.py --test"
    )
    
    parser.add_argument("--test", action="store_true", help="テストモード")
    args = parser.parse_args()
    
    try:
        if args.test:
            run_tests()
        else:
            run_application(args)
    except KeyboardInterrupt:
        print("\n中断されました")
        sys.exit(0)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 📁 ファイル配置ルール

### プロジェクト構造

```
project_name_cli/
├── main.py              # メインプログラム（必須）
├── test_main.py         # テストコード（必須）
├── README.md            # ドキュメント（必須）
├── requirements.txt     # 依存関係（外部ライブラリ使用時のみ）
├── data/               # データファイル格納用
├── logs/               # ログファイル格納用
└── docs/               # 追加ドキュメント
```

### ファイル命名規則

- ✅ スネークケース: `my_module.py`
- ❌ キャメルケース: `MyModule.py`
- ✅ 小文字のみ: `utils.py`
- ❌ 大文字混在: `Utils.py`

## 🧪 テスト要件

### 必須テスト項目

1. **構文チェック**: `python -m py_compile main.py`
2. **ヘルプ表示**: `python main.py --help` (タイムアウトなし)
3. **テストモード**: `python main.py --test` (成功終了)

### テストコード例

```python
import unittest
from main import process_data

class TestMain(unittest.TestCase):
    def test_basic_functionality(self):
        result = process_data("test")
        self.assertIsNotNone(result)
    
    def test_error_handling(self):
        with self.assertRaises(ValueError):
            process_data(None)

if __name__ == "__main__":
    unittest.main()
```

## 🔍 デバッグガイドライン

### 自動デバッグ時のヒント活用

1. **ローカル知識ベース**: よくあるエラーパターン
2. **Web検索**: Python公式ドキュメント優先
3. **データベース検索**: 過去の成功パターン
4. **サンプルコード**: READMEのサンプルを参照

### 同じエラーの繰り返し回避

- 5回連続で同じエラー → 手法を変更
- DatabaseManagerサンプルを活用
- 既存の成功パターンをコピー

## 📚 参考リソース

### 内部ドキュメント

- `docs/SEARCH_DB_GUIDE.md` - 検索DB活用方法
- `docs/OLLAMA_MODELFILE_GUIDE.md` - Ollamaモデル構築
- `README.md` - プロジェクト全体の説明

### サンプルコード

生成されたプロジェクトのREADMEに以下が含まれます：

1. DatabaseManagerクラス（完全実装）
2. ファイル操作関数（JSON/テキスト）
3. エラーハンドリングパターン

## 🎯 コード品質チェックリスト

- [ ] input()を使用していない
- [ ] argparseを実装している
- [ ] --testオプションがある
- [ ] エラーハンドリングがある
- [ ] ロギングを実装している
- [ ] Pathlibを使用している
- [ ] 標準ライブラリのみ使用
- [ ] 構文チェックが通る
- [ ] --helpが動作する（タイムアウトなし）
- [ ] --testが成功する

## 🔄 更新履歴

- 2025-11-02: 初版作成
  - input()禁止ルール追加
  - argparse必須化
  - サンプルコード統合
