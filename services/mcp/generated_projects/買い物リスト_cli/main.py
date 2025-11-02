import argparse
import logging
from typing import Dict, Any

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_items() -> Dict[str, str]:
    """買い物リストの読み込み

    Returns:
        dict: 読み込んだトランザクション履歴の内容
    """
    items_file = "items.txt"
    logger.info(f"読込ファイル：{items_file}")

    with open(items_file, 'r') as file:
        return {line.strip(): '' for line in file.readlines()}

def save_items(transactions: Dict[str, str]) -> None:
    """買い物リストの保存

    Args:
        transactions (dict): 読み込んだトランザクション履歴
    """
    items_file = "items.txt"
    logger.info(f"書き込みファイル：{items_file}")

    with open(items_file, 'w') as file:
        for item in sorted(transactions.keys()):
            file.write(f"{item}\n")

def main() -> None:
    """メインの実行

    パーサーで引数を処理し、必要に応じてトランザクション履歴を読み込む
    または保存する。
    """

    parser = argparse.ArgumentParser(description="買い物リスト管理システム")
    parser.add_argument("--load", action="store_true", help="買い物リストのロード")
    parser.add_argument("--save", action="store_true", help="買い物リストの保存")
    parser.add_argument("--add", type=str, help="アイテムを追加")
    parser.add_argument("--list", action="store_true", help="リスト表示")

    args = parser.parse_args()

    if args.load:
        try:
            transactions = load_items()
            logger.info(f"読み込んだアイテム数: {len(transactions)}")
            for item in transactions:
                print(f"  • {item}")
        except FileNotFoundError:
            logger.warning("items.txtが見つかりません。新規作成します。")
            transactions = {}

    elif args.save:
        # サンプルデータで保存
        transactions = {"牛乳": "", "パン": "", "卵": ""}
        save_items(transactions)
        logger.info("買い物リストを保存しました")

    elif args.add:
        try:
            transactions = load_items()
        except FileNotFoundError:
            transactions = {}
        transactions[args.add] = ""
        save_items(transactions)
        logger.info(f"アイテム'{args.add}'を追加しました")

    elif args.list:
        try:
            transactions = load_items()
            print("📋 買い物リスト:")
            for item in sorted(transactions.keys()):
                print(f"  ✓ {item}")
        except FileNotFoundError:
            logger.warning("リストが空です")

if __name__ == "__main__":
    main()
