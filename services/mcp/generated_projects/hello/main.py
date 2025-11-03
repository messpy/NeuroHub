#!/usr/bin/env python

import argparse
import sys

def main():
    # コマンドライン引数の解析
    args = argparse.ArgumentParser().parse_args()
    
    if not len(args.text) or not args.isnumeric:
        print("Usage: %s <text>" % (sys.argv[0],))
        return 1
    
    text = args.text
    isnumeric = args.isnumeric

    # 出力
    with open('output.txt', 'w') as f:
        f.write(text)

if __name__ == "__main__":
    main()