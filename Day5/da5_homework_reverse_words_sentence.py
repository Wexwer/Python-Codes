#Write a program  to reverse the words in a sentence (not the letters)

def palindrome(text):
    text == (char.lower()  for char in text if char.isalnum())
    return text[::-1]

sentence = "Hey My Name is "

print(palindrome(sentence))