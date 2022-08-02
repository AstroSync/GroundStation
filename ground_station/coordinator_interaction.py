import requests


def requst_sessions():
    response = requests.get('https://api.hirundo.ru/pending_sessions')
    result = eval(response.content.decode('utf-8'))[0]
    print(result)
    return result