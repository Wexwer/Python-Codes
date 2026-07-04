from itertools import permutations

# ! User Input
s, k = input().upper().split(" ")
k = int(k)

s = sorted(s)

for p in permutations(s,k):
    print("".join(p))