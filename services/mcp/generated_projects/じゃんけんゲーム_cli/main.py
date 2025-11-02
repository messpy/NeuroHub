import argparse
import logging
from random import randint

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# じゃんけんの選択肢
CHOICES = ["グー", "チョキ", "パー"]

def game():
    parser = argparse.ArgumentParser(description='じゃんけんゲーム')

    # 引数設定
    parser.add_argument('--random', action="store_true", help="ランダムの手を選択します")
    parser.add_argument('--difficulty', type=int, choices=range(1, 5), default=2, help="選択肢を指定します (難易度：1-4)")

    args = parser.parse_args()

    # 引数の確認
    if not args.random:
        logging.info("あなたはランダム的手を選択しません。")

    difficulty = 3 - args.difficulty + 1

    # ゲームロジック
    choice = randint(0, 2)
    computer_choice = randint(0, 2)

    result_msg = f"あなたが選んだ手は{CHOICES[choice]}です。\nコンピュータが選んだ手は{CHOICES[computer_choice]}です。\n"

    if choice == computer_choice:
        result_msg += "引き分けです。"
    elif (choice == 0 and computer_choice == 1) or \
         (choice == 1 and computer_choice == 2) or \
         (choice == 2 and computer_choice == 0):
        result_msg += "あなたの勝ちです！"
    else:
        result_msg += "あなたの負けです。"

    return result_msg

def main():
    result = game()
    print(result)

if __name__ == "__main__":
    main()
