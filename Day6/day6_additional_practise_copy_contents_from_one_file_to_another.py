def write_file(filename, items):
        with open(filename, "w") as file:
            for item in items:
                file.write(item + "\n")

    
def read_file(filename):
    try:
        with open(filename, "r") as file:
            content = file.read() 
            print(f"Items in the file: ")
            print(content)
            return content
            
    except FileNotFoundError:
        print(f"File not found! ")
        
def copy_file(source,destination):
    content = read_file(source)
    with open(destination, "w") as file:
        file.write(content)

text = ["Stefance e nai golemiqt", "Iskam da stana IT"]

write_file("source_file.txt", text)

source_content = read_file("source_file.txt")

copy_file("source_file.txt", "copied_file.txt")

read_file("copied_file.txt")