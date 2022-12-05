import time
i = 0
result = ''
while True:
    print(f'tick {i:+=1}')
    time.sleep(1)
    result = result.join(str(i))
