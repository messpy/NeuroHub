# ファイル一覧表示ツール - MCP デモ

このツールは、指定されたディレクトリのファイル一覧を表示するシンプルなMCP（Model Context Protocol）ツールのデモです。

## 機能

- ディレクトリ内のファイル・フォルダ一覧表示
- 再帰的なサブディレクトリ検索
- 隠しファイルの表示オプション
- 拡張子によるフィルタリング
- 複数のソート方法（名前、サイズ、更新日時）
- 複数の出力形式（テーブル、JSON、CSV）

## 使用方法

### 基本的な使用例

```bash
# 現在のディレクトリのファイル一覧
python main.py

# 指定ディレクトリのファイル一覧
python main.py /path/to/directory

# ヘルプ表示
python main.py --help
```

### 高度な使用例

```bash
# 再帰的にサブディレクトリも含める
python main.py -r

# 隠しファイルも表示
python main.py -a

# Python ファイルのみ表示
python main.py --filter .py

# ファイルサイズ順でソート
python main.py --sort size

# JSON 形式で出力
python main.py --format json

# ファイル数のみ表示
python main.py --count
```

## コマンドライン引数

| 引数 | 説明 |
|------|------|
| `directory` | 対象ディレクトリのパス（省略時は現在のディレクトリ） |
| `-r, --recursive` | サブディレクトリも再帰的に表示 |
| `-a, --all` | 隠しファイル（.で始まるファイル）も表示 |
| `--filter EXTENSION` | 拡張子でフィルタ（例: `.py`, `.txt`） |
| `--sort {name,size,modified}` | ソート方法（デフォルト: name） |
| `--format {table,json,csv}` | 出力形式（デフォルト: table） |
| `--count` | ファイル数のみ表示 |

## 出力形式

### テーブル形式（デフォルト）
```
名前                           タイプ      サイズ     更新日時            パス
==========================================================================================
main.py                       file       2.5 KB     2024-11-01 10:30:15 main.py
README.md                     file       1.2 KB     2024-11-01 10:25:30 README.md
```

### JSON形式
```json
[
  {
    "name": "main.py",
    "path": "main.py",
    "absolute_path": "/full/path/to/main.py",
    "type": "file",
    "size": 2567,
    "modified": "2024-11-01 10:30:15",
    "permissions": "644",
    "extension": ".py"
  }
]
```

### CSV形式
```csv
名前,タイプ,サイズ,更新日時,パス
"main.py","file","2.5 KB","2024-11-01 10:30:15","main.py"
"README.md","file","1.2 KB","2024-11-01 10:25:30","README.md"
```

## エラーハンドリング

- 存在しないディレクトリを指定した場合、適切なエラーメッセージが表示されます
- アクセス権限のないファイルは警告メッセージと共にスキップされます
- Ctrl+C での中断に対応しています

## 技術的詳細

- Python 3.6以上が必要
- 標準ライブラリのみを使用（外部依存関係なし）
- クロスプラットフォーム対応（Windows、Linux、macOS）

## MCP統合

このツールは NeuroHub の MCP システムと統合されており、以下のような方法で自動テストできます：

```bash
# MCPテストシステムでの実行例
python main.py --help        # ヘルプ表示テスト
python main.py              # 基本実行テスト
python main.py --count      # ファイル数取得テスト
```

## ライセンス

MIT License - 自由に使用・改変してください。
