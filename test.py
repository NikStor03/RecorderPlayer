def round_num(num):
    if not str(int(num)).endswith("0") and len(str(int(num))) > 1:
        last_num = int(str(int(num))[-1])
        if last_num <= 5:
            num = int(num) - last_num
        else:
            last_num = 10 - last_num
            num = int(num) + last_num
    return num

num = round_num(16)

print(num)

