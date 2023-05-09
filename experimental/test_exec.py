def add(a, b):
    return a + b

def main():
    global_var = {"result": 20, "add": add}
    exec("result = add(10, 10)", global_var)
    print(global_var["result"])
    sss = 20
    print()
    
if __name__ == "__main__":
    main()