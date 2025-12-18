# Define varibale of different data types

integer_var = 10 
float_var = 3.14
string_var = "AI"
list_var = [1, 2, 3]
tuple_var = (4, 5, 6)
dict_var = {"name:" "Alice", "role:" "Engineer", "gendar:" "Male"}
bool_var = True


print(f"Integer: {integer_var}")
print(f"Float: {float_var}")
print(f"String: {string_var} + Bootcamp")
list_var.append(4)
print(f"List: {list_var}")
print(f"Tupple: {tuple_var}")
print(f"Dictionary Value: {dict_var}")
print(f"Boolean: {bool_var}")


fruits = ["apple", "cherry", "orange"]
for fruit in fruits:
    print(f"This is a {fruit}")

# prime numbers
num = int(input("Enter a number: "))

if num > 1:
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            print(f"{num} is not a prime number")
            break
    else:
        print(f"{num} is a prime number")
else:
    print(f"{num} is not a prime number")