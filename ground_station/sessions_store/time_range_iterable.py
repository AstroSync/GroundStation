from __future__ import annotations
from datetime import datetime, timedelta
# from typing import Iterable
from ground_station.sessions_store.time_range import EmptyRange

class TimeRange:
    def __init__(self, t1: datetime, t2: datetime) -> None:
        self.t1: datetime = t1
        self.t2: datetime = t2
        if self.t1 > self.t2:
            raise ValueError('TimeRange init error: t1 > t2')

    def __repr__(self) -> str:
        return f'{self.t1.strftime("%H:%M:%S"), self.t2.strftime("%H:%M:%S")}'

    def __contains__(self, val: datetime | TimeRange) -> bool:
        """
        self:      |--------------|
        val:           |======|
        (val in self) = True
        """
        if isinstance(val, TimeRange):
            return val.t1 >= self.t1 and val.t2 <= self.t2
        return self.t1 <= val <= self.t2

    def has_intersection(self, val: TimeRange) -> bool:
        latest_start: datetime = max(self.t1, val.t1)
        earliest_end: datetime = min(self.t2, val.t2)
        return latest_start <= earliest_end

    def calc_intersection(self, val: TimeRange) -> TimeRange:
        if self.has_intersection(val):
            return TimeRange(max(self.t1, val.t1), min(self.t2, val.t2))
        return self

    def relative_complement(self, val: TimeRange):
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
        t2: datetime = self.t2
        t1: datetime = self.t1
        intersection: TimeRange = self.calc_intersection(val)
        if intersection is not self:
            if intersection.t1 > self.t1 and intersection.t2 == self.t2:
                t2: datetime = intersection.t1
            elif intersection.t1 == self.t1 and intersection.t2 < self.t2:
                t1: datetime = intersection.t2
            elif intersection.t1 == self.t1 and intersection.t2 == self.t2:
                # self in val
                return EmptyRange()
            elif val in self:
                return (TimeRange(self.t1, val.t1), TimeRange(val.t2, self.t2))
        # partial or no intersection
        return TimeRange(t1, t2)

class TimeRanges:
    def __init__(self, time_ranges: list[TimeRange]):
        self.collection: list[TimeRange] = time_ranges
        self.__index: int = 0

    def len(self):
        return len(self.collection)

    def __repr__(self) -> str:
        new_line: str = '\n'
        return f'{new_line.join([str(val) for val in self.collection])}'

    def __getitem__(self, key: int) -> TimeRange:
        return self.collection[key]

    def __next__(self) -> TimeRange:
        if self.__index < len(self.collection):
            var: TimeRange = self.collection[self.__index]
            self.__index += 1
            return var
        raise StopIteration


if __name__ == '__main__':
    t_1: datetime = datetime.now()
    t_2: datetime = t_1 + timedelta(seconds = 5)
    t3: datetime = t_2 + timedelta(seconds = 15)
    t4: datetime = t3 + timedelta(seconds = 5)
    tr: TimeRanges = TimeRanges([TimeRange(t_1, t_2), TimeRange(t3, t4)])
    for t in tr:
        print(t)