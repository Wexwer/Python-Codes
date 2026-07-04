from itertools import groupby, count

s = input()

for key, group in groupby(s):
    print((len(list(group)), int(key)), end=" ")