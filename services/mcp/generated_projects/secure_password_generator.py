#!/usr/bin/env python3
"""
セキュアなパスワード生成ツール

機能:
- 長さ指定可能
- 記号含有オプション
- 複数パスワード生成
- コマンドライン引数対応
"""

import argparse
import secrets
import string
import sys


def generate_password(length: int = 12, include_symbols: bool = True, count: int = 1) -> list:
    """
    セキュアなパスワードを生成

    Args:
        length: パスワードの長さ (デフォルト: 12)
        include_symbols: 記号を含むかどうか (デフォルト: True)
        count: 生成するパスワード数 (デフォルト: 1)

    Returns:
        生成されたパスワードのリスト
    """
    # 文字セット定義
    chars = string.ascii_letters + string.digits

    if include_symbols:
        chars += string.punctuation

    passwords = []

    for _ in range(count):
        # secrets.choice() を使用してセキュアなランダム生成
        password = ''.join(secrets.choice(chars) for _ in range(length))
        passwords.append(password)

    return passwords


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="セキュアなパスワード生成ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デフォルト（12文字、記号含む、1個）
  python3 secure_password_generator.py

  # 長さ16文字、記号なし、3個生成
  python3 secure_password_generator.py -l 16 --no-symbols -c 3

  # 長さ8文字、記号含む、5個生成
  python3 secure_password_generator.py -l 8 -c 5
        """
    )

    parser.add_argument(
        '-l', '--length',
        type=int,
        default=12,
        help='パスワードの長さ (デフォルト: 12)'
    )

    parser.add_argument(
        '--no-symbols',
        action='store_true',
        help='記号を含めない'
    )

    parser.add_argument(
        '-c', '--count',
        type=int,
        default=1,
        help='生成するパスワード数 (デフォルト: 1)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='出力ファイル名（指定しない場合は標準出力）'
    )

    try:
        args = parser.parse_args()

        # 入力値検証
        if args.length < 4:
            print("エラー: パスワードの長さは4文字以上である必要があります", file=sys.stderr)
            sys.exit(1)

        if args.count < 1:
            print("エラー: 生成数は1以上である必要があります", file=sys.stderr)
            sys.exit(1)

        if args.count > 1000:
            print("エラー: 生成数は1000以下である必要があります", file=sys.stderr)
            sys.exit(1)

        # パスワード生成
        include_symbols = not args.no_symbols
        passwords = generate_password(args.length, include_symbols, args.count)

        # 出力
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    for password in passwords:
                        f.write(password + '\n')
                print(f"✅ {len(passwords)}個のパスワードを {args.output} に保存しました")
            except IOError as e:
                print(f"エラー: ファイル出力に失敗しました: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"🔐 生成されたパスワード ({args.count}個):")
            print("-" * 40)
            for i, password in enumerate(passwords, 1):
                print(f"{i:3d}: {password}")
            print("-" * 40)
            print(f"✅ 長さ: {args.length}文字, 記号: {'含む' if include_symbols else '含まない'}")

    except KeyboardInterrupt:
        print("\n⚠️ 操作が中断されました", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
