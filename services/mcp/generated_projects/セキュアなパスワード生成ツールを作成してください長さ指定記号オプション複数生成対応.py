if __name__ == "__main__":
    args = parser.parse_args()

if not (args.length and args.symbols):
        print("Usage: python3 [script_name] [-s <length>]")
        sys.exit(1)

    with open('password.txt', 'w') as file:
for symbol in args.symbols:
            password = generate_password(args.length, symbol)
            print(password)

def generate_password(length, symbol):
    # パスワード生成
    pass_str = ''.join(random.choices(pwdgen_symbols, k=length))
    return pass_str

def pwdgen_symbols():
    symbols = string.ascii_letters + string.digits + string.punctuation  # 長さが指定されたならここに指定
    symbol_set = set(symbols)
    password = ''.join(random.sample(symbol_set, length))
    return password

if __name__ == "__main__":
    args = parser.parse_args()

if not (args.length and args.symbols):
        print("Usage: python3 [script_name] [-s <length>]")
        sys.exit(1)

    with open('password.txt', 'w') as file:
for symbol in args.symbols:
            password = generate_password(args.length, symbol)
            file.write(password + "\n")