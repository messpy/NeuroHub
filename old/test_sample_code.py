"""READMEのサンプルコードテスト"""
import sqlite3
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path='data.db'):
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()

    def _connect(self):
        """データベース接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def execute(self, query, params=()):
        """SQLクエリ実行"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
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

# 使用例テスト
print("=" * 60)
print("🧪 DatabaseManagerサンプルコードテスト")
print("=" * 60)

# テストDBを作成
db = DatabaseManager('test_sample.db')

# テーブル作成
print("\n📋 1. テーブル作成")
db.execute('CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT)')
print("✅ items テーブル作成成功")

# データ挿入
print("\n📝 2. データ挿入")
db.execute('INSERT INTO items (name) VALUES (?)', ('サンプル1',))
db.execute('INSERT INTO items (name) VALUES (?)', ('サンプル2',))
db.execute('INSERT INTO items (name) VALUES (?)', ('サンプル3',))
print("✅ 3件のデータを挿入")

# 全件取得
print("\n📊 3. 全件取得")
items = db.fetch_all('SELECT * FROM items')
for item in items:
    print(f"  - ID: {item['id']}, Name: {item['name']}")

# 1件取得
print("\n🔍 4. 1件取得")
item = db.fetch_one('SELECT * FROM items WHERE id = ?', (2,))
if item:
    print(f"  - ID: {item['id']}, Name: {item['name']}")

# 更新
print("\n✏️ 5. データ更新")
db.execute('UPDATE items SET name = ? WHERE id = ?', ('更新されたサンプル', 2))
print("✅ ID=2のデータを更新")

# 更新後の確認
print("\n📊 6. 更新後の全件取得")
items = db.fetch_all('SELECT * FROM items')
for item in items:
    print(f"  - ID: {item['id']}, Name: {item['name']}")

# 削除
print("\n🗑️ 7. データ削除")
db.execute('DELETE FROM items WHERE id = ?', (1,))
print("✅ ID=1のデータを削除")

# 削除後の確認
print("\n📊 8. 削除後の全件取得")
items = db.fetch_all('SELECT * FROM items')
for item in items:
    print(f"  - ID: {item['id']}, Name: {item['name']}")

db.close()

print("\n" + "=" * 60)
print("✅ サンプルコードテスト完了!")
print("=" * 60)
