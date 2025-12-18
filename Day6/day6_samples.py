#read a file
# with open("sample.txt", "r") as file:
#     content = file.read()
#     print(content)

#write to a file    
# with open("sample.txt", "w") as file:
#     file.write("Hello, World!")
#     file.writelines(["Alice", "Bob", "Cherry"])

#try-except box FileNotFoundError, PermissonEror, IOError (input output error)
try:
    with open("sample.txt", "r") as file:
        contennt = file.read()
except FileNotFoundError:
    print(f"File not found! ")