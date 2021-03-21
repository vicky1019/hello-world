# encoding:utf-8
# @date: 2020.01.19
# @editor: vicky
# @environment: python37
# @brief: test

import numpy as np


def valid_parenthese(args):
    """
    :param args: input strings
    :return: true or false,  true means the parentheses met the request, otherwise it is false
    """
    print('s = "{}"'.format(args))

    str_dict = {"(": ")", "{": "}", "[": "]"}
    list_str = list(args)
    tmp = []
    for i in range(len(list_str)):
        if list_str[i] in str_dict:
            tmp.append(list_str[i])
        elif len(tmp) != 0 and str_dict[tmp[-1]] == list_str[i]:
            tmp.pop()
        else:
            return False
    if not tmp:
        return True
    else:
        return False


def get_test_strs(k):
    """
    make the test string
    :param k: the length of the test string
    :return: the test string
    """
    str_dict = {0: "(", 1: "[", 2: "{", 3: "}", 4: "]",  5: ")"}

    if (k >= 1) and (k <= 10**4):
        idxs = np.random.randint(0, len(str_dict), size=k)
        new_list = [str_dict[i] for i in idxs]
        # print(new_list)
        res = "".join(new_list)
    else:
        print("length limited!")
    return res


if __name__ == "__main__":
    test_string_len = 4
    result = valid_parenthese(get_test_strs(test_string_len))
    print(result)

"""test datas"""
# Example 1:
# Input: s = "()"
# Output: true

# Example 2:
# Input: s = "()[]{}"
# Output: true
#
# Example 3:
# Input: s = "(]"
# Output: false
#
# Example 4:
# Input: s = "([)]"
# Output: false
#
# Example5:
# Input: s = "{[]}"
# Output: true



