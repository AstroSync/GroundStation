<<<<<<< HEAD
from typing import Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

DB_CONNECTION_STATUS: bool = False

try:
    print('try to connect to db...')
    client: MongoClient = MongoClient(host='localhost', port=27017, username='root',
                                      password='rootpassword', authMechanism='DEFAULT',
                                      serverSelectionTimeoutMS=2000)
    db: Database = client['sessions']
    print("Connected to MongoDB")
    DB_CONNECTION_STATUS: bool = True
    pending_collection: Collection = db['pending']
    failed_collection: Collection = db['failed']
    completed_collection: Collection = db['completed']
except TimeoutError as e:
    print(f'Database connection failed: {e}')


def db_register_new_session(data) -> None:
    print(data)
    result = __check_same(data)
    print(result)
    if result is None:
        pending_collection.insert_one(data)
    else:
        print(f'Document {data} already exists.')


def __check_same(data):
    return pending_collection.find_one({'sat_name': data['sat_name'], 'session_list': data['session_list']})


def get_all_sessions() -> list[Any]:
    cursor = pending_collection.find({}, {'_id': False})
    return list(cursor)

# def __find_data_in_db(collection: collection, data)


if __name__ == '__main__':
    print(list(pending_collection.find({'user_data.userId': 1}, {"_id": 0})))
=======
from typing import Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

DB_CONNECTION_STATUS: bool = False

try:
    print('try to connect to db...')
    client: MongoClient = MongoClient(host='localhost', port=27017, username='root',
                                      password='rootpassword', authMechanism='DEFAULT',
                                      serverSelectionTimeoutMS=2000)
    db: Database = client['sessions']
    print("Connected to MongoDB")
    DB_CONNECTION_STATUS: bool = True
    pending_collection: Collection = db['pending']
    failed_collection: Collection = db['failed']
    completed_collection: Collection = db['completed']
except TimeoutError as e:
    print(f'Database connection failed: {e}')


def db_register_new_session(data) -> None:
    print(data)
    result = __check_same(data)
    print(result)
    if result is None:
        pending_collection.insert_one(data)
    else:
        print(f'Document {data} already exists.')


def __check_same(data):
    return pending_collection.find_one({'sat_name': data['sat_name'], 'session_list': data['session_list']})


def get_all_sessions() -> list[Any]:
    cursor = pending_collection.find({}, {'_id': False})
    return list(cursor)

# def __find_data_in_db(collection: collection, data)


if __name__ == '__main__':
    print(list(pending_collection.find({'user_data.userId': 1}, {"_id": 0})))
>>>>>>> celery_integration
