import os

def test_help():
    # 基本のCLIツール処理
    os.system('my_cli.py --help')
    assert os.name == 'nt' or 'os.name' in globals()

    # パラメーター指定時のテスト
    os.system('my_cli.py file.txt --output out.txt')
    with open(os.devnull, 'w') as dev_null:
        with pytest.raises(SystemExit) as context:
            os.system('my_cli.py file.txt --output out.txt', env={'PYTHONUNBUFFERED': '1'})
    assert type(context.value.code) == int

def test_basic_command():
    # 空のファイルを指定した場合
    os.system('my_cli.py file.txt')
    assert False  # ルートが存在しない場合は出力されるはずだ

if __name__ == '__main__':
    pytest.main(args=['-v', '--cov=.'])