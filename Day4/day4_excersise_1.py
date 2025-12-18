#Manipulate Data in Dictionary

person = {"name": "Alice", "age": 25, "grade": "A"}

#add new key-value pair
person["address"] = "123 Main ST"

#Update Age
person["age"] = 32

#remove grade in the dictionery 
if "age" in person:
    del person["age"]
print(person) 