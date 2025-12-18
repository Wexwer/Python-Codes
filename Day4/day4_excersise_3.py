my_list = ["Anna", "Silvana", "Krisia", "Anna"]

#Convertin the list into a set, to remove dublicates and then back to list so it can be reversed
unique_list = list(set(my_list))

#reversing the list 
reverse_set = unique_list[::-1]

print(reverse_set)