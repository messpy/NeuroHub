import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python calculate.py [expression]")
        return
    
    expression = sys.argv[1]
    
    try:
        result = evaluate_expression(expression)
        print(f"The result of {expression} is {result}")
    except Exception as e:
        print(f"Error: {e}")

def evaluate_expression(expression):
    if not expression:
        raise ValueError("Invalid input")
    
    tokens = expression.split()
    operand_stack = []
    for token in tokens:
        if token.isdigit():
            operand_stack.append(int(token))
        else:
            if len(operand_stack) > 0 and operand_stack[-1] == "(":
                result = evaluate_expression(expression)
                for i, token in enumerate(tokens):
                    if token == ")":
                        break
                    elif token == "(": 
                        continue
                    else:
                        if token.isdigit():
                            operand_stack.append(int(token))
                        elif token != "+-*/":
                            raise ValueError("Invalid operator")
                        elif len(operand_stack) > 0 and operand_stack[-1] in ["-", "*", "/"]:
                            result = evaluate_expression(expression)
                            for i, token in enumerate(tokens):
                                if token == ")":
                                    break
                                else:
                                    if token.isdigit():
                                        operand_stack.append(int(token))
                                    elif token != "+-*/":
                                        raise ValueError("Invalid operator")
                                    elif len(operand_stack) > 0 and operand_stack[-1] in ["-", "*", "/"]:
                                        result = evaluate_expression(expression)
                                        for i, token in enumerate(tokens):
                                            if token == ")":
                                                break
                                            else:
                                                if token.isdigit():
                                                    operand_stack.append(int(token))
                                                elif token != "+-*/":
                                                    raise ValueError("Invalid operator")
                                    elif len(operand_stack) > 0 and token not in ["-", "*", "/"]:
                                        result = evaluate_expression(expression)
                                        for i, token in enumerate(tokens):
                                            if token == ")":
                                                break
                                            else:
                                                if token.isdigit():
                                                    operand_stack.append(int(token))
                                                elif token != "+-*/":
                                                    raise ValueError("Invalid operator")
            else:
                operand_stack.append(float(token))
    
    result = evaluate_expression(expression)
    return float(result)

if __name__ == "__main__":
    main()