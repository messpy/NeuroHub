def main():
    expression = args.expression
    
    try:
        expression = expression.replace(" ", "")
        
        if not expression.isnumeric():
            print("Error: Invalid input.")
            return
        
        # 適切な計算式の表現を求める
        result = eval(expression)
        print(f"{expression} = {result}")
    
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()