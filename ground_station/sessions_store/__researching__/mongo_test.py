from __future__ import annotations
from datetime import datetime
import json
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

class ModelTest2(BaseModel):
    c: int = 2

class ModelTest(BaseModel):
    a: int = 1
    b: ModelTest2 = ModelTest2()

def encoder(obj) -> str | dict:
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj.__dict__

def decoder(obj):
    # if isinstance(obj, dict):
    #     if 'azimuth' in obj:
    #         return RotatorModel(**obj)
    return obj

def my_dumps(obj) -> str:
    return json.dumps(obj, default=encoder)

def my_loads(obj):
    return json.loads(obj, object_hook=decoder)

class MyClass2:
    def __init__(self) -> None:
        self.c: int = 2



class MyClass:
    def __init__(self) -> None:
        self.a: int = 1
        self.b: MyClass2 = MyClass2()

def to_dict(obj):
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

class MongoController:
    def __init__(self, host: str, username: str, password: str) -> None:
        super().__init__()

        client: MongoClient = MongoClient(host=host, port=27017, username=username, uuidRepresentation='standard',
                                            password=password, authMechanism='DEFAULT',
                                            serverSelectionTimeoutMS=2000)
        db: Database = client['TimeRanges']
        print("Connected to MongoDB")
        self.db_origin_ranges: Collection = db['origin_ranges']
        self.db_prev_merge: Collection = db['prev_merge']
        self.db_schedule: Collection = db['schedule']

        # self.db_origin_ranges.insert_one(to_dict(MyClass().__dict__))
        print(list(self.db_origin_ranges.find({}))[0])

controller = MongoController('10.6.1.74', 'root', 'rootpassword')

