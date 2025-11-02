#!/usr/bin/env python3

import sqlite3
from pathlib import Path
import sys
import re
import argparse

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

def main():
    # データベース接続
    db_manager = DatabaseManager('calculator.db')
    
    try:
        while True:
            user_input = input("足し算を入力してください (または 'help' でヘルプを表示): ")
            
            if user_input.lower() == 'help':
                print_help()
                continue
            
            # 強制的に数字や記号以外の文字が含まれている場合、エラー処理
            if not re.match(r'^\d+(\.\d+)?$', user_input):
                raise ValueError("入力は数値または記号のみです。")
            
            # エラーハンドリングを実装
            try:
                result = eval(user_input)
                print(f"結果: {result}")
            except ZeroDivisionError:
                print("エラー: 0で割ることはできません。")
            except Exception as e:
                print(f"エラーが発生しました: {e}")

    finally:
        db_manager.close()

def print_help():
    print("""
足し算アプリケーションのヘルプ

このプログラムは、簡単な計算を実行するためのツールです。

使用方法:
1. 足し算を入力してください (例: 2 + 3)
2. エラーが発生した場合、エラーメッセージが表示されます。
3. 'help' を入力するとこのヘルプメッセージが表示されます。

注意点:
- 無効な文字や記号は受け付けません (例: + - * /)
- 0で割ることはできません
- ゼロ除算のエラーを検出します

使用例:
2 + 3 = 5
10 - 4 = 6
9 * 7 = 63
8 / 2 = 4.0
0 / 0 = ERROR: Division by zero is not allowed.
""")

if __name__ == "__main__":
    main()