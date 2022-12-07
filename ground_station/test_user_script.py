# import time
# i = 0
# result = []
# while i < 5:
#     print(f'tick {i}')
#     time.sleep(1)
#     result.append(str(i))
#     i+=1

SCRIPT = """
import time
i = 0
result = []
while i < 5:
    print(f'tick {i}')
    time.sleep(1)
    result.append(str(i))
    i+=1
"""
result = None
def exec_task():
    loc = {}
    exec(SCRIPT, globals(), loc)
    result = loc['result']
    return result

if __name__ == '__main__':
    result = exec_task()
    print(globals())