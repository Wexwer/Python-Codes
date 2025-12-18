#Text Cleaner

import re

def clean_text(text):
    #remove punctuation
    text = re.sub(r"[^\w\s]", "", text)
    #Remove extra spaces
    text = " ".join(text.split())
    #Convert to lowercases
    return text.lower()

input_text = "   Hello World!!!. Welcome to Python, Programming....."

cleaned_text = clean_text(input_text)

print(f"Cleaned text: {cleaned_text}")