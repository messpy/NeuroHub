import sys
from typing import List, Dict, Union
import argparse

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
        self.commands = []

    def parse_args(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='Calculate operations with basic arithmetic operators.')
        # Add arguments for each operation
        for op, priority in sorted(self.op_priority.items()):
            parser.add_argument(f'--{op}', action='store_true', help=f'{op} calculation')
        
        return parser

    def run(self) -> None:
        if len(sys.argv) < 2:
            print("Usage: python calculator.py [expression]")
            sys.exit(1)

        expression = sys.argv[1]
        try:
            self.parse_args()
        except Exception as e:
            print(f"Error parsing arguments: {e}")
            sys.exit(1)
        
        for cmd in self.commands:
            if not isinstance(cmd, str) or len(cmd.strip()) == 0:
                continue

            action = cmd.split()[0].strip().lower()
            operands = list(map(float, cmd.split()[1:]))
            try:
                result = eval(action + " ".join([str(i) for i in operands]), {'__builtins__': None}, self.history_stack)
            except Exception as e:
                print(f"Error executing command {cmd}: {e}")
                sys.exit(1)

            # Add the result to the history stack
            self.history_stack.append(result)

    def show_history(self) -> None:
        if not self.history_stack:
            return

        for i in range(len(self.history_stack)):
            print(f"{i+1} - {self.history_stack[i]}")

if __name__ == "__main__":
    calculator = Calculator()
    parser = argparse.ArgumentParser()
    cmd_parser = parser.add_argument_group('Commands')
    cmd_parser.add_argument_group('Options')

    command_args = parser.parse_args()

    if command_args.show_history:
        calculator.show_history()
    else:
        calculator.run()