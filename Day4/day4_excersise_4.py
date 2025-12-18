student_grades = [
    {"name": "Alice", "grade": 6}
    {"name": "Bob", "grade": 5}
    {"name": "Tiger", "grade": 111}
]

total_grades = 0
number_of_studentes = 0

for grade in student_grades:
    total_grades += student_grades["grade"]
    number_of_studentes += 1

average_grade = total_grades / number_of_studentes
print(average_grade)