import sys
from typing import List, Dict

class Calculator:
    def __init__(self):
        self.op_priority = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2,
            '(': 0
        }
        self.history_stack: List[float] = []
        self.parse_arguments()

    def parse_arguments(self) -> None:
        parser = argparse.ArgumentParser(description='四則演算ができるコマンドライン計算機')
        
        # コマンドライン引数の入力
        parser.add_argument('command', type=str, help='四則演算したい数学式を入力してください。')
        args = parser.parse_args()
        self.command: str = args.command

    def run(self) -> None:
        try:
            if self.command in ['+', '-', '*', '/', '(', ')']:
                self.calculate_expression()
            else:
                print(" Invalid command. Use '+' or '-' for addition/subtraction, '*' or '/' for multiplication/division, and '(' for parentheses.")
                sys.exit(1)
        except Exception as e:
            logging.error(f" An error occurred while executing '{self.command}'. Error: {e}")

    def calculate_expression(self) -> None:
        # 計算結果を保持するリスト
        self.history_stack.append(float(self._evaluate_expression()))

    def _evaluate_expression(self) -> float:
        if self.command == '+':
            return self.history_stack[-1] + self.history_stack[-2]
        elif self.command == '-':
            return self.history_stack[-1] - self.history_stack[-2]
        elif self.command == '*':
            return self.history_stack[-1] * self.history_stack[-2]
        elif self.command == '/':
            if self.history_stack[-2] != 0:
                return self.history_stack[-1] / self.history_stack[-2]
            else:
                logging.error(" Divison by zero error.")
                sys.exit(1)