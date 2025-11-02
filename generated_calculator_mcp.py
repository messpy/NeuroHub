import argparse
from pathlib import Path

def calculate(num1, num2, operator):
    if operator == '+':
        return num1 + num2
    elif operator == '-':
        return num1 - num2
    elif operator == '*':
        return num1 * num2
    elif operator == '/':
        if num2 == 0:
            raise ValueError("ゼロ除算エラー")
        return num1 / num2
    else:
        raise ValueError("無効な演算子")

def test_calculate():
    assert calculate(1, 2, '+') == 3
    assert calculate(5, 3, '-') == 2
    assert calculate(4, 6, '*') == 24
    assert calculate(8, 2, '/') == 4.0
    print("テストケースが全て成功しました。")

def main():
    parser = argparse.ArgumentParser(description="四則演算ができるCLI計算機")
    parser.add_argument('--num1', type=float, required=True, help='最初の数値')
    parser.add_argument('--num2', type=float, required=True, help='二つ目の数値')
    parser.add_argument('--operator', choices=['+', '-', '*', '/'], required=True, help='演算子 (+, -, *, /)')
    parser.add_argument('--test', action='store_true', help='テストケース実行')

    args = parser.parse_args()

    if args.test:
        test_calculate()
    else:
        try:
            result = calculate(args.num1, args.num2, args.operator)
            print(f"計算結果: {result}")
        except ValueError as e:
            print(f"エラー: {e}")

if __name__ == "__main__":
    main()