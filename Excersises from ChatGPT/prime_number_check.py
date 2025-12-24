def is_prime(n):
    return n > 1 and all (n % i != 0 for i in range(2, int(n**0.5) + 1))


while True:
    
    user_input = (input("Enter a number: "))
    
    if user_input == "Stop":
        print(f"Goodbye!")
        break    
    
    
    n = int(user_input)

    if is_prime(n) == True:
        print(f"{n} is a prime number!")
    else:
        print(f"{n} is not a prime number!")
    
        