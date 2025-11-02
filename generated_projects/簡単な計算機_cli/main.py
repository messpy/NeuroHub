import sqlite3
from pathlib import Path

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
        try:
            cursor.execute(query, params)
            self.conn.commit()
            return cursor
        except Exception as e:
            print(f"Error executing query: {e}")
    
    def fetch_all(self, query, params=()):
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query, params=()):
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def close(self):
        if self.conn:
            self.conn.close()

def calculator():
    db_manager = DatabaseManager('data.db')
    
    while True:
        try:
            expression = input("Enter an arithmetic expression (or 'help' for help): ")
            
            if expression.lower() == 'help':
                print("Calculator: A simple command-line calculator that supports basic operations (+, -, *, /) and parentheses.")
                continue
            
            # Check for invalid characters
            if not expression.replace(' ', '').isalnum():
                raise ValueError("Invalid input. Please enter a valid arithmetic expression with only digits and operators.")
            
            result = eval(expression)
            print(f"Result: {result}")
        except ZeroDivisionError:
            print("Error: Division by zero is not allowed.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    calculator()