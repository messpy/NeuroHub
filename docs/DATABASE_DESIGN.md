# NeuroHub データベース設計書

## 📋 概要
NeuroHubプロジェクトの統合データベース設計とCRUD操作インターフェース仕様

## 🏗️ データベース構造

### テーブル一覧

| テーブル名 | 説明 | 主キー | 外部キー |
|------------|------|---------|----------|
| `users` | ユーザー情報 | `user_id` | - |
| `llm_history` | LLM実行履歴 | `id` | `user_id` |
| `llm_sessions` | LLMセッション管理 | `session_id` | `user_id` |
| `knowledge_base` | 知識データベース | `id` | `user_id` |
| `related_questions` | 関連質問 | `id` | `knowledge_id`, `user_id` |
| `command_history` | コマンド履歴 | `id` | `user_id` |

---

## 📊 テーブル詳細設計

### 1. users（ユーザー情報）
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,           -- ユーザーID（ハッシュ値）
    username TEXT UNIQUE NOT NULL,      -- ユーザー名
    email TEXT UNIQUE,                  -- メールアドレス
    full_name TEXT,                     -- フルネーム
    preferred_provider TEXT DEFAULT 'ollama',  -- デフォルトプロバイダー
    provider_config TEXT,               -- JSON: プロバイダー設定
    settings TEXT,                      -- JSON: ユーザー設定
    api_keys TEXT,                      -- JSON: 暗号化APIキー
    usage_stats TEXT,                   -- JSON: 使用統計
    last_login DATETIME,                -- 最終ログイン
    is_active BOOLEAN DEFAULT 1,        -- アクティブ状態
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. llm_history（LLM実行履歴）
```sql
CREATE TABLE llm_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,                    -- セッションID
    user_id TEXT,                       -- ユーザーID
    provider TEXT NOT NULL,             -- プロバイダー名
    model TEXT NOT NULL,                -- モデル名
    request_type TEXT,                  -- リクエスト種別
    prompt_text TEXT,                   -- プロンプト
    response_text TEXT,                 -- レスポンス
    status_code INTEGER,                -- ステータスコード
    success BOOLEAN,                    -- 成功フラグ
    error_message TEXT,                 -- エラーメッセージ
    response_time_ms INTEGER,           -- 応答時間
    token_count_input INTEGER,          -- 入力トークン数
    token_count_output INTEGER,         -- 出力トークン数
    token_count_total INTEGER,          -- 総トークン数
    char_count_input INTEGER,           -- 入力文字数
    char_count_output INTEGER,          -- 出力文字数
    rate_limit_flag BOOLEAN DEFAULT 0,  -- 制限フラグ
    debug_level INTEGER DEFAULT 1,      -- デバッグレベル
    debug_info TEXT,                    -- JSON: デバッグ情報
    metadata TEXT,                      -- JSON: メタデータ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### 3. knowledge_base（知識データベース）
```sql
CREATE TABLE knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                -- タイトル
    content TEXT NOT NULL,              -- 内容
    category TEXT,                      -- カテゴリー
    tags TEXT,                          -- カンマ区切りタグ
    source_type TEXT,                   -- ソース種別
    source_file TEXT,                   -- 元ファイル
    language TEXT,                      -- プログラミング言語
    relevance_score REAL,               -- 関連度スコア
    usage_count INTEGER DEFAULT 0,      -- 使用回数
    user_id TEXT,                       -- 作成者
    is_public BOOLEAN DEFAULT 0,        -- 公開フラグ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### 4. related_questions（関連質問）
