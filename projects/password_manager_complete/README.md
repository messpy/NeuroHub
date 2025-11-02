# パスワードマネージャー

Ollama MCP Agent で生成された完全なパスワードマネージャー

## 概要

このパスワードマネージャーは、Ollamaプロバイダーを使用したMCP (Model Context Protocol) Agentによって生成された、完全な機能を持つセキュアなパスワード管理システムです。

### 主な機能

- 🔐 **強力な暗号化**: Fernet対称暗号化によるパスワードの安全な保存
- 🗄️ **SQLiteデータベース**: 軽量で高性能なローカルデータベース
- 🌐 **REST API**: FastAPIベースのWebサービス
- 💻 **CLI ツール**: コマンドライン インターフェース
- 🧪 **包括的テスト**: ユニットテスト・統合テスト完備
- 📝 **完全なドキュメント**: docstring、型ヒント、エラーハンドリング

## 技術スタック

- **言語**: Python 3.8+
- **暗号化**: cryptography (Fernet)
- **データベース**: SQLite3
- **Web フレームワーク**: FastAPI + uvicorn
- **CLI**: Click
- **テスト**: unittest + pytest

## インストール

### 1. 依存関係のインストール

```bash
# 基本的な依存関係
pip install -r requirements.txt

# または個別にインストール
pip install cryptography fastapi uvicorn click
```

### 2. 環境変数の設定

```bash
# マスターパスワード（必須）
export MASTER_PASSWORD="your_secure_master_password"

# API設定（オプション）
export API_HOST="127.0.0.1"
export API_PORT="8000"
export API_TOKEN="your_api_token"
```

## 使用方法

### CLI ツール

#### 基本的な使用方法

```bash
# ヘルプの表示
python cli/manager.py --help

# パスワードの追加
python cli/manager.py add --site "example.com" --username "user@example.com"

# パスワードの取得
python cli/manager.py get --site "example.com" --username "user@example.com" --show-password

# パスワードの一覧表示
python cli/manager.py list

# パスワードの検索
python cli/manager.py search --query "example"

# パスワードの削除
python cli/manager.py delete --site "example.com" --username "user@example.com"

# 安全なパスワードの生成
python cli/manager.py generate --length 20
```

#### 高度な機能

```bash
# クリップボードにコピー
python cli/manager.py get --site "example.com" --copy

# パスワード自動生成で追加
python cli/manager.py add --site "newsite.com" --username "user" --generate

# データベース統計
python cli/manager.py stats --verbose

# カスタムデータベースパス
python cli/manager.py --db-path "custom/path/passwords.db" list
```

### REST API

#### サーバーの起動

```bash
# 開発サーバーの起動
python api/server.py

# 本番環境での起動
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

#### API エンドポイント

```bash
# ヘルスチェック
curl http://localhost:8000/health

# パスワード追加
curl -X POST http://localhost:8000/passwords \\
  -H "Authorization: Bearer your_api_token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "site": "example.com",
    "username": "user@example.com", 
    "password": "secure_password",
    "notes": "重要なアカウント"
  }'

# パスワード取得
curl http://localhost:8000/passwords/example.com?username=user@example.com \\
  -H "Authorization: Bearer your_api_token"

# パスワード一覧
curl http://localhost:8000/passwords \\
  -H "Authorization: Bearer your_api_token"

# パスワード削除
curl -X DELETE http://localhost:8000/passwords/example.com?username=user@example.com \\
  -H "Authorization: Bearer your_api_token"
```

#### API ドキュメント

サーバー起動後、以下のURLでインタラクティブなAPI ドキュメントにアクセスできます：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Python モジュールとして使用

```python
from src.main import PasswordManager

# パスワードマネージャーの初期化
manager = PasswordManager(
    db_path="data/passwords.db",
    master_password="your_master_password"
)

# パスワードの追加
success = manager.add_password(
    site="example.com",
    username="user@example.com",
    password="secure_password",
    notes="重要なアカウント"
)

# パスワードの取得
entry = manager.get_password("example.com", "user@example.com")
if entry:
    print(f"パスワード: {entry['password']}")

# パスワード一覧
entries = manager.list_entries()
for entry in entries:
    print(f"{entry['site']}: {entry['username']}")
