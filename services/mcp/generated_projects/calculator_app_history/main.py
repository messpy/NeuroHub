#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
計算機アプリ - DB履歴付き
計算を実行し、結果をSQLiteデータベースに保存して履歴を表示する
"""

import argparse
import sqlite3
import sys
import datetime
from pathlib import Path

class CalculatorDB:
    """計算履歴を管理するデータベースクラス"""
    
    def __init__(self, db_path: str = "calculator_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベースとテーブルを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expression TEXT NOT NULL,
                    result REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print(f"✅ データベース初期化完了: {self.db_path}")
    
    def save_calculation(self, expression: str, result: float):
        """計算結果をデータベースに保存"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO calculations (expression, result) VALUES (?, ?)",
                (expression, result)
            )
            conn.commit()
            print(f"💾 計算履歴保存: {expression} = {result}")
    
    def get_history(self, limit: int = 10):
        """計算履歴を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT expression, result, timestamp FROM calculations ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()

class Calculator:
    """計算機クラス"""
    
    def __init__(self, db: CalculatorDB):
        self.db = db
    
    def calculate(self, expression: str) -> float:
        """数式を計算し、結果をDBに保存"""
        try:
            # 安全な計算のため、evalの代わりに基本的な演算のみ許可
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                raise ValueError("不正な文字が含まれています")
            
            result = eval(expression)
            self.db.save_calculation(expression, result)
            return result
        except Exception as e:
            print(f"❌ 計算エラー: {e}")
            raise
    
    def show_history(self, limit: int = 10):
        """計算履歴を表示"""
        print(f"\n📋 計算履歴 (最新{limit}件)")
        print("="*50)
        history = self.db.get_history(limit)
        
        if not history:
            print("履歴がありません")
            return
        
        for expression, result, timestamp in history:
            print(f"{timestamp} | {expression} = {result}")
        print("="*50)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="計算機アプリ - DB履歴付き")
    parser.add_argument("--db", default="calculator_history.db", help="データベースファイル名")
    parser.add_argument("--expression", "-e", help="計算式を指定")
    parser.add_argument("--history", action="store_true", help="履歴を表示")
    parser.add_argument("--limit", type=int, default=10, help="履歴表示件数")
    parser.add_argument("--interactive", "-i", action="store_true", help="インタラクティブモード")
    
    args = parser.parse_args()
    
    # データベース初期化
    db = CalculatorDB(args.db)
    calculator = Calculator(db)
    
    try:
        if args.history:
            # 履歴表示
            calculator.show_history(args.limit)
        elif args.expression:
            # 単一計算
            result = calculator.calculate(args.expression)
            print(f"🎯 結果: {args.expression} = {result}")
        elif args.interactive:
            # インタラクティブモード
            print("🧮 計算機インタラクティブモード (終了: quit)")
            while True:
                try:
                    expression = input("計算式を入力 > ").strip()
                    if expression.lower() in ['quit', 'exit', 'q']:
                        break
                    if expression == 'history':
                        calculator.show_history(args.limit)
                        continue
                    
                    result = calculator.calculate(expression)
                    print(f"✅ {expression} = {result}")
                    
                except KeyboardInterrupt:
                    print("\n👋 終了します")
                    break
                except Exception as e:
                    print(f"❌ エラー: {e}")
        else:
            # ヘルプ表示とサンプル実行
            parser.print_help()
            print("📖 使用例:")
            print("  python main.py -e '2 + 3 * 4'  # 単一計算")
            print("  python main.py --history        # 履歴表示")
            print("  python main.py -i              # インタラクティブモード")
            
            # サンプル計算
            print("\n🧪 サンプル計算実行:")
            sample_expressions = ["2 + 3", "10 * 5", "100 / 4", "(3 + 7) * 2"]
            for expr in sample_expressions:
                result = calculator.calculate(expr)
                print(f"  {expr} = {result}")
                
            calculator.show_history(5)
    
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()