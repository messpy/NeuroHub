import argparse
from logging import basicConfig, getLogger, INFO

# エラーハンドリングの基底クラス
class ErrorHandler:
    def handle(self, exc):
        print(f"エラーが発生しました: {exc}")
        raise exc  # 原因を残して再投げる

def main():
    parser = argparse.ArgumentParser(description="テキストエディタ")
    parser.add_argument("--edit", action="store_true", help="テキストファイルを編集する")

    args = parser.parse_args()

    try:
        if args.edit:
            # テキストファイルの保存先
            save_path = "edited.txt"

            # テキスト読み込み、編集、保存
            with open("original.txt", 'r') as file, open(save_path, 'w') as new_file:
                content = file.read()
                edited_content = replace_important_words(content)  # ソースコードの代替例を挙げる
                new_file.write(edited_content)
    
    except Exception as exc:
        ErrorHandler().handle(exc)

def replace_important_words(text):
    return text.replace("テキストエディタ", "新しいテキストエディタ")

if __name__ == "__main__":
    basicConfig(level=INFO)  # ログ出力用の設定
    logger = getLogger(__name__)

    try:
        main()
    except Exception as exc:
        ErrorHandler().handle(exc)