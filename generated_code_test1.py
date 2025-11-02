"""
テスト: 基本的なCRUD操作
productsテーブル(id, name, price)を作成して、2件の商品を追加して、全件取得して表示するコードを書いて
"""

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

    def fetch_one(self, query, params=()):
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def close(self):
        if self.conn:
            self.conn.close()


def create_products_table():
    with DatabaseManager() as db_manager:
        # Productsテーブルを作成
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')

        print("Productsテーブル作成しました。")

def add_products():
    with DatabaseManager() as db_manager:
        # 2件の商品を追加
        db_manager.execute('INSERT INTO products (name, price) VALUES (?, ?)', ('Product A', 10.99))
        db_manager.execute('INSERT INTO products (name, price) VALUES (?, ?)', ('Product B', 25.49))

        print("2件の商品を追加しました。")

def fetch_all_products():
    with DatabaseManager() as db_manager:
        # 全件取得して表示
        results = db_manager.fetch_all('SELECT * FROM products')
        
        for result in results:
            product_id, name, price = result['id'], result['name'], result['price']
            print(f"ID: {product_id}, 名称: {name}, 価格: {price}")

def main():
    create_products_table()
    add_products()
    fetch_all_products()

if __name__ == "__main__":
    main()