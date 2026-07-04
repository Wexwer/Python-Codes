n, m = map(int, input().split())

result_a = {}
result_b = {}

for i in range(1, n+1):
    num_input = input()
    if num_input not in result_a:
        result_a[num_input] = []
    result_a[num_input].append(i)

for i in range(1, m+1):
    num_input = input()
    result_b[i] = num_input


for k, v in result_b.items():
    if v in result_a:
        print(*result_a[v])
    else:
        print(-1)

