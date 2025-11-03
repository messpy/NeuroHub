import argparse
import sys

def main():
    # コマンドライン引数パラメータ
    args = argparse.ArgumentParser().parse_args()

    if not len(args.text) or not args.isnumeric:
        print("Usage: hello <text>")
        return 1
    
    text = args.text
    isnumeric = args.isnumeric

if __name__ == "__main__":
    main()