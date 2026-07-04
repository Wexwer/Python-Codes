def animals(chickens, cows, pigs):
    chicken_legs = 2
    cows_legs = 4
    pigs_legs = 4

    return ((chicken_legs*chickens) + (cows_legs*cows) + (pigs_legs*pigs))

print(animals(2, 3, 5))