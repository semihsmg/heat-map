from collections import Counter

words_list = []

with open('log.txt') as file:
    # read lines
    data = file.read()
    for line in data:
        # append the line without \n char
        words_list.append(line[:-1])

    # Count each item and sort them from most to least common order
    count_table = Counter(words_list).most_common()

    for item in count_table:
        print(str(item[0]) + ' : ' + str(item[1]))
