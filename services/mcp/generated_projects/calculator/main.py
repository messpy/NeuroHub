#!/usr/bin/env python3

import sys
import os

def main(input_file):
    with open(input_file, "r") as file:
        data = file.read()
        result = main(data)
    
    print(f"Input data: {data}")
    print(f"Result: {result}")

if __name__ == "__main__":
    input_file = sys.argv[1]
    if os.path.exists(input_file):
        with open(input_file, "r") as file:
            data = file.read()
            result = main(data)
        
        print(f"Input data: {data}")
        print(f"Result: {result}")