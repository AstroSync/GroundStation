import threading
import time
from io import StringIO

from pylint.lint import Run
from pylint.reporters.text import TextReporter

STOP_FLAG = True

def api_func(i: int):
    if STOP_FLAG:
        raise Exception('STOP SCRIPT')
    print(i)
    time.sleep(1)


SCRIPT = """
i = 0
while True:
    i += 1
    if stop_flag:
        print('stop')
        break
    api_func(i)

"""


# def inf_func(script: str):
#     try:
#         while True:
#             i += 1
#             if stop_flag:
#                 prin
#             api_func(i)
#     except Exception as e:
#         print(e)

def pylint_check(path: str):
    pylint_output = StringIO()  # Custom open stream
    reporter = TextReporter(pylint_output)
    results = Run(['--disable=line-too-long', f'{path}'],
                  reporter=reporter, exit=False)
    errors = results.linter.stats.error
    fatal = results.linter.stats.fatal
    return errors, fatal, pylint_output.getvalue()

    # Run(['script.py'])

# def is_valid_python2():
#     from flake8.api import legacy as flake8
#     Run(['script.py'])


if __name__ == '__main__':
    # print(type(compile(script, "<string>", 'exec')))
    print(pylint_check('gwxkherhqw_database_api.py'))
    # thread = threading.Thread(name='t1', target=inf_func, args=[script])
    # thread2 = threading.Thread(name='t2', target=inf_func, args=[script])
    # thread.start()
    # thread2.start()
    # time.sleep(5)
    # stop_flag = True
    # thread = None
