from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Iterable, Optional, Union
from zoneinfo import ZoneInfo
import uuid


class EmptyRange:
    def __sub__(self, val: TimeRange | EmptyRange) -> TimeRange | EmptyRange:  # type: ignore
        if isinstance(val, EmptyRange):
            return self
        return val
    def __str__(self) -> str:
        return 'EmptyRange'

class TimeRange():
    def __init__(self, task_id, start: datetime, finish: Optional[datetime] = None,
                 duration: timedelta | int = 0, tz: str | ZoneInfo = 'UTC', priority: int = 1,
                 symbol: str = '-') -> None:
        self.id_ = task_id
        if isinstance(tz, str):
            self.timezone = ZoneInfo(tz)
        elif isinstance(tz, ZoneInfo):
            self.timezone = tz
        self.priority = priority
        self.start: datetime = start
        self.symbol = symbol
        # self.previos_state: Optional[TimeRange] = None
        if finish is not None:
            self.finish: datetime = finish
            if duration == 0:  # default value
                self.duration = (self.finish - self.start).seconds
            elif isinstance(duration, timedelta):
                self.duration: int = duration.seconds
            elif isinstance(duration, int):
                self.duration: int = duration
            if (self.finish - self.start).seconds != self.duration:
                raise ValueError('Duration has incompatible value. You can do \
                                 not use duration of finish time parameter')
        else:
            if isinstance(duration, timedelta):
                self.duration: int = duration.seconds
                self.finish: datetime = self.start + duration
            elif isinstance(duration, int):
                self.duration: int = duration
                self.finish: datetime = self.start + timedelta(seconds=duration)
                if self.duration == 0:
                    raise Warning('Use EmptyRange')
        self.start.astimezone(self.timezone)
        self.finish.astimezone(self.timezone)
        validate_range(self)

    def __eq__(self, val: TimeRange | EmptyRange) -> bool:
        if isinstance(val, TimeRange):
            return self.id_ == val.id_ and self.timezone == val.timezone and self.priority == val.priority and \
                self.start == val.start and self.finish == val.finish and self.duration == val.duration
        return False

    def __lt__(self, val: TimeRange) -> bool:
        return self.priority < val.priority

    def __gt__(self, val: TimeRange) -> bool:
        return self.priority > val.priority

    def __sub__(self, val: TimeRange | EmptyRange) -> TimeRange | EmptyRange | tuple[TimeRange, TimeRange]:
        """
        Example:
        ###############################
        INPUTS:
        t1:        |---------|
        t2:             |=========|
        _______________________________
        t1 - t2:   |----|
        t2 - t1:             |====|
        t1 - t1:  EmptyRange
        t2 - t2:  EmptyRange
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        t1:       |--------------|
        t2:           |====|
        ______________________________
        t1 - t2:  |---|    |-----|
        t2 - t1:  EmptyRange
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        t1:        |-----|
        t2:                 |=====|
        ______________________________
        t1 - t2:   |-----|
        t2 - t1:            |=====|
        """
        if isinstance(val, EmptyRange):
            return self
        if self in val:
            return EmptyRange()  # type: ignore
        if val in self:
            return (TimeRange(self.id_, self.start,  val.start, priority=self.priority),
                    TimeRange(self.id_, val.finish, self.finish, priority=self.priority))
        intersection: TimeRange | EmptyRange = calc_intersect(self, val)
        if not isinstance(intersection, EmptyRange):
            if intersection.start > self.start and intersection.finish == self.finish:
                self.finish = intersection.start
            elif intersection.start == self.start and intersection.finish < self.finish:
                self.start = intersection.finish
            elif intersection.start == self.start and intersection.finish == self.finish:
                return EmptyRange()  # type: ignore
        self.duration = (self.finish - self.start).seconds
        return self

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
        return f'id: {self.id_}\nstart: {self.start}\nstop: {self.finish}\n'\
               f'duration: {self.duration} sec\npriority: {self.priority}\nsymbol: {self.symbol}\n'

    @staticmethod
    def run_callback(callback, args: Optional[list] = None, kwargs: Optional[dict] = None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        return callback(*args, **kwargs)

    def timedelta(self) -> timedelta:
        return self.finish - self.start

    def astimezone(self, tz: str) -> TimeRange:
        self.timezone: ZoneInfo = ZoneInfo(tz)
        self.start.astimezone(self.timezone)
        self.finish.astimezone(self.timezone)
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
        val:            |====|
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
        finish = self.finish
        start = self.start
        if not isinstance(intersection, EmptyRange):
            if intersection.start > self.start and intersection.finish == self.finish:
                finish = intersection.start
            elif intersection.start == self.start and intersection.finish < self.finish:
                start = intersection.finish
            elif intersection.start == self.start and intersection.finish == self.finish:
                # self in val
                return EmptyRange()  # type: ignore
            elif val in self:
                return (TimeRange(self.id_, self.start, val.start, priority=self.priority, symbol=self.symbol,
                                  tz=self.timezone),
                        TimeRange(self.id_, val.finish, self.finish, priority=self.priority, symbol=self.symbol,
                                  tz=self.timezone))
        # partial or no intersection
        return TimeRange(task_id=self.id_, start=start, finish=finish, priority=self.priority, symbol=self.symbol,
                         tz=self.timezone)

    def graphical_view(self) -> str:
        space = ' '
        return f'{space * ((self.start - datetime.now()).seconds)}|{self.symbol*(self.duration - 1)}| p={self.priority}'


RelativeComplement = Union[TimeRange, tuple[TimeRange, TimeRange], EmptyRange]


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
        return TimeRange(uuid.uuid4(), max(t1.start, t2.start), min(t1.finish, t2.finish))
    return EmptyRange()  # type: ignore


def merge(ranges_list: list[TimeRange]) -> list[TimeRange]:
    """
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
    result_list.sort(reverse=True)  # sort by priority
    for i, time_range in enumerate(result_list):
        for comparable_range in result_list[i + 1: ]:
            relative_complement: RelativeComplement = comparable_range.relative_complement(time_range)
            if isinstance(relative_complement, EmptyRange):
                result_list.remove(comparable_range)
            elif relative_complement != comparable_range:  # comparable_range was splitted or has intersecion
                result_list[:] = list(replace(result_list, old_item=comparable_range, new_items=relative_complement))[:]
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
