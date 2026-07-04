number_of_items = int(input())

supermarket = {}

for i in range(number_of_items):
    data = input().split()
    price = int(data[-1])
    item_name = " ".join(data[:-1])
    # * The [:-1] part is a slice. In Python, this means "start from the beginning and go up to, but do not include, the last element."
    # *
    # *Input: ['POTATO', 'CHIPS', '30']
    # *
    # *Action: Remove the last element ('30').
    # *
    # *Result: ['POTATO', 'CHIPS']


    supermarket[item_name] = supermarket.get(item_name, 0) + price


for key, value in supermarket.items():
    print(key, value)