import sys
from typing import List, Dict, Union

class Calculator:
    def __init__(self):
        self.op_priority: Dict[str, int] = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2,
            '(': 0
        }
        self.history_stack: List[float] = []
        self.variables: Dict[str, float] = {}

    def evaluate(self, expression: str) -> float:
        tokens = self.tokenize_expression(expression)
        return eval(tokens)

    @staticmethod
    def tokenize_expression(expression: str) -> List[str]:
        tokens = []
        i = 0
        while i < len(expression):
            if expression[i].isdigit() or (expression[i] == '.' and i + 1 < len(expression) and expression[i + 1].isdigit()):
                start = i
                while i < len(expression) and (
                        expression[i].isdigit() or (i + 1 < len(expression) and expression[i] in '0123456789.')):
                    i += 1
                if i - start > 1:
                    tokens.append(expression[start:i])
            else:
                i += 1
        return tokens

    def parse_expression(self, expr: str):
        tokens = self.tokenize_expression(expr)
        index = len(tokens) - 1
        while index >= 0 and self.op_priority[tokens[index]] > 0:
            if index < len(tokens) - 1 and (tokens[index + 1] in '+-'):
                tokens.insert(index, '('+str(tokens.pop())+'-'+tokens.pop()+')')
                tokens.append('('+str(tokens.pop()), '-', str(tokens.pop()), ')')
                index += 2
            else:
                index -= 1

    def execute_command(self, command):
        parts = command.split()
        if len(parts) == 1:
            return self.evaluate(parts[0])
        elif parts[0] == "history":
            print(" ".join(reversed(self.history_stack)))
        else:
            raise ValueError(f"Invalid syntax: {command}")

    def run(self, command: str):
        tokens = command.replace(' ', '').split()
        if len(tokens) < 2:
            raise ValueError("Not enough arguments")
        operation, operand = float(tokens[0]), float(tokens[1])
        self.history_stack.append(str(operation))
        return operation(operand)

def main():
    calc = Calculator()

    while True:
        user_input = input("> ").strip()
        if user_input.lower() == "exit":
            break
        elif user_input.startswith("--help"):
            print("Calculator commands:")
            print("- 'history': Show previous calculations")
            continue

        try:
            result = calc.run(user_input)
            print(f"Result: {result}")
        except ValueError as e:
            print(e)

if __name__ == "__main__":
    main()