
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Iterable
import uuid
from ground_station.sessions_store.time_range import merge, TimeRange, terminal_print


def analize_difference(prev_merge: list[TimeRange], schedule: list[TimeRange],
                       new_ranges: tuple[TimeRange] | list[TimeRange] | TimeRange | None = None,
                       removed_ranges: tuple[TimeRange] | list[TimeRange] | TimeRange | None = None):
    """

    Args:
        prev_merge (list[TimeRange]): Результат слияния списка интервалов raw_prev_merge.
        current_merge (list[TimeRange]): Результат слияния raw_prev_merge + new_ranges, который хотим проанализировать.
        new_ranges (list[TimeRange] | None): Список интервалов, что были добавлены в последнем слиянии.
        removed_ranges (list[TimeRange] | None): Список интервалов, что должны были быть удалены.

    Raises:
        ValueError: Если в removed_ranges есть элемент, которого нет в prev_merge. В таком случае, возможно есть
                    проблемы с согласованностью.
        ValueError: Если элемент из new_ranges есть в prev_merge. Система не должна пытаться зарегистрировать сеанс,
                    который уже был зарегистрирован. Вероятно, список составлен неверно.
    """
    print('\nAnalazing...\n')
    if new_ranges is None:
        new_ranges = []
    if removed_ranges is None:
        removed_ranges = []
    if not isinstance(new_ranges, Iterable):
        analize_append(schedule=schedule, new_ranges=[new_ranges])
    else:
        analize_append(schedule=schedule, new_ranges=list(new_ranges))
    if not isinstance(removed_ranges, Iterable):
        analize_remove(prev_merge=prev_merge, schedule=schedule, removed_ranges=[removed_ranges])
    else:
        analize_remove(prev_merge=prev_merge, schedule=schedule, removed_ranges=list(removed_ranges))


def analize_append(schedule: list[TimeRange], new_ranges: list[TimeRange]):
    schedule_idlist: list[uuid.UUID] = [time_range.get_id() for time_range in schedule]
    for time_range in new_ranges:
        # if time_range.get_id() in prev__idlist:
        #     raise ValueError(f'New element can not be in pre_merge and new_ranges lists simultaneously\n{time_range}')
        if time_range.get_id() in schedule_idlist:
            merged_elements: list[TimeRange] = get_time_range_by_id(schedule, time_range.get_id())
            if len(merged_elements) == 1:
                if merged_elements[0].duration_sec < time_range.duration_sec:
                    print(f'New element lost part {time_range.duration_sec - merged_elements[0].duration_sec} sec.\n{time_range}')
                else:
                    print(f'New element was successfully added.\n{time_range}')
            elif len(merged_elements) > 1:
                print(f'New element was splitted to {len(merged_elements)} parts.')
            else:
                raise ValueError('Impossible result because there is an id in the current_merge.')
        else:
            print(f'Another element from new_ranges or prev_merge fully covers and has higher priority.\n{time_range}')


def analize_remove(prev_merge: list[TimeRange], schedule: list[TimeRange], removed_ranges: list[TimeRange]):
    schedule_idlist: list[uuid.UUID] = [time_range.get_id() for time_range in schedule]
    prev_idlist: list[uuid.UUID] = [time_range.get_id() for time_range in prev_merge]
    for removed_range in removed_ranges:
        # Элемент удаляется из raw_prev_merge и после слияния получаем current_merge но уже без этого элемента
        # Далее сравниваем два результата слияния с элементом и без него.
        if not removed_range.get_id() in prev_idlist:
            raise ValueError(f'TimeRange from removed_ranges list was never registered.\n{removed_range}')
    for prev_merged_element in prev_merge:
        if not prev_merged_element.get_id() in schedule_idlist:
            print(f'Prev_merge element was fully covered by new element. Deleted element:\n{prev_merged_element}')
        else:
            schedule_element_parts: list[TimeRange] = get_time_range_by_id(schedule, prev_merged_element.get_id())
            prev_merged_element_parts: list[TimeRange] = get_time_range_by_id(prev_merge, prev_merged_element.get_id())
            if len(prev_merged_element_parts) < len(schedule_element_parts):
                print(f'Prev_merge element was splitted to {len(schedule_element_parts)} parts.')
            elif len(prev_merged_element_parts) > len(schedule_element_parts):
                print(f'Prev_merge part of element was fully covered by new element with higher priority.')


