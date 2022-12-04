from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timedelta
from typing import TypeVar, Iterable, Any
from uuid import UUID, uuid4
from ground_station.sessions_store.__researching__.time_range_iterable import TimeRange, TimeRanges, EmptyRange

Self = TypeVar("Self", bound="Task")

class Task:
    def __init__(self, user_id: UUID, username: str, sat_name: str, station: str, start: datetime, duration_sec: int,
                       status: str = 'WAITING', priority: int = 1, script_id: UUID | None = None,
                       _id: UUID | None = None, finish: datetime | None = None, result: str = '',
                       traceback: str = '', symbol: str = '-') -> None:
        self._id: UUID = _id if _id is not None else uuid4()
        self.priority: int = priority
        self.time_ranges: TimeRanges = TimeRanges([TimeRange(start, start + timedelta(seconds=duration_sec))])
        self.user_id: UUID = user_id
        self.username: str = username
        self.script_id: UUID | None = script_id
        self.sat_name: str = sat_name
        self.station: str = station
        self.status: str = status
        self.registration_time: datetime = datetime.now()
        self.result: str = result
        self.traceback: str = traceback

    def __lt__(self, val: Self) -> bool:
        return self.priority < val.priority

    def __gt__(self, val: Self) -> bool:
        return self.priority > val.priority

    # def convert_to_db_model(self) -> DbTaskModel:
    #     return DbTaskModel.parse_obj(self.__dict__)

def merge(ranges_list: list[Task]) -> list[Task]:
    """ Immutable function.
    Отсортировав изначальный список интервалов по наибольшему приоритету мы сможем
    избежать ситуации, когда интервал с которым сравнивают будет раздроблен сравниваемым
    интервалом.

    Интервал, стоящий в списке раньше интервала с таким же значением приоритета считается
    более приоритетным и будет дробить следущие за ним интервалы.

    Остается поэлементно сравнить каждый интервал с остальными и посчитать их относительное
    дополнение. Результат относительного дополнения перезаписывает элемент в изначальном
    списке от которого был посчитан. При дроблении интервалов изначальный список будет
    расширяться.
    """
    result_list: list[Task] = deepcopy(ranges_list)
    result_list.sort(reverse=True)  # sort by priority. Higher priority first
    # changes: TimeRangeChanges = TimeRangeChanges()  # prev state and current state
    for i, task in enumerate(result_list):
        for comparable_task in result_list[i + 1: ]:
            for time_range in task.time_ranges:
                for comparable_time_range in comparable_task.time_ranges:
                    relative_complement = comparable_time_range.relative_complement(time_range)
                    if isinstance(relative_complement, EmptyRange):
                        result_list.remove(comparable_task)
                    elif relative_complement != comparable_task:  # comparable_range was splitted or has an intersecion
                        result_list[:] = list(replace(result_list, old_item=comparable_task, new_items=relative_complement))[:]
                # changes.update_state(comparable_range, relative_complement)
    # recalculate_parts(result_list)  # after splitting ranges need to recalculater their 'parts' parameter
    return result_list  # sorted(result_list, key=lambda x: x.start, reverse=False)

def replace(origin_list: list, old_item: Any, new_items: Iterable | Any):
    for item in origin_list:
        if item == old_item:
            if isinstance(new_items, Iterable):
                for new_tem in new_items:
                    yield new_tem
            else:
                yield new_items
        else:
            yield item

if __name__ == '__main__':
    start_time: datetime = datetime.now() + timedelta(seconds=2)
    s1: Task = Task(user_id=uuid4(), username='lolkek', station='NSU@2135dsf23',
                          start=start_time, duration_sec=10, sat_name='NORBI', priority=1, symbol='-')
    s2: Task = Task(user_id=uuid4(), username='gdfg',station='NSU@2135dsf23', sat_name='NORBI',
                          start=start_time + timedelta(seconds=2),  duration_sec=5, priority=2, symbol='=')
    data: list[Task] = [s1, s2]
    # terminal_print(data)  # type: ignore
    new_data, changes = merge(data) # type: ignore
    print('-----------------')
    # terminal_print(new_data)  # type: ignore
    # print(new_data[1].parts)
    # print(s1.convert_to_db_model())
