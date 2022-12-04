from __future__ import annotations
# from datetime import datetime, timedelta
from uuid import UUID
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.results import DeleteResult, InsertOneResult

from ground_station.models.db import UserScriptModel

class ScriptsStore:
    def __init__(self, host: str, username: str, password: str) -> None:
        super().__init__()
        try:
            client: MongoClient = MongoClient(host=host, port=27017, username=username, uuidRepresentation='standard',
                                              password=password, authMechanism='DEFAULT',
                                              serverSelectionTimeoutMS=2000)
            db: Database = client['UserData']
            print("Connected to MongoDB")
            self.scripts: Collection = db['scripts']
            self.scripts.create_index([( "user_id", ASCENDING )])
        except TimeoutError as e:
            print(f'Database connection failed: {e}')

    def save_script(self, script: UserScriptModel):
        result: InsertOneResult = self.scripts.insert_one(script.dict(by_alias=True))
        return result.inserted_id

    def download_script(self, script_id: UUID) -> UserScriptModel | None:
        result: dict | None = self.scripts.find_one({'_id': script_id})
        if result is not None:
            return UserScriptModel.parse_obj(result)
        return None

    def download_users_scripts(self, user_id: UUID) -> list[UserScriptModel]:
        return [UserScriptModel.parse_obj(data) for data in list(self.scripts.find({'user_id': user_id}))]

    def update_script(self, user_id: UUID, script_id: UUID, content: bytes):
        pass

    def delete_script(self, script_id: UUID) -> int:
        result: DeleteResult = self.scripts.delete_one({'script_id': script_id})
        return result.deleted_count

script_store = ScriptsStore('10.6.1.74', 'root', 'rootpassword')

if __name__ == '__main__':
    res = script_store.download_script(UUID('e32d478f-e305-4a74-94dc-47234d17d959'))
    print(res)
