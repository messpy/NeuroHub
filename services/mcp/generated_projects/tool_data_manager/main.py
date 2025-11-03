def check_and_handle_errors():
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # SQL命令の例（データベース名は実際においてください）
            data_table = "data"
            values = [("John", 10), ("Jane", 20)]

            # 繰り返しの処理
            for row in cursor.execute(f"SELECT * FROM {data_table}"):
                print(f"{row[0]}, {row[1]}")
    except Exception as e:
        logging.error("データベース操作にエラーが発生しました:", str(e))