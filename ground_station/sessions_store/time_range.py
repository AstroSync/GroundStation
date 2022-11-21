from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timedelta
import random
from typing import Any, Iterable, Union
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo


class EmptyRange:
    def __sub__(self, val: TimeRange | EmptyRange) -> TimeRange | EmptyRange:  # type: ignore
        if isinstance(val, EmptyRange):
            return self
        return val
    def __str__(self) -> str:
        return 'EmptyRange'

symbol_list: list[str] = ['@', '#', '$', '%', '^', '&', '*', '-', '=', '~', 'o', '+', '0']

class TimeRange:
    def __init__(self, start: datetime, finish: datetime | None = None, duration_sec: int = 0,
                 priority: int = 1, _id: UUID | None = None, symbol: str | None = None) -> None:
        self._id: UUID = uuid4() if _id is None else _id
        self.priority: int = priority
        self.start: datetime = start
        self.duration_sec: int = duration_sec
        self.parts: int = 1
        if finish is not None:
            self.finish: datetime = finish
            if duration_sec == 0:  # default value
                self.duration_sec = (self.finish - self.start).seconds
                if self.duration_sec == 0:
                    raise ValueError('Use EmptyRange')
            # if (self.finish - self.start).seconds != self.duration_sec:
            #     raise ValueError(f'Duration has incompatible value. You can do ' \
            #                       f'not use duration or finish time parameter')
        else:
            self.duration_sec: int = duration_sec
            self.finish: datetime = self.start + timedelta(seconds=duration_sec)
            if self.duration_sec == 0:
                raise Warning('Use EmptyRange')
        self.initial_start: datetime = start
        self.initial_duration_sec: int = self.duration_sec
        self.vip_list: list[UUID] = []
        self.symbol: str = symbol if symbol is not None else random.choice(symbol_list)
        validate_range(self)

    def __eq__(self, val: TimeRange | EmptyRange) -> bool:
        if isinstance(val, TimeRange):
            return self._id == val._id and self.priority == val.priority and self.start == val.start and \
                   self.finish == val.finish and self.duration_sec == val.duration_sec
        return False

    def __lt__(self, val: TimeRange) -> bool:
        return self.priority < val.priority

    def __gt__(self, val: TimeRange) -> bool:
        return self.priority > val.priority

    def __contains__(self, val: datetime | TimeRange) -> bool:
        """
        self:      |--------------|
        val:           |======|
        (val in self) = True
        """
        if isinstance(val, TimeRange):
            return val.start >= self.start and val.finish <= self.finish
        return self.start <= val <= self.finish

    def __str__(self) -> str:
        return f'id: {self._id}\nstart: {self.start}\nstop: {self.finish}\nparts: {self.parts}\n'\
               f'duration: {self.duration_sec} sec\npriority: {self.priority}\n'

    def get_id(self) -> UUID:
        return self._id

    @staticmethod
    def run_callback(callback, args: list | None = None, kwargs: dict | None = None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        return callback(*args, **kwargs)

    def timedelta(self) -> timedelta:
        return self.finish - self.start

    def astimezone(self, tz: ZoneInfo) -> TimeRange:
        self.start.astimezone(tz)
        self.finish.astimezone(tz)
        return self

    def relative_complement(self, val: TimeRange | EmptyRange):
        """
        ###############################
        self:        |----------|
        val:              |=========|
        _______________________________
        res:         |----|

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        self:            |----------|
        val:       |=========|
        _______________________________
        res:                 |------|

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        self:       |--------------|
        val:            |====|
        _______________________________
        res:        |---|    |-----|

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        self:           |----|
        val:         |==========|
        _______________________________
        res:          EmptyRange

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        self:        |-----|
        val:                 |=====|
        _______________________________
        res:         |-----|
        """
        if isinstance(val, EmptyRange):
            return self
        intersection: TimeRange | EmptyRange = calc_intersect(self, val)
        finish: datetime = self.finish
        start: datetime = self.start
        if not isinstance(intersection, EmptyRange):
            if intersection.start > self.start and intersection.finish == self.finish:
                finish: datetime = intersection.start
            elif intersection.start == self.start and intersection.finish < self.finish:
                start: datetime = intersection.finish
            elif intersection.start == self.start and intersection.finish == self.finish:
                # self in val
                return EmptyRange()  # type: ignore
            elif val in self:

                return (TimeRange(_id=self._id, start=self.start, finish=val.start, priority=self.priority, symbol=self.symbol),
                        TimeRange(_id=self._id, start=val.finish, finish=self.finish, priority=self.priority, symbol=self.symbol))
        # partial or no intersection
        return TimeRange(_id=self._id, start=start, finish=finish, priority=self.priority, symbol=self.symbol)

    def graphical_view(self) -> str:
        space = ' '
        return f'{space * ((self.start - datetime.now()).seconds)}|{self.symbol*(self.duration_sec - 1)}|'\
               f' p={self.priority}'


def terminal_print(tr_list: list[TimeRange]) -> None:
    for tr in tr_list:
        print(tr.graphical_view())


class TimeRangeState:
    def __init__(self, before_merge: TimeRange, after_merge: list[TimeRange]):
        self._id: UUID = before_merge.get_id()
        self.before_merge: TimeRange = before_merge  # state before merge
        self.after_merge: list[TimeRange] = after_merge  # state after merge

    def __str__(self) -> str:
        return f'id: {self._id}\nbefore_merge: {self.before_merge}\n after_merge: {self.after_merge}\n'

    # def __str__(self) -> str:
    #     new_line = '\n'
    #     return ''.join([f'\nid: {k}\n\n'\
    #                     f'before_merge: {{\n{v.before_merge if not isinstance(v.before_merge, Iterable) else [str(x).split(new_line) for x in v.before_merge]}'\
    #                     f'}}\nafter_merge: {{\n'\
    #                     f'{v.after_merge if not isinstance(v.after_merge, Iterable) else [str(x).split(new_line) for x in v.after_merge]}'\
    #                     f'}}\n\n'
    #                     for k, v in self.items()])


def validate_range(*args: TimeRange) -> None:
    """Check intervals inside TimeRange are not inverted"""
    for time_range in args:
        if time_range.start > time_range.finish:
            raise ValueError('TimeRange inversed!')


def isintersection(t1: TimeRange | EmptyRange, t2: TimeRange | EmptyRange) -> bool:
    if isinstance(t1, EmptyRange) or isinstance(t2, EmptyRange):
        return False
    latest_start = max(t1.start, t2.start)
    earliest_end = min(t1.finish, t2.finish)
    return latest_start <= earliest_end


def calc_intersect(t1: TimeRange | EmptyRange, t2: TimeRange | EmptyRange) -> TimeRange | EmptyRange:
    """ Creates new instance of intersection t1 and t2
    INPUTS:
    t1:         |------------|
    t2:                |===========|
    _______________________________________
    intersec:          |#####|

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    t1:          |---------|
    t2:        |===============|
    _______________________________________
    intersec:    |#########|

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    t1:         |---------|
    t2:                      |=======|
    _______________________________________
    intersec:  EmptyRange
    """
    if isinstance(t1, EmptyRange) and not isinstance(t2, EmptyRange):
        return t2
    if not isinstance(t1, EmptyRange) and isinstance(t2, EmptyRange):
        return t1
    if isinstance(t1, EmptyRange) and isinstance(t2, EmptyRange):
        return EmptyRange()
    if not isinstance(t1, EmptyRange) and not isinstance(t2, EmptyRange) and isintersection(t1, t2):
        return TimeRange(start=max(t1.start, t2.start), finish=min(t1.finish, t2.finish))
    return EmptyRange()  # type: ignore


RelativeComplement = Union[TimeRange, tuple[TimeRange, TimeRange], EmptyRange]


def merge(ranges_list: list[TimeRange]) -> list[TimeRange]:
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
    result_list: list[TimeRange] = deepcopy(ranges_list)
    result_list.sort(reverse=True)  # sort by priority. Higher priority first
    for i, time_range in enumerate(result_list):
        for comparable_range in result_list[i + 1: ]:
            relative_complement: RelativeComplement = comparable_range.relative_complement(time_range)
            if isinstance(relative_complement, EmptyRange):
                result_list.remove(comparable_range)
            elif relative_complement != comparable_range:  # comparable_range was splitted or has an intersecion
                result_list[:] = list(replace(result_list, old_item=comparable_range, new_items=relative_complement))[:]
    recalculate_parts(result_list)  # after splitting ranges need to recalculater their 'parts' parameter
    return result_list  # sorted(result_list, key=lambda x: x.start, reverse=False)


def recalculate_parts(ranges_list: list[TimeRange]) -> None:
    id_list: list[UUID] = [val.get_id() for val in ranges_list]
    for val in ranges_list:
        val.parts = id_list.count(val.get_id())


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
    # print((zoneinfo.available_timezones()))
    start_time = datetime.now()
    t_1: TimeRange = TimeRange(start_time + timedelta(seconds=5), duration_sec=20, priority=2)
    t_2: TimeRange = TimeRange(start_time + timedelta(seconds=1), duration_sec=10, priority=3)
    print(t_1.__dict__)
