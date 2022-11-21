from __future__ import annotations
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from ground_station.models import DbTaskModel
from ground_station.sessions_store.time_range import TimeRange, terminal_print, merge


class Session(TimeRange):
    def __init__(self, user_id: UUID, username: str, sat_name: str, station: str, start: datetime, duration_sec: int,
                       status: str = 'WAITING', priority: int = 1, script_id: UUID | None = None,
                       _id: UUID | None = None, finish: datetime | None = None, result: str = '',
                       traceback: str = '', symbol: str | None = None) -> None:
        super().__init__(_id=_id, start=start, finish=finish, duration_sec=duration_sec, priority=priority,
                         symbol=symbol)
        self.user_id: UUID = user_id
        self.username: str = username
        self.script_id: UUID | None = script_id
        self.sat_name: str = sat_name
        self.station: str = station
        self.status: str = status
        self.registration_time: datetime = datetime.now()
        self.result: str = result
        self.traceback: str = traceback

    def convert_to_db_model(self) -> DbTaskModel:
        return DbTaskModel.parse_obj(self.__dict__)


if __name__ == '__main__':
    start_time: datetime = datetime.now() + timedelta(seconds=2)
    s1: Session = Session(user_id=uuid4(), username='lolkek', station='NSU@2135dsf23',
                          start=start_time, duration_sec=10, sat_name='NORBI', priority=1)
    s2: Session = Session(user_id=uuid4(), username='gdfg',station='NSU@2135dsf23', sat_name='NORBI',
                          start=start_time + timedelta(seconds=2),  duration_sec=5, priority=2)
    data: list[Session] = [s1, s2]
    terminal_print(data)  # type: ignore
    new_data: list[TimeRange] = merge(data) # type: ignore
    print('-----------------')
    terminal_print(new_data)  # type: ignore
    # print(s1.convert_to_db_model())
