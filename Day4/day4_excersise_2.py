#Word Frequency Counter

sentence = input("Enter sentence: ")

#Split the sentence in words

words = sentence.split()

#Intializa a dictionary

world_count = {}

#Count word frequency

for word in words:
    word = word.lower()
    if word in world_count:
        world_count[word] += 1
    else:
        world_count[word] = 1
        
print(world_count)