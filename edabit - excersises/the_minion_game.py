def minion_game(string):
    vowels = set("AEIOU")
    n = len(string)
    kevin = 0
    stuart = 0

    for i, ch in enumerate(string):
        if ch in vowels:
            kevin += n - i
        else:
            stuart += n - i

    if kevin > stuart:
        print("Kevin", kevin)
    elif stuart > kevin:
        print("Stuart", stuart)
    else:
        print("Draw")


# If you want to run it with input:
if __name__ == "__main__":
    s = input().strip()
    minion_game(s)
