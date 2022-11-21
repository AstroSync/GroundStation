from datetime import datetime, timedelta
import uuid
from ground_station.sessions_store.session import Session
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from ground_station.sessions_store.time_range import TimeRange
from ground_station.sessions_store.sessions_store import TimeRangesStore


class MongoController(TimeRangesStore):
    def __init__(self, host: str, username: str, password: str):
        super().__init__()
        try:
            client: MongoClient = MongoClient(host=host, port=27017, username=username, uuidRepresentation='standard',
                                              password=password, authMechanism='DEFAULT',
                                              serverSelectionTimeoutMS=2000)
            self.db: Database = client['TimeRanges']
            print("Connected to MongoDB")
            self.connection_status: bool = True
            self.db_origin_ranges: Collection = self.db['origin_ranges']
            self.db_prev_merge: Collection = self.db['prev_merge']
            self.db_schedule: Collection = self.db['schedule']
        except TimeoutError as e:
            print(f'Database connection failed: {e}')
        print(list(self.db_origin_ranges.find()))
        self.origin_ranges = [TimeRange(task_id=el['_id'], start=el['start_time'], finish=el['finish_time'],
                                        duration_sec=el['duration_sec'], timezone=el['timezone'],
                                        priority=el['priority']) for el in list(self.db_origin_ranges.find())]
        self.prev_merge = [TimeRange(task_id=el['_id'], start=el['start_time'], finish=el['finish_time'],
                                     duration_sec=el['duration_sec'], timezone=el['timezone'],
                                     priority=el['priority']) for el in list(self.db_prev_merge.find())]
        self.schedule = [TimeRange(task_id=el['_id'], start=el['start_time'], finish=el['finish_time'],
                                   duration_sec=el['duration_sec'], timezone=el['timezone'],
                                   priority=el['priority']) for el in list(self.db_schedule.find())]

    def append(self, *time_ranges: TimeRange):
        super().append(*time_ranges)

        _ = [self.db_origin_ranges.replace_one({'_id': convert_timerange_to_dict(tr)['_id']},
                                             convert_timerange_to_dict(tr), upsert=True) for tr in time_ranges]
        self.db_prev_merge.delete_many({})
        self.db_prev_merge.insert_many([tr for tr in self.prev_merge])
        self.db_schedule.delete_many({})
        self.db_schedule.insert_many([convert_timerange_to_dict(tr) for tr in self.schedule])

    def remove(self, element: list[uuid.UUID]):
        super().remove(element)
        self.db_origin_ranges.delete_many({})
        self.db_origin_ranges.insert_many([convert_timerange_to_dict(tr) for tr in self.origin_ranges])
        self.db_prev_merge.delete_many({})
        self.db_prev_merge.insert_many([convert_timerange_to_dict(tr) for tr in self.prev_merge])
        self.db_schedule.delete_many({})
        self.db_schedule.insert_many([convert_timerange_to_dict(tr) for tr in self.schedule])


if __name__ == '__main__':
    controller = MongoController('astrosync.ru', 'root', 'rootpassword')
    start_time = datetime(2011, 12, 1, 1, 1, 1)
    t_1: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=5), duration_sec=20, priority=2, symbol='-')
    t_2: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=1), duration_sec=10, priority=3, symbol='=')
    controller.append(t_1, t_2)

