def reverse_string(text):
    return text[::-1]
    

def count_vowels(text):
    vowels = "aeiouAEIOU"
    count = 0
    
    for char in text:
        if char in vowels:
            count += 1
    return count

def is_palindrome(text):
    cleaned_text = text.replace(" ", "").lower()
    
    return cleaned_text == cleaned_text[::-1]