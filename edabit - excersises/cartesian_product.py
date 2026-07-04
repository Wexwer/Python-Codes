# input_a = list(map(int, input().split(" ")))
# input_b = list(map(int, input().split(" ")))
#
# result = []
#
# for i in input_a:
#     for b in input_b:
#         result.append(f"({i}, {b})")
#
# result1 = " ".join(map(str, result))
# print(result1)

from itertools import product

input_a = list(map(int, input().split()))
input_b = list(map(int, input().split()))

result = [f"({a}, {b})" for a, b in product(input_a, input_b)]
print(" ".join(result))