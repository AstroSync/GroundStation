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
while i < 5:
    print(f'tick {i}')
    time.sleep(1)
    result.append(str(i))
    i+=1
"""
def print_loc():
    print('dfsf')

def exec_task():
    local_a = 324
    loc = {'local_a': local_a}
    exec(SCRIPT, globals(), loc)
    result = loc['result']
    return result

if __name__ == '__main__':
    res = exec_task()