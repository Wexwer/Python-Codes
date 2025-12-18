def count_vowels(text):
    vowels = "aeiouAEIOU"
    count = 0
    
    for char in text:
        if char in vowels:
            count += 1
        else:
            pass
    return count


    
inpunt = input("Please enter text: ")

print(f"The number of vowels are: {count_vowels(inpunt)}")