#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse  # ここにPythonのargparseを使用するためのライブラリをインポート。

parser = argparse.ArgumentParser(description="このファイルでは、足し算と引き算を行うアプリケーションを作成します。")

parser.add_argument("add", type=int, help="加算または減算の数値")
parser.add_argument("sub", type=int, help="減算または加算の数値")
parser.add_argument("exponent", type=int, help="指数の数値")
parser.add_argument("number1", type=int, help="最初の数値")
args = parser.parse_args()

try:
    if args.add == 0 and args.sub == 0:
        # 足し算が0の場合
        result = 0
    elif args.add > 0 and args.sub < 0:
        # 加算と減算の両方を繰り返して計算する
        for i in range(args.add):
            result += args.exponent * (args.number1 + args.exponent)
    elif args.add > 0:
        # 加算のみを行って計算を終了する
        for i in range(args.add):
            result += args.exponent * args.number1
        if args.sub == 0:
            return result

    if args.add < 0 and args.sub >= 0:
        # 减算と加算の両方を繰り返して計算する
        for i in range(args.add):
            result += args.exponent * (args.number1 - args.exponent)
    elif args.add < 0:
        # 减算のみを行って計算を終了する
        if args.sub == 0:
            return result

except ValueError:
    print("エラー: コマンドラインオプションの値が正しくありません。")