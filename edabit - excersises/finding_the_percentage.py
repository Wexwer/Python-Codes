if __name__ == '__main__':
    n = int(input())
    student_marks = {}
    for _ in range(n):
        name, *line = input().split()
        scores = list(map(float, line))
        student_marks[name] = {"scores": scores}
    query_name = input()

    if query_name in student_marks:
       scores = student_marks[query_name]["scores"]
       average = sum(scores)/len(scores)
       print(f"{average:.2f}")