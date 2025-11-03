import argparse

def main():
    parser = argparse.ArgumentParser(description="Hello, World!")
    parser.add_argument('text', help='コマンドライン引数を入力してください')
    args = parser.parse_args()

    if not len(args.text) or not args.isnumeric:
        print("Usage: %s <text>" % (sys.argv[0],))
        parser.print_help()
        sys.exit(1)

    text = args.text
    isnumeric = args.isnumeric

if __name__ == "__main__":
    main()