import math_operations_module as m


# num1 = 10
# num2 = 5

# result = m.multiply(num1, num2)

# print(f"Addition: {result}")



def is_even(number):
    return number % 2 == 0 

def check_number(number):
    if is_even(number):
        print(f"This is a even number: {number}")
    else:
        print(f"This is an odd number: {number}")
        

while True:
    
    print("\nMenu")
    print("1. Check number")
    print("2. Exit programm")
    
    choice = input("Enter the option you want: ")
    
    if choice == "2":
        print("Exiting the programm, thank for using it")
        break
    
    n = int(input("Please enter a number you want to check: "))
    
    check_number(n)