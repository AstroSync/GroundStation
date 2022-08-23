from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

client: MongoClient = MongoClient(host='astrosync.ru', port=27017, username='root',
                                    password='rootpassword', authMechanism='DEFAULT',
                                    serverSelectionTimeoutMS=2000)
db: Database = client['celery_db']
tasks: Collection = db['tasks_collection']

def get_sessions_for_user(user_id: str):
    return list(tasks.find({'result.user_id': user_id}, {'_id': False}))

def get_all_tasks():
    return list(tasks.find({}, {'_id': False}))

if __name__ == '__main__':
    print(get_sessions_for_user('fdhhfd4334gfd32123'))
    # print(get_all_tasks())