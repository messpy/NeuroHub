import argparse  # 対話式入力モジュールをインポートする
import sys  # コマンドライン引数のインスタンス化

def add(a, b):
    """ 数値を足す関数 """
    return a + b

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="2つの数値を加算します")
    
    parser.add_argument("num1", type=float, help="第一个数字")
    parser.add_argument("num2", type=float, help="第二个数字")

    args = parser.parse_args()
    result = add(args.num1, args.num2)
    print(f"{args.num1} + {args.num2} = {result}")