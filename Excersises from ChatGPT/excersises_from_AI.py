# def prime_check(number):
#     if number > 1:
#         for i in range(2, int(number**0.5) + 1 ):
#             if i % 2 == 0:
#                 print(f"This is not a prime number!")
#             else:
#                 print(f"This is a prime number")       

# prime_check(13)


# def sum(a,b):
#     return a + b

# print(sum(1,2))     

# for i in range(1, 50 + 1):
#     if i % 2 == 0:
#         print(f"{i}")
        
        
# correct_number = int(input("Judge please enter the  correct number: "))

# while True:
#     n = int(input("Which is the correct number "))
#     if n == correct_number:
#         print(f"Congratulations, this is the right number! ")
#         break

# n = int(input("Please input a number: "))
# factorial_result = 1
# while True:
#     factorial_result *= n 
#     n = n - 1
#     if n == 0:
#         print(factorial_result)
#         break




balance_account = 0
while True:
 
    
    print(f"\nMenu")
    print(f"1. Deposit")
    print(f"2. Withdraw")
    print(f"3. Balance Check")
    print(f"4. Exit")

    
    choise = input("Please select your action: ")
    if choise == "4":
        print(f"Exiting, thank you for using us! ")
        break
    
    elif choise == "1":
        deposits = int(input("Please enter the desired amount to be deposited: "))
        balance_account += deposits
        print(f"You have succesfully deposited {deposits:.2f}")
        print(f"\nYour current balance is {balance_account:.2f}")
        
    elif choise == "2":
        withdraw = int(input("Please enter the desired amout to be withdraw: "))
        
        if withdraw > balance_account:
            print(f"You are not able to withdraw {withdraw:.2f} There is not enough balance. ")
            print(f"\nYour current balance is: {balance_account:.2f}")
        else:
            balance_account -= withdraw
            print(f"You have succesfully withdrawn {withdraw:.2f}")
            print(f"\nYour new balance is {balance_account:.2f}")
        
    
        
    elif choise == "3":
        print(f"Your balance in your account is: {balance_account}") 
        
