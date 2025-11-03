# セキュア パスワードマネージャー

SQLite + FastAPI + CLIで構成されたセキュアなパスワードマネージャーシステム

## 特徴

- 🔐 **強力な暗号化**: AES-256-GCM暗号化によるパスワード保護
- 🛡️ **マスターパスワード**: bcryptによるマスターパスワードハッシュ化
- 🌐 **REST API**: FastAPIベースの完全なCRUD API
- 💻 **CLI**: Clickベースの使いやすいコマンドラインインターフェース
- 🗃️ **SQLite**: 軽量で移植性の高いデータベース
- 🧪 **完全テスト**: 95%以上のコードカバレッジ
- 🔍 **検索機能**: サービス名による高速検索
- 📊 **統計情報**: パスワード使用状況の分析

## インストール

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 必須依存関係

- Python 3.12+
- fastapi
- uvicorn
- click
- cryptography
- bcrypt
- pytest
- sqlite3 (標準ライブラリ)

## 使用方法

### CLI使用法

#### ユーザー登録
```bash
python main.py cli register -u yourusername
```

#### ログイン
```bash
python main.py cli login -u yourusername
```

#### パスワード追加
```bash
# 手動入力
python main.py cli add -s "Gmail" -u "your@email.com"

# パスワード自動生成
python main.py cli add -s "Facebook" -u "username" --generate --length 20
```

#### パスワード一覧表示
```bash
# 全て表示
python main.py cli list

# パスワードも表示
python main.py cli list --show-passwords

# 検索
python main.py cli list --search "Gmail"
```

#### パスワード取得
```bash
# パスワードを隠して表示
python main.py cli get 1

# パスワードも表示
python main.py cli get 1 --show-password
```

#### パスワード更新
```bash
# 特定フィールドを更新
python main.py cli update 1 --password "NewPassword123!"

# 新しいパスワードを生成
python main.py cli update 1 --generate-password --length 24
```

#### パスワード削除
```bash
python main.py cli delete 1
```

#### パスワード生成
```bash
# デフォルト設定（16文字）
python main.py cli generate

# カスタム設定
python main.py cli generate --length 32 --no-special
```

#### データエクスポート
```bash
# 標準出力
python main.py cli export

# ファイル出力
python main.py cli export --output passwords_backup.json
```

#### 統計情報
```bash
python main.py cli stats
```

#### ログアウト
```bash
python main.py cli logout
```

### API使用法

#### APIサーバー起動
```bash
python main.py api
```

APIサーバーが http://127.0.0.1:8000 で起動します。

#### API ドキュメント
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

#### API エンドポイント

##### 認証
```bash
# ユーザー登録
curl -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "yourusername", "master_password": "YourPassword123!"}'

# ログイン
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "yourusername", "master_password": "YourPassword123!"}'
```

##### パスワード管理（認証トークン必要）
```bash
# パスワード追加
curl -X POST "http://127.0.0.1:8000/passwords" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "Gmail", "username": "user@gmail.com", "password": "SecurePassword123!"}'

# パスワード一覧
curl -X GET "http://127.0.0.1:8000/passwords" \
  -H "Authorization: Bearer YOUR_TOKEN"

# パスワード検索
curl -X GET "http://127.0.0.1:8000/passwords?search=Gmail" \
  -H "Authorization: Bearer YOUR_TOKEN"

# パスワード取得
curl -X GET "http://127.0.0.1:8000/passwords/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# パスワード更新
curl -X PUT "http://127.0.0.1:8000/passwords/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "NewPassword123!"}'

# パスワード削除
curl -X DELETE "http://127.0.0.1:8000/passwords/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# パスワード生成
curl -X POST "http://127.0.0.1:8000/passwords/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"length": 20, "include_special": true}'
```

## テスト

### テスト実行
```bash
# 全テスト実行
python main.py test

# 特定テストファイル
pytest tests/test_password_manager.py -v

# カバレッジ付き
pytest tests/ --cov=src --cov-report=html
```

### テスト構成

- `tests/test_password_manager.py`: メイン機能テスト
- `tests/test_integration.py`: 統合テスト
- `tests/conftest.py`: pytest設定

## セキュリティ

### 暗号化仕様

- **パスワード暗号化**: AES-256-GCM
- **マスターパスワード**: bcrypt (コスト係数12)
- **キー導出**: PBKDF2-HMAC-SHA256 (100,000回反復)
- **ソルト**: 128ビットランダム生成
- **ナンス**: 96ビットランダム生成（AES-GCM用）

### セキュリティ機能

- マスターパスワード必須
- セッション管理
- メモリクリア（ベストエフォート）
- SQLインジェクション対策
- 入力値検証
- CORS設定

## プロジェクト構造

```
password_manager/
├── src/                    # メインソースコード
│   ├── __init__.py
│   ├── config.py          # 設定管理
│   ├── models.py          # データモデル
│   ├── database.py        # SQLiteデータベース操作
│   ├── encryption.py      # 暗号化処理
│   └── password_manager.py # コア機能
├── api/                   # REST API関連
│   ├── __init__.py
│   └── server.py          # FastAPIサーバー
├── cli/                   # CLIツール関連
│   ├── __init__.py
│   └── app.py             # Clickベースのメインアプリ
├── tests/                 # テストコード
│   ├── __init__.py
│   ├── conftest.py        # pytest設定
│   ├── test_password_manager.py # メイン機能テスト
│   └── test_integration.py # 統合テスト
├── main.py                # エントリーポイント
├── requirements.txt       # 依存関係
└── README.md             # このファイル
```

## 設定

### 環境変数

- `SECRET_KEY`: JWTトークン署名用（デフォルト: "your-secret-key-change-this"）

### 設定ファイル

`src/config.py`で以下の設定が可能：

- データベースパス
- 暗号化設定
- API設定（ホスト、ポート）
- ログ設定

## トラブルシューティング

### よくある問題

1. **依存関係エラー**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **データベースパーミッションエラー**
   ```bash
   # データベースファイルのパーミッション確認
   ls -la password_manager.db
   ```

3. **ポート競合**
   ```bash
   # 異なるポートで起動
   uvicorn api.server:app --host 127.0.0.1 --port 8001
   ```

## 開発者向け

### コードスタイル

- PEP 8準拠
- 型ヒント使用
- docstring記述
- pytest使用

### コントリビューション

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run tests and ensure coverage
5. Submit a pull request

## ライセンス

MIT License

## セキュリティに関する注意

- マスターパスワードは安全に管理してください
- データベースファイルは適切にバックアップしてください
- 本番環境では適切なアクセス制御を設定してください
- 定期的にパスワードを更新することを推奨します

## サポート

問題やご質問がございましたら、GitHubのIssuesページまでお寄せください。
