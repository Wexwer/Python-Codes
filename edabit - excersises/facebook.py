followers = {}

while True:
    command = input()
    if command == "Log out":
        break

    parts = command.split(": ")

    if parts[0] == "New follower":
        username = parts[1]
        if username not in followers:
            followers[username] = {"likes": 0, "comments": 0}

    elif parts[0] == "Like":
        username = parts[1]
        likes = int(parts[2])

        if username not in followers:
            followers[username] = {"likes": likes, "comments": 0}
        else:
            followers[username]["likes"] += likes

    elif parts[0] == "Comment":
        username = parts[1]

        if username not in followers:
            followers[username] = {"likes": 0, "comments": 1}
        else:
            followers[username]["comments"] += 1

    elif parts[0] == "Blocked":
        username = parts[1]

        if username in followers:
            del followers[username]
        else:
            print(f"{username} doesn't exist.")

# Output
print(f"{len(followers)} followers")
for user in followers:
    total = followers[user]["likes"] + followers[user]["comments"]
    print(f"{user}: {total}")