def get_time_range_by_id(ranges_list: list[TimeRange], range_id: uuid.UUID) -> list[TimeRange]:
    result_elements: list[TimeRange]= []
    for time_range in ranges_list:
        if time_range.get_id() == range_id:
            result_elements.append(time_range)
    return result_elements


class TimeRangesStore:
    def __init__(self) -> None:
        self.origin_ranges: list[TimeRange] = []  # unmerged ranges
        self.prev_merge: list[TimeRange] = []
        self.schedule: list[TimeRange] = []  # calculated priority ranges

    def set_timezone(self, tz):
        raise NotImplementedError()

    def append(self, *time_ranges: TimeRange) -> None:
        self.origin_ranges.extend(time_ranges)
        merged_ranges: list[TimeRange] = merge(self.origin_ranges)
        if len(self.prev_merge) == 0 and len(self.schedule) == 0:
            self.prev_merge[:] = merged_ranges[:]
            self.schedule[:] = merged_ranges[:]
        else:
            self.prev_merge[:] = self.schedule[:]
            self.schedule[:] = merged_ranges[:]
        analize_difference(self.prev_merge, self.schedule, time_ranges)

    def remove(self, element: uuid.UUID | list[uuid.UUID] | TimeRange | list[TimeRange]):
        if len(self.origin_ranges) == 0:
            raise ValueError('You can not remove element from empty list.')
        match element:
            case [uuid.UUID(), *_]:
                for el in element:
                    self.__remove_single(el)
            case [TimeRange(), *_]:
                for el in element:
                    self.origin_ranges.remove(el)
            case uuid.UUID():
                self.__remove_single(element)
            case TimeRange():
                # May be need to catch exception
                self.origin_ranges.remove(element)
            case _:
                raise TypeError('Incorrect variable type for TimeRangeStore operation.')
        merged_ranges: list[TimeRange] = merge(self.origin_ranges)
        self.prev_merge[:] = self.schedule[:]
        self.schedule[:] = merged_ranges[:]
        analize_difference(self.prev_merge, self.schedule, None, element)  # type: ignore

    def __remove_single(self, element: uuid.UUID) -> None:
        origin_element: list[TimeRange] = get_time_range_by_id(self.origin_ranges, element)
        if len(origin_element) == 1:
            self.origin_ranges.remove(origin_element[0])
        else:
            raise ValueError(f'Origin ranges does not consist this element. id: {origin_element}')



TimeRanges_store = TimeRangesStore()

if __name__ == '__main__':

    start_time: datetime = datetime.now()

    t_1: TimeRange = TimeRange(start=start_time + timedelta(seconds=5), duration_sec=20, priority=2)
    t_2: TimeRange = TimeRange(start=start_time + timedelta(seconds=1), duration_sec=10, priority=3)
    t_3: TimeRange = TimeRange(start=start_time + timedelta(seconds=1), duration_sec=30, priority=1)
    t_4: TimeRange = TimeRange(start=start_time + timedelta(seconds=5), duration_sec=26, priority=2)
    t_5: TimeRange = TimeRange(start=start_time + timedelta(seconds=45), duration_sec=5, priority=5)
    t_8: TimeRange = TimeRange(start=start_time + timedelta(seconds=55), duration_sec=5, priority=5)
    t_6: TimeRange = TimeRange(start=start_time + timedelta(seconds=12), duration_sec=5, priority=1)
    t_7: TimeRange = TimeRange(start=start_time + timedelta(seconds=42), duration_sec=25, priority=1)
    print(t_1.get_id())
    print(t_2.get_id())
    print(t_3.get_id())
    TimeRanges_store.append(t_2, t_3)
    TimeRanges_store.append(t_1)

    TimeRanges_store.append(t_7)

    TimeRanges_store.append(t_5, t_4, t_6, t_8)

    # TimeRanges_store.remove([t_2, t_4, t_7])
    terminal_print(TimeRanges_store.origin_ranges)
    print('--------------------------------------------------------')
    terminal_print(TimeRanges_store.schedule)
    print('--------------------------------------------------------')
    terminal_print(TimeRanges_store.prev_merge)
