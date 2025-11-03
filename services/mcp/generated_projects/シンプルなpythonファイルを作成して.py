import argparse

# コマンドラインの引数を読み取る (略して)
def main():
    parser = ArgumentParser()
    args = parser.parse_args()

    # プログラムで使用するコマンドライン引数を取得
    usage_text = "usage: %prog --args"
    print(usage_text)