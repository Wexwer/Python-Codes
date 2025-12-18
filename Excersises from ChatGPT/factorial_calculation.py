n = int(input("Please enter a whole number: "))

factorial_value = 1

while True:
    factorial_value *= n
    n = n - 1
    if n <= 0:
        break

print(f"Factorial of your number is {factorial_value}")