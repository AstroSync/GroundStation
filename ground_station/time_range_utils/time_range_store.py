
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Iterable, Optional
import uuid
from ground_station.time_range_utils.time_range import TimeRange, merge


def analize_difference(prev_merge: list[TimeRange], schedule: list[TimeRange],
                       new_ranges: Optional[list[TimeRange]] = None, removed_ranges: Optional[list[TimeRange]] = None):
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

    prev_id_list: list[uuid.UUID] = [time_range.id_ for time_range in prev_merge]
    schedule_id_list: list[uuid.UUID] = [time_range.id_ for time_range in schedule]

    for removed_range in removed_ranges:
        # Элемент удаляется из raw_prev_merge и после слияния получаем current_merge но уже без этого элемента
        # Далее сравниваем два результата слияния с элементом и без него.
        if not removed_range.id_ in prev_id_list:
            raise ValueError(f'TimeRange from removed_ranges list was never registered.\n{removed_range}')
    for prev_merged_element in prev_merge:
        if not prev_merged_element.id_ in schedule_id_list:
            print(f'Prev_merge element was fully covered by new element. Deleted element:\n{prev_merged_element}')
        else:
            schedule_element_parts = get_time_range_by_id(schedule, prev_merged_element.id_)
            prev_merged_element_parts = get_time_range_by_id(prev_merge, prev_merged_element.id_)
            if len(prev_merged_element_parts) < len(schedule_element_parts):
                print(f'Prev_merge element was splitted to {len(schedule_element_parts)} parts.')
            elif len(prev_merged_element_parts) > len(schedule_element_parts):
                print(f'Prev_merge part of element was fully covered by new element with higher priority.')

    for time_range in new_ranges:
        # if time_range.id_ in prev_id_list:
        #     raise ValueError(f'New element can not be in pre_merge and new_ranges lists simultaneously\n{time_range}')
        if time_range.id_ in schedule_id_list:
            merged_elements: list[TimeRange] = get_time_range_by_id(schedule, time_range.id_)
            if len(merged_elements) == 1:
                if merged_elements[0].duration < time_range.duration:
                    print(f'New element lost part {time_range.duration - merged_elements[0].duration} sec.\n{time_range}')
                else:
                    print(f'New element was successfully added.\n{time_range}')
            elif len(merged_elements) > 1:
                print(f'New element was splitted to {len(merged_elements)} parts.')
            else:
                raise ValueError('Impossible result because there is an id in the current_merge.')
        else:
            print(f'Another element from new_ranges or prev_merge fully covers and has higher priority.\n{time_range}')


def get_time_range_by_id(ranges_list: list[TimeRange], range_id: uuid.UUID) -> list[TimeRange]:
    result_elements: list[TimeRange]= []
    for time_range in ranges_list:
        if time_range.id_ == range_id:
            result_elements.append(time_range)
    return result_elements


class TimeRangeStore:
    def __init__(self) -> None:
        self.origin_ranges: list[TimeRange] = []  # unmerged ranges
        self.prev_merge: list[TimeRange] = []
        self.schedule: list[TimeRange] = []  # calculated priority ranges

    def set_timezone(self, tz):
        raise NotImplementedError()

    def append(self, *time_ranges: TimeRange):
        self.origin_ranges.extend(time_ranges)
        merged_ranges: list[TimeRange] = merge(self.origin_ranges)
        if len(self.prev_merge) == 0 and len(self.schedule) == 0:
            self.prev_merge[:] = merged_ranges[:]
            self.schedule[:] = merged_ranges[:]
        else:
            self.prev_merge[:] = self.schedule[:]
            self.schedule[:] = merged_ranges[:]
        analize_difference(self.prev_merge, self.schedule, time_ranges)  # type: ignore

    def remove(self, element: uuid.UUID | list[uuid.UUID] | TimeRange | list[TimeRange]):
        if len(self.origin_ranges) == 0:
            raise ValueError('You can not remove element from empty list.')
        if isinstance(element, Iterable):
            if isinstance(element[0], uuid.UUID):
                for el in element:
                    origin_element: list[TimeRange] = get_time_range_by_id(self.origin_ranges, el)  # type: ignore
                    if len(origin_element) == 1:
                        self.origin_ranges.remove(origin_element[0])  # type: ignore
                    else:
                        raise ValueError(f'Origin ranges does not consist this element. id: {origin_element}')
            elif isinstance(element[0], TimeRange):
                for el in element:
                    self.origin_ranges.remove(el)  # type: ignore
        elif isinstance(element, uuid.UUID):
            origin_element: list[TimeRange] = get_time_range_by_id(self.origin_ranges, element)
            if len(origin_element) == 1:
                self.origin_ranges.remove(origin_element[0])  # type: ignore
            else:
                raise ValueError(f'Origin ranges does not consist this element. id: {origin_element}')
        elif isinstance(element, TimeRange):
            # May be need to catch exception
            self.origin_ranges.remove(element)
        merged_ranges: list[TimeRange] = merge(self.origin_ranges)
        self.prev_merge[:] = self.schedule[:]
        self.schedule[:] = merged_ranges[:]
        analize_difference(self.prev_merge, self.schedule, None, element)  # type: ignore

    def terminal_print(self):
        print('\n' + '_'*25 + 'ORIGIN INTERVALS' + '_'*25 + '\n')
        for origin_range in self.origin_ranges:
            print(origin_range.graphical_view())
        print('\n' + '_'*24 + 'PREVIOUS INTERVALS' + '_'*24 + '\n')
        for prev_merge in self.prev_merge:
            print(prev_merge.graphical_view())
        print('\n' + '_'*25 + 'MERGED INTERVALS' + '_'*25 + '\n')
        for schedule in self.schedule:
            print(schedule.graphical_view())


if __name__ == '__main__':
    store = TimeRangeStore()
    start_time = datetime.now()
    t_1: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=5), duration=20, priority=2, symbol='-')
    t_2: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=1), duration=10, priority=3, symbol='=')
    t_3: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=1), duration=30, priority=1, symbol='#')
    t_4: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=5), duration=26, priority=2, symbol='*')
    t_5: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=45), duration=5, priority=5, symbol='~')
    t_8: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=55), duration=5, priority=5, symbol='^')
    t_6: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=12), duration=5, priority=1, symbol='%')
    t_7: TimeRange = TimeRange(uuid.uuid4(), start_time + timedelta(seconds=42), duration=25, priority=1, symbol='&')
    store.append(t_2, t_3)
    store.append(t_1)
    store.terminal_print()
    store.append(t_7)
    store.terminal_print()
    store.append(t_5, t_4, t_6, t_8)
    store.terminal_print()
    store.remove([t_2, t_4, t_7])
    store.terminal_print()
