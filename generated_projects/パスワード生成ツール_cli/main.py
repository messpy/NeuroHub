import argparse
from getpass import getpass  # 編集後に確認すると必要性が消失する可能性があるためコメントアウト


def generate_password(length=12):
    """ランダムなパスワードを生成する関数"""
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    password = ''
    for _ in range(length):
        password += getpass(f"password{random.choice(characters)}")
    return password


def main():
    parser = argparse.ArgumentParser(description="パスワード生成ツール")

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        exit(0)

    try:
        length = int(input("パスワードの長さを入力してください (12以上で適切): "))
        password = generate_password(length)
        print(f"生成されたパスワード: {password}")
    except ValueError as e:
        logging.error(str(e))
        print("エラーが発生しました。再度実行してください。")
    except Exception as e:
        logging.error(str(e))
        print("システムのエラーが発生しました。")


if __name__ == "__main__":
    main()