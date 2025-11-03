import argparse

def main():
    # コマンドライン引数を取得
    parser = argparse.ArgumentParser(description="Bmi Calculator")
    args = parser.parse_args()

if args.bmi:
        bmi = args.bmi
        height = args.height
        age = args.age
        gender = "male"  # 健康に配慮して指定

        # BMIを計算
        bmi_calculator(bmi, height, age, gender)

        print("BMI:", bmi)
    else:
        parser.print_help()

def bmi_calculator(bmi: float, height: float, age: int, gender: str) -> None:
if gender == "male":
        # 女性の場合
        result = round((bmi - 10.587 * height ** 2 + (height / 3)) / (age * 65.5), 2)
    else:
        # 男性の場合
        result = round(bmi - 4.355, 2)

    print("Result:", result)

if __name__ == "__main__":
    main()