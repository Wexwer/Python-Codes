numbers = [1, 2,3 ,4]

fruits = ["apple", "banana", "cherry"]


mixed_list = [1, "apple", True]

#calling certain parts of the index
print(numbers[3])
print(fruits[2])
print(mixed_list[1])

#adding items to the lists
fruits.append("orange")
fruits.insert(1, "grape")

print(fruits)

fruits.remove("banana")

print(fruits)

#deleting the index 0 from the list in fruits
del fruits[0]

#deleting the last one from the list
fruits.pop()

#this is going to give the list items from position 2 to 4
sliced_fruits = fruits[2:4]


#######Tuples cannot be changed#######
colours = ("red", "green", "blue") # for triple tuples
colours = ("orange",) # for single tuples, it has to have a comma, never the less it is a single item


##Dictionaries


#sets, can be comibned wih "|" or intersectionn with & or difference with - 
set1 = {1,2,3}
set2 = {3,4,5}
print(set1 | set2)
print(set1 & set2)
print(set1 - set2)