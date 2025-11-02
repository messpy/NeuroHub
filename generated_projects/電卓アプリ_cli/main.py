#!/usr/bin/env python3

import argparse
import logging
import sys

# ロガーはグローバルに定義し、main関数で設定を初期化します。
logger = logging.getLogger(__name__)

def setup_logging(log_level_str: str):
    """
    ロギングを設定します。

    Args:
        log_level_str (str): 設定するログレベルの文字列 (例: 'INFO', 'DEBUG')
    """
    # 文字列からloggingモジュールのログレベル定数に変換
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # ロギングの基本設定
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # 標準出力にログを出力
        ]
    )
    logger.debug(f"ロギングレベルを '{log_level_str}' に設定しました。")

def calculate(num1_str: str, operator_str: str, num2_str: str) -> float:
    """
    2つの数値と1つの演算子に基づいて計算を実行します。

    Args:
        num1_str (str): 最初の数値の文字列表現。
        operator_str (str): 演算子 ('+', '-', '*', '/') の文字列。
        num2_str (str): 2番目の数値の文字列表現。

    Returns:
        float: 計算結果。

    Raises:
        ValueError: 無効な数値入力または無効な演算子が指定された場合。
        ZeroDivisionError: ゼロによる除算が試行された場合。
    """
    logger.debug(f"計算を開始します: '{num1_str}' '{operator_str}' '{num2_str}'")

    try:
        num1 = float(num1_str)
        num2 = float(num2_str)
    except ValueError:
        logger.error(f"無効な数値が入力されました: '{num1_str}' または '{num2_str}' は数値ではありません。")
        raise ValueError("無効な数値入力です。数値のみを入力してください。")

    logger.debug(f"数値変換成功: num1={num1}, num2={num2}")

    result: float
    if operator_str == '+':
        result = num1 + num2
    elif operator_str == '-':
        result = num1 - num2
    elif operator_str == '*':
        result = num1 * num2
    elif operator_str == '/':
        if num2 == 0:
            logger.error("ゼロ除算はできません。")
            raise ZeroDivisionError("ゼロによる除算は許可されていません。")
        result = num1 / num2
    else:
        logger.error(f"無効な演算子: '{operator_str}'。サポートされている演算子は +, -, *, / です。")
        raise ValueError("無効な演算子です。サポートされている演算子は +, -, *, / です。")
    
    logger.info(f"計算実行: {num1} {operator_str} {num2} = {result}")
    return result

def main():
    """
    CLI電卓アプリのメインエントリポイント。
    コマンドライン引数を解析し、計算を実行して結果を表示します。
    """
    parser = argparse.ArgumentParser(
        description='シンプルなCLI電卓アプリです。2つの数値と1つの演算子を入力して計算します。',
        formatter_class=argparse.RawTextHelpFormatter # ヘルプメッセージの改行を維持
    )
    parser.add_argument(
        'num1',
        type=str,
        help='最初の数値。整数または浮動小数点数を指定してください。例: 10, 3.14'
    )
    parser.add_argument(
        'operator',
        type=str,
        choices=['+', '-', '*', '/'],
        help='実行する演算子。以下のいずれかを指定してください:\n'
             '  + (加算)\n'
             '  - (減算)\n'
             '  * (乗算)\n'
             '  / (除算)'
    )
    parser.add_argument(
        'num2',
        type=str,
        help='2番目の数値。整数または浮動小数点数を指定してください。例: 5, 2.71'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='ログレベルを設定します (デフォルト: INFO)。\n'
             '利用可能なレベル: DEBUG, INFO, WARNING, ERROR, CRITICAL'
    )

    args = parser.parse_args()

    # ロギングの初期設定
    setup_logging(args.log_level)
    logger.debug(f"コマンドライン引数解析完了: num1='{args.num1}', operator='{args.operator}', num2='{args.num2}', log_level='{args.log_level}'")

    try:
        result = calculate(args.num1, args.operator, args.num2)
        print(f"計算結果: {result}")
        sys.exit(0)  # 成功終了
    except (ValueError, ZeroDivisionError) as e:
        # calculate関数内で既に詳細なログが出力されているため、
        # ここではユーザー向けの簡潔なエラーメッセージを表示
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)  # エラー終了
    except Exception as e:
        # 予期せぬその他のエラーを捕捉
        logger.critical(f"予期せぬ重大なエラーが発生しました: {e}", exc_info=True)
        print(f"予期せぬエラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)  # エラー終了

if __name__ == '__main__':
    main()