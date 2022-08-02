from pymongo import MongoClient, collection

database_connection_status = False
pending_collection: collection = None
failed_collection: collection = None
completed_collection: collection = None

try:
    print('try to connect to db...')
    client = MongoClient(host='localhost', port=27017, username='root',
                         password='rootpassword', authMechanism='DEFAULT', serverSelectionTimeoutMS=2000)
    db = client['sessions']
    print("Connected to MongoDB")
    database_connection_status = True
    pending_collection = db['pending']
    failed_collection = db['failed']
    completed_collection = db['completed']
except Exception as e:
    print(f'Database connection failed: {e}')


def db_register_new_session(data):
    print(data)
    result = __check_same(data)
    print(result)
    if result is None:
        pending_collection.insert_one(data)
    else:
        print(f'Document {data} already exists.')


def __check_same(data):
    return pending_collection.find_one({'sat_name': data['sat_name'], 'session_list': data['session_list']})


def get_all_sessions():
    cursor = pending_collection.find({}, {'_id': False})
    return [session for session in cursor]

# def __find_data_in_db(collection: collection, data)


if __name__ == '__main__':
    print([x for x in pending_collection.find({'user_data.userId': 1}, {"_id": 0})])