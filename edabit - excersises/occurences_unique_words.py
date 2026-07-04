# ! USER INPUT
unique_counter = 0
number_of_words = int(input())

# ! LOGIC
dict = {}

for i in range(number_of_words):
    data = input()
    if data not in dict:
        dict[data] = 0
        unique_counter += 1
    dict[data] += 1

# ! OUTPUT
print(unique_counter)
for value in dict.values():
    print(value, end=" ")

