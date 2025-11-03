def main():
    # エラーレスポンスメッセージを宣言
    error_message = "エラー: 複数キーが指定されており、パスワード生成はできません。\n"
    
    try:
        # 動作確認用ファイルを作成し読み込みます。
        f = open("input.txt", "r")
        input_text = f.read()
        f.close()

        # 重複の値を排除
        unique_values = set(input_text.split())

        for i in range(5):
            # キーワードの生成に使用する値
            key_value_pairs = []
            
            # 1つ目のキーで入力した場合
            if "key_0" in input_text:
                # 入力されたキーバーをキーとセットに代入します。
                unique_values.remove("key_0")
                key_value_pairs.append((input_text.split(":")[0], input_text.split(":")[1]))
            
            # 2つ目のキーで入力した場合
            if "key_1" in input_text:
                # 入力されたキーバーをキーとセットに代入します。
                unique_values.remove("key_1")
                key_value_pairs.append((input_text.split(":")[0], input_text.split(":")[2]))
                
            # 3つ目のキーで入力した場合
            if "key_2" in input_text:
                # 入力されたキーバーをキーとセットに代入します。
                unique_values.remove("key_2")
                key_value_pairs.append((input_text.split(":")[0], input_text.split(":")[3]))

        # 4つ目のキーで入力した場合
        if "key_3" in input_text:
            # 入力されたキーバーをキーとセットに代入します。
            unique_values.remove("key_3")
            key_value_pairs.append((input_text.split(":")[0], input_text.split(":")[4]))

        # 5つ目のキーで入力した場合
        if "key_4" in input_text:
            # 入力されたキーバーをキーとセットに代入します。
            unique_values.remove("key_4")
            key_value_pairs.append((input_text.split(":")[0], input_text.split(":")[5]))

    except Exception as e:
        error_message += f"\nエラー: {str(e)}"

    # メイン処理実行
    main_output = main_key_value(key_value_pairs, unique_values)
    if not main_output:
        raise ValueError(f"値の組み合わせが異常で、キーを生成できませんでした:")
    
    print(main_output)

if __name__ == "__main__":
    main()