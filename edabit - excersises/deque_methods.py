from collections import deque

d = deque()

user_input = int(input())

for i in range(user_input):
    command = input().split()
    if command[0] == "append":
        d.append(int(command[1]))
    if command[0] == "appendleft":
        d.appendleft(int(command[1]))
    if command[0] == "pop":
        d.pop()
    if command[0] == "popleft":
        d.popleft()

for value in d:
    print(value, end=" ")