import ast
import requests


def requst_sessions():
    response = requests.get('https://api.hirundo.ru/pending_sessions')  # FIXME: use .env
    result = ast.literal_eval(response.content.decode('utf-8'))[0]
    print(result)
    return result
