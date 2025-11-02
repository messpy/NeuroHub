import os
from colorama import init, Fore, Style

init(autoreset=True)

def test_cli_tool():
    # キーディングシステム設定
    print(f"{Fore.GREEN}成功: タスク完了{Style.RESET_ALL}")
    print(f"{Fore.RED}エラー: ファイルが見つかりません{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}警告: 設定が不完全です{Style.RESET_ALL}")

    # 引数パース
    parser = argparse.ArgumentParser(description="My CLI Tool")
    parser.add_argument("input", help="Input file")

    args = parser.parse_args()

    if args.command == "add":
        print(f"Adding {args.name}")
    else:
        print(f"Unknown command: {args.command}")

    # ドロップアウト：表示に使用する代入型設定
    del_parser = parser.add_subparsers(dest="command")
    del_parser.command = "delete"

    args = parser.parse_args()