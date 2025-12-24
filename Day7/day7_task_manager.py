import os

#file to store task
FILE_NAME = "task.txt"

# Load task from file
def load_tasks():
    tasks = {}
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            for line in file:
                task_id, title, status = line.strip().split(" | ")
                tasks[int(task_id)] = {"title": title, "status": status}
    return tasks

#Save task to file
def save_tasks(tasks):
    with open(FILE_NAME, "w") as file:
        for task_id, task in tasks.items():
            file.write(f"{task_id} | {task["title"]} | {task["status"]}\n")
            
            
#Add a new task
def add_task(tasks):
    title = input("Enter task title: ")
    task_id = max(tasks.keys(), default=0) + 1
    tasks[task_id] = {"title": title, "status": "Incomplete"}
    print(f"Task '{title}' added.")        
    
#View all tasks
def view_tasks(tasks):
    if not tasks:
        print("No tasks avaible")
    else:
        for task_id, task in tasks.items():
            print(f"[{task_id}] {task["title"]} - {task['status']}")
            
#Mark task as complete
def mark_task_complete(tasks):
    task_id = int(input("Enter task ID to mark as complete: "))
    if task_id in tasks:
        tasks[task_id]["status"] = "complete"
        print(f"Task '{tasks[task_id]["title"]}' marked as complete")
    else:
        print(f"Task ID not found")
        
#Delete a taks
def delete_task(tasks):
    task_id = int(input("Enter task ID to delete: "))
    if task_id in tasks:
        deleted_tasks = tasks.pop(task_id)
        print(f"Task '{deleted_tasks['title']}' task deleted")
    else:
        print(f"Task ID not found")
        
# Main Menu
def main():
    task = load_tasks()
    while True:
        print("\nTask Manager Menu")
        print(f"1. Add Task")
        print(f"2. View Task")
        print(f"3. Mark Task as Complete")
        print(f"4. Delete Task")
        print(f"5. Exit")
        choice = input("Enter your choice: ")
        
        if choice == "1":
            add_task(task)
        elif choice == "2":
            view_tasks(task)
        elif choice == "3":
            mark_task_complete(task)
        elif choice == "4":
            delete_task(task)
        elif choice == "5":
            save_tasks(task)
            print(f"Goodbye! ")
            break
        else:
            print(f"Invalid Choise. Please try again")

if __name__ == "__main__":    
    main()        