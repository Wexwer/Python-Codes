import string

def read_text(filename):
    word_count = {}
    
    with open(filename, "r") as file:
        
        items = file.read().lower().split()
        
        for item in items:
            item = item.strip(string.punctuation)
            if item in word_count:
                word_count[item] += 1
            else:
                word_count[item] = 1
    print(f"The statistics are: {word_count}")

with open("source.txt", "w") as source_file:
    source_file.write("Stefancata Stefancata Stefancata e mnogo qk, ama mnogo qk")


read_text("source.txt")