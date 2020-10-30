import random
from itertools import permutations

numbers = [1,2,3,4,5,6,7,8,9]
perm = permutations(numbers)
perm = list(perm)

all_answers = []
def check_if_true(a,b,c):

    a = int(''.join(map(str, a)))
    b = int(''.join(map(str, b)))
    c = int(''.join(map(str, c)))

    sum = a + b

    if(len(str(sum))!=3):
        return False

    if sum == c:
        return True
    else:
        return False

for row in perm:
    group_a = []
    group_b = []
    group_c = []

    for x in row:
        if (len(group_a) < 3):
            group_a.append(x)
        else:
            if (len(group_b) < 3):
                group_b.append(x)
            else:
                if (len(group_c) < 3):
                    group_c.append(x)

    value = check_if_true(group_a, group_b, group_c)

    if value == True:
        all_answers.append([group_a,group_b,group_c])
    else:
        continue

print(len(all_answers))

for row in all_answers:
    print(row)


