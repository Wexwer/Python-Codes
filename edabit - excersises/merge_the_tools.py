import textwrap
# ! User Input
k = 3
string = input()

# ! Logic
chunk = textwrap.wrap(string, k)
for i in chunk:
    cleaned = ''.join(dict.fromkeys(i))
    print(cleaned)

