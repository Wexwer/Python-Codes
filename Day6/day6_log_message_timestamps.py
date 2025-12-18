from datetime import datetime

log_file = "message_log.txt"

while True:
    message = input("Entere your message (or type exit to quit): ")
    
    if message.lower() == "exit":
        print(f"Exiting the programm")
        break
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, "a") as file:
        file.write(f"[{timestamp}] {message}\n")
    
    with open(log_file, "r") as file:
        text = file.readlines()
        for content in text:
            print(content, end="")