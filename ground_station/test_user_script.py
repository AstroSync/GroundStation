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
from ground_station.test_user_script import print_loc
i = 0
result = []
print_loc()
local_a = 99
while i < 2:
    print(f'tick {i}')
    time.sleep(1)
    result.append(str(i))
    i+=1
"""
def print_loc():
    print('dfsf')

def exec_task():
    loc = {}
    exec(SCRIPT, globals(), loc)
    result = loc.get('local_a', None)
    return result

if __name__ == '__main__':
    res = exec_task()
    print(res)