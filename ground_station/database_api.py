from datetime import datetime
from hashlib import sha256
import sys
from typing import Any
from uuid import UUID, uuid4
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from ground_station.models import DbTaskModel, UserScriptModel

DB_CONNECTION_STATUS: bool = False

try:
    print('try to connect to db...')
    if sys.platform.startswith('win'):
        host = 'localhost'
    else:
        host = 'mongodb'
    client: MongoClient = MongoClient(host=host, port=27017, username='root', uuidRepresentation='standard',
                                      password='rootpassword', authMechanism='DEFAULT',
                                      serverSelectionTimeoutMS=2000)
    db: Database = client['sessions']
    print("Connected to MongoDB")
    DB_CONNECTION_STATUS: bool = True
    user_scripts: Collection = db['user_scripts']
    sessions: Collection = db['sessions']
except TimeoutError as e:
    print(f'Database connection failed: {e}')


def db_update_user_script(model: UserScriptModel):
    return user_scripts.replace_one({'_id': model._id}, model.__dict__, upsert=True).raw_result


def db_remove_user_script(script_id: UUID):
    return user_scripts.delete_one({'_id': script_id}).raw_result


def db_remove_sessions(session_id: UUID):
    return sessions.delete_one({'_id': session_id}).raw_result


def db_update_session(model: DbTaskModel):
    return sessions.replace_one({'_id': model._id}, model.__dict__, upsert=True).raw_result


def get_all_sessions() -> list[Any]:
    cursor = sessions.find({}, {'_id': False})
    return list(cursor)

# def __find_data_in_db(collection: collection, data)


if __name__ == '__main__':
    content = 'print("hello world")'.encode()
    print(db_update_user_script(UserScriptModel(user_id=uuid4(), script_name='script.py', upload_date=datetime.now(),
                                                last_edited_date=datetime.now(), username='user',
                                                content=content, size=len(content), sha256=sha256(content).hexdigest())))
    # print(db_remove_user_script(UUID('cc466e35-b3a5-4959-a89e-07098094dafd')))
