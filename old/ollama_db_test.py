import sqlite3
from pathlib import Path

# READMEに記載されているDatabaseManagerクラス
class DatabaseManager:
    def __init__(self, db_path='data.db'):
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()
    
    def _connect(self):
        """データベース接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row # カラム名でアクセスできるように設定
    
    def execute(self, query, params=()):
        """SQLクエリ実行"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit() # 変更をコミット
        return cursor
    
    def fetch_all(self, query, params=()):
        """全件取得"""
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query, params=()):
        """1件取得"""
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def close(self):
        """接続を閉じる"""
        if self.conn:
            self.conn.close()

# データベース操作の実行
if __name__ == "__main__":
    db_file_name = 'ollama_test.db'
    db = DatabaseManager(db_file_name)

    try:
        # 1. テーブル作成: users テーブル (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)
        print("--- 1. テーブル作成: 'users' テーブルを作成します ---")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER
        )
        """
        db.execute(create_table_query)
        print("テーブル 'users' が作成されました。")

        # 2. INSERT: 3人のユーザーを追加
        print("\n--- 2. ユーザーを3人追加します ---")
        users_to_insert = [
            ('太郎', 25),
            ('花子', 30),
            ('次郎', 28)
        ]
        for name, age in users_to_insert:
            db.execute('INSERT INTO users (name, age) VALUES (?, ?)', (name, age))
            print(f"ユーザー '{name}' (年齢: {age}) を追加しました。")

        # 3. UPDATE: '太郎'の年齢を26に更新
        print("\n--- 3. '太郎'の年齢を26に更新します ---")
        db.execute('UPDATE users SET age = ? WHERE name = ?', (26, '太郎'))
        print("'太郎'の年齢を26に更新しました。")

        # 4. SELECT: 全ユーザーを取得してprint表示（表形式で見やすく）
        print("\n--- 4. 全ユーザーを取得して表示します ---")
        all_users = db.fetch_all('SELECT id, name, age FROM users')

        if all_users:
            # ヘッダーの表示
            print(f"{'ID':<5} {'名前':<10} {'年齢':<5}")
            print(f"{'-'*5} {'-'*10} {'-'*5}")
            # 各ユーザーのデータを表示
            for user in all_users:
                print(f"{user['id']:<5} {user['name']:<10} {user['age']:<5}")
        else:
            print("ユーザーが見つかりませんでした。")

    except sqlite3.Error as e:
        print(f"データベース操作中にエラーが発生しました: {e}")
    finally:
        # 最後にデータベースをclose
        print(f"\n--- データベース '{db_file_name}' への接続を閉じます ---")
        db.close()
        print("接続が閉じられました。")