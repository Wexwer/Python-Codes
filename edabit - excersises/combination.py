from itertools import combinations

# ! User Input
s, k = input().upper().split(" ")
k = int(k)
s = sorted(s)

for r in range(1, k +1):
    for c in combinations(s,r):
        print("".join(c))