```sql
CREATE TABLE related_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER,               -- 知識ベースID
    question TEXT NOT NULL,             -- 質問
    answer TEXT,                        -- 回答
    question_type TEXT,                 -- 質問タイプ
    difficulty_level INTEGER DEFAULT 1, -- 難易度
    tags TEXT,                          -- タグ
    usage_count INTEGER DEFAULT 0,      -- 使用回数
    user_id TEXT,                       -- 作成者
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_base(id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

## 🔧 CRUD操作インターフェース設計

### 基本メソッド命名規則

| 操作 | メソッド名 | 説明 | 例 |
|------|------------|------|-----|
| 作成 | `create_table` | テーブル作成 | `create_table(table_name, schema)` |
| 挿入 | `insert_data` | データ挿入 | `insert_data(table_name, data)` |
| 取得 | `get_data` | データ取得 | `get_data(table_name, conditions)` |
| 更新 | `update_data` | データ更新 | `update_data(table_name, data, conditions)` |
| 削除 | `delete_data` | データ削除 | `delete_data(table_name, conditions)` |
| 検索 | `search_data` | 全文検索 | `search_data(table_name, query)` |
| スキーマ | `get_schema` | テーブル構造取得 | `get_schema(table_name)` |
| カラム | `get_columns` | カラム一覧取得 | `get_columns(table_name)` |

### 統一DBマネージャークラス
```python
class DatabaseManager:
    def __init__(self, db_path: str)

    # テーブル操作
    def create_table(self, table_name: str, schema: str) -> bool
    def drop_table(self, table_name: str) -> bool
    def get_tables(self) -> List[str]
    def get_schema(self, table_name: str) -> Dict[str, Any]
    def get_columns(self, table_name: str) -> List[str]

    # データ操作（CRUD）
    def insert_data(self, table_name: str, data: Dict[str, Any]) -> int
    def get_data(self, table_name: str, conditions: Dict[str, Any] = None,
                limit: int = None, order_by: str = None) -> List[Dict[str, Any]]
    def update_data(self, table_name: str, data: Dict[str, Any],
                   conditions: Dict[str, Any]) -> int
    def delete_data(self, table_name: str, conditions: Dict[str, Any]) -> int

    # 検索・集計
    def search_data(self, table_name: str, query: str,
                   columns: List[str] = None) -> List[Dict[str, Any]]
    def count_data(self, table_name: str, conditions: Dict[str, Any] = None) -> int
    def aggregate_data(self, table_name: str, func: str, column: str,
                      conditions: Dict[str, Any] = None) -> Any

    # カラム操作
    def add_column(self, table_name: str, column_name: str,
                  column_type: str, default_value: Any = None) -> bool
    def drop_column(self, table_name: str, column_name: str) -> bool
    def rename_column(self, table_name: str, old_name: str, new_name: str) -> bool

    # インデックス操作
    def create_index(self, table_name: str, column_names: List[str],
                    index_name: str = None) -> bool
    def drop_index(self, index_name: str) -> bool
    def get_indexes(self, table_name: str) -> List[str]

    # トランザクション
    def begin_transaction(self) -> None
    def commit_transaction(self) -> None
    def rollback_transaction(self) -> None

    # バックアップ・復元
    def backup_table(self, table_name: str, file_path: str) -> bool
    def restore_table(self, table_name: str, file_path: str) -> bool

    # 統計情報
    def get_table_info(self, table_name: str) -> Dict[str, Any]
    def analyze_table(self, table_name: str) -> Dict[str, Any]
```

---

## 📈 インデックス設計

### 主要インデックス

```sql
-- ユーザーテーブル
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- LLM履歴テーブル
CREATE INDEX idx_llm_timestamp ON llm_history(timestamp);
CREATE INDEX idx_llm_provider ON llm_history(provider);
CREATE INDEX idx_llm_user ON llm_history(user_id);
CREATE INDEX idx_llm_success ON llm_history(success);
CREATE INDEX idx_llm_rate_limit ON llm_history(rate_limit_flag);

-- 知識ベーステーブル
CREATE INDEX idx_knowledge_title ON knowledge_base(title);
CREATE INDEX idx_knowledge_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_user ON knowledge_base(user_id);
CREATE INDEX idx_knowledge_public ON knowledge_base(is_public);
CREATE INDEX idx_knowledge_relevance ON knowledge_base(relevance_score);
```

---

## 🔍 全文検索設計

### FTS5仮想テーブル

```sql
-- 知識ベース全文検索
CREATE VIRTUAL TABLE knowledge_base_fts USING fts5(
    title, content, tags,
    content='knowledge_base',
    content_rowid='id'
);

-- 関連質問全文検索
CREATE VIRTUAL TABLE related_questions_fts USING fts5(
    question, answer, tags,
    content='related_questions',
    content_rowid='id'
);

-- LLM履歴全文検索
CREATE VIRTUAL TABLE llm_history_fts USING fts5(
    prompt_text, response_text, error_message,
    content='llm_history',
    content_rowid='id'
);
```

---

## 💻 使用例

### 基本的なCRUD操作
```python
# データベースマネージャー初期化
db = DatabaseManager("neurohub.db")

# ユーザー作成
user_data = {
    "user_id": "user123",
    "username": "kenny",
    "email": "kenny@example.com",
    "preferred_provider": "ollama"
}
db.insert_data("users", user_data)

# ユーザー検索
users = db.get_data("users", {"username": "kenny"})

# 知識ベース追加
knowledge = {
    "title": "Pythonリスト操作",
    "content": "リストの基本操作について...",
    "category": "programming",
    "tags": "python,list,tutorial",
    "user_id": "user123"
}
kb_id = db.insert_data("knowledge_base", knowledge)

# 全文検索
results = db.search_data("knowledge_base", "Python リスト")

# テーブル情報取得
schema = db.get_schema("users")
columns = db.get_columns("llm_history")
```

---

## 🛡️ セキュリティ考慮事項

1. **APIキー暗号化**: `api_keys`フィールドは暗号化して保存
2. **SQLインジェクション対策**: パラメータ化クエリ使用
3. **ユーザー権限**: 公開/非公開データの適切な分離
4. **データバックアップ**: 定期的な自動バックアップ
5. **ログ監査**: 重要操作のログ記録

---

## 📊 パフォーマンス最適化

1. **適切なインデックス**: 検索頻度の高いカラムにインデックス
2. **クエリ最適化**: EXPLAINを使った実行計画確認
3. **バッチ処理**: 大量データ操作時のバッチ処理
4. **接続プール**: 複数接続時のプール管理
5. **キャッシュ**: 頻繁にアクセスされるデータのキャッシュ

---

*最終更新: 2025年11月1日*
