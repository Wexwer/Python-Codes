students_table = {}

for _ in range(int(input())):
    name = input()
    score = float(input())

    students_table[name] = score


unique_scores = sorted(set(students_table.values()))
second_min = unique_scores[1]

winners = [name for name, score in students_table.items() if score == second_min]
winners.sort()
for name in winners:
    print(name)
