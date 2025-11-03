def main(number1, number2):
    try:
        first_number = int(number1)
        second_number = [int(s) for s in number2]
        
        if len(second_number) == 1:  # 別の数字が無かった場合
            result = first_number + second_number[0]
        else:
            result = first_number - (second_number[0] * 10**len(second_number))
        
        print(f"前後の数を足す：{result}")
    except Exception as e:
        print("エラー:", str(e))