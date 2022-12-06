import time
i = 0
result = []
while True:
    print(f'tick {i}')
    time.sleep(1)
    result.append(str(i))
    i+=1


# if __name__ == '__main__':
#     print(result)