```

## ディレクトリ構造

```
password_manager_complete/
├── src/                    # メインソースコード
│   ├── main.py            # エントリーポイント
│   ├── models.py          # データモデル
│   ├── database.py        # データベース操作
│   └── encryption.py      # 暗号化機能
├── api/                   # REST API
│   └── server.py          # FastAPI サーバー
├── cli/                   # CLI ツール
│   └── manager.py         # Click コマンド
├── tests/                 # テストファイル
│   └── test_complete.py   # 包括的テスト
├── data/                  # データディレクトリ
├── requirements.txt       # 依存関係
└── README.md             # このファイル
```

## テスト

### 全テストの実行

```bash
# unittest での実行
python tests/test_complete.py

# pytest での実行（推奨）
pytest tests/ -v

# カバレッジ付きテスト
pytest tests/ --cov=src --cov-report=html
```

### 個別テストの実行

```bash
# 暗号化テストのみ
python -m unittest tests.test_complete.TestEncryptionManager

# データベーステストのみ
python -m unittest tests.test_complete.TestDatabaseManager

# 統合テストのみ
python -m unittest tests.test_complete.TestIntegration
```

## セキュリティ

### 暗号化

- **アルゴリズム**: Fernet（AES 128 in CBC mode with HMAC using SHA256）
- **キー導出**: PBKDF2 with SHA256、100,000回反復
- **ソルト**: 16バイトのランダムソルト

### 認証

- **マスターパスワード**: 全データの暗号化キー生成に使用
- **API トークン**: REST API アクセス用認証（Bearer Token）

### データ保護

- データベースファイルは暗号化されたパスワードのみ保存
- 平文パスワードはメモリ上でのみ存在
- ログにパスワードは記録されない

## 設定

### 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `MASTER_PASSWORD` | マスターパスワード | 対話的入力 |
| `API_HOST` | APIサーバーホスト | `127.0.0.1` |
| `API_PORT` | APIサーバーポート | `8000` |
| `API_TOKEN` | API認証トークン | `password_manager_token_123` |

### データベース設定

- **デフォルトパス**: `data/passwords.db`
- **自動バックアップ**: 今後の機能として予定
- **マイグレーション**: スキーマバージョン管理対応

## トラブルシューティング

### よくある問題

#### 1. cryptography インストールエラー

```bash
# Windowsの場合
pip install --upgrade pip setuptools wheel
pip install cryptography

# Linuxの場合
sudo apt-get install build-essential libffi-dev python3-dev
pip install cryptography
```

#### 2. データベース権限エラー

```bash
# データディレクトリの作成
mkdir -p data
chmod 755 data
```

#### 3. API サーバー起動エラー

```bash
# ポート使用確認
netstat -an | grep :8000

# 別ポートでの起動
export API_PORT=8001
python api/server.py
```

### ログ確認

```bash
# ログファイルの確認
tail -f data/password_manager.log

# デバッグモードでの実行
python cli/manager.py --verbose list
```

## 開発

### 開発環境のセットアップ

```bash
# 開発用依存関係のインストール
pip install -r requirements.txt

# pre-commitフック（オプション）
pip install pre-commit
pre-commit install

# コードフォーマット
black src/ api/ cli/ tests/
isort src/ api/ cli/ tests/

# 型チェック
mypy src/
```

### コントリビューション

1. フォークしてブランチを作成
2. 機能追加・バグ修正
3. テストの追加・実行
4. コードフォーマット
5. プルリクエストの作成

## ライセンス

このプロジェクトはオープンソースで提供されます。

## 生成情報

- **生成者**: Ollama MCP Agent
- **生成モデル**: Ollama
- **生成日時**: 2025年11月3日
- **プロンプト**: ollama_complete_prompt.txt

## サポート

質問や問題がある場合は、以下の方法でサポートを受けることができます：

1. **ドキュメント確認**: このREADMEと各ソースファイルのdocstring
2. **テスト実行**: 問題の再現確認
3. **ログ確認**: エラーメッセージの詳細確認
4. **GitHub Issues**: バグ報告・機能要求

---

**注意**: このパスワードマネージャーは学習・開発目的で作成されました。本番環境での使用前に、セキュリティ監査を実施することを強く推奨します。