import argparse
import logging
from pathlib import Path
from sqlite3 import Error as SQLiteError

# エラーハンドリングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except SQLiteError as e:
        logging.error(f"Failed to connect to {db_file}: {e}")
        raise

def create_table(conn, create_table_sql):
    """Create a table from the create_table_sql statement."""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except SQLiteError as e:
        logging.error(f"Failed to create table: {e}")

def main():
    parser = argparse.ArgumentParser(description="数当てゲーム")
    
    # オプションの設定
    parser.add_argument("--db", type=str, default="data.db",
                        help="データベースファイルパス (デフォルトは 'data.db'")
    parser.add_argument("--table_name", type=str, default="numbers",
                        help="テーブル名 (デフォルトは 'numbers' です)")
    
    # 引数の解析
    args = parser.parse_args()
    
    db_path = Path(args.db)
    if not db_path.exists():
        logging.error(f"データベースファイル {db_path} が存在しません")
        return
    
    conn = create_connection(db_path)
    if conn is None:
        return

    # テーブルの作成
    table_create_sql = f"""
CREATE TABLE IF NOT EXISTS {args.table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER UNIQUE NOT NULL
);
"""
    create_table(conn, table_create_sql)

    while True:
        try:
            user_input = input("あなたの数を入力してください (または 'q' で終了): ")
            if user_input.lower() == "q":
                break

            # ユーザーの数をテーブルに保存
            insert_number_sql = f"""
INSERT INTO {args.table_name} (number) VALUES (?);
"""
            conn.execute(insert_number_sql, (int(user_input),))
            logging.info(f"あなたの数: {user_input}")

        except ValueError:
            logging.error("数値が入力されました。再度入力を試してください。")
        except KeyboardInterrupt:
            logging.warning("プログラムを中止しました。")
            break

    conn.close()

if __name__ == "__main__":
    main()