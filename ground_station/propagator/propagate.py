from __future__ import annotations

import copy
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from dateutil import parser
from pytz import utc
from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite
from skyfield.timelib import Time, Timescale
from skyfield.toposlib import wgs84
from skyfield.units import Angle, Distance, AngleRate, Velocity
from skyfield.vectorlib import VectorSum
import numpy as np


OBSERVERS = {'Новосибирск': wgs84.latlon(54.842625, 83.095025, 170),
             'Красноярск': wgs84.latlon(56.010041, 92.852069),
             'Москва': wgs84.latlon(55.4507, 37.3656)}

satellites: list[EarthSatellite] = load.tle_file(os.path.join(os.path.dirname(__file__), 'cubesat_tle.txt'))


def get_sat_from_local_tle_file(name: str) -> Optional[EarthSatellite]:
    start_time = time.time()
    try:
        cubesat: EarthSatellite = list(filter(lambda sat: sat.name == name, satellites))[0]
    except IndexError:
        return None
    print(f"Tle loading took {time.time() - start_time} seconds")
    return cubesat


def request_celestrak_sat_tle(sat_name: str):
    start_time = time.time()
    try:
        cubesat: EarthSatellite = load.tle_file(f"https://celestrak.org/NORAD/elements/gp.php?NAME={sat_name}")[0]
    except IndexError:
        return None
    print(f"Tle loading took {time.time() - start_time} seconds")
    return cubesat


def convert_time_args(t_1: date | str, t_2: Optional[date | str] = None) -> tuple[Timescale, Timescale]:
    """As the frontend pass time arguments in different format, they need to be convertet datetime and
    then to Timescale. This function is auxiliary function for get_sessions_for_sat().

    Args:
        t_1 (date): start time of popagetion
        t_2 (Optional[date, str]): finish time of propagetion. Defaults to None.
                                   None supposed to calculate session for 1 day since t_1 time.

    Returns:
        tuple[Timescale, Timescale]: converted time values for skyfield propagation.
    """
    if isinstance(t_1, str):
        t_1 = parser.parse(t_1)
    if isinstance(t_2, str):
        t_2 = parser.parse(t_2)
    if t_2 is None:
        t_2 = load.timescale().from_datetime(datetime.combine(t_1, datetime.max.time(), tzinfo=utc))
    elif t_2 == t_1:
        t_2 = load.timescale().from_datetime(datetime.combine(t_2, datetime.max.time(), tzinfo=utc))
    else:
        t_2 = load.timescale().from_datetime(datetime.combine(t_2, datetime.min.time(), tzinfo=utc))
    t_1 = load.timescale().from_datetime(datetime.combine(t_1, datetime.now().time(), tzinfo=utc))
    return t_1, t_2


def skip_events_until_start(event_type_list: list[int], event_time_list: list[Time]) -> tuple[list[int], list[Time]]:
    """Some times propagation may start at moment, when the satellite already at observation point.
    We will skip this session and wait next.

    Args:
        event_type_list (list[int]): List of event numbers,
                                     where 0 - rise above horizone, 1 - culminate, 2 - set below horizone
        event_time_list (list[Time]): Corresponding time points for events.

    Returns:
        tuple[list[int], list[Time]]: Event list without already running session.
    """
    while event_type_list[0] != 0:
        event_type_list = event_type_list[1:]
        event_time_list = event_time_list[1:]
        if len(event_type_list) == 0:
            break
    return event_type_list, event_time_list


def map_events(event_type_list: list[int], event_time_list: list[Time], location_name: str):
    event_dict: dict[str, datetime | int | str] = {}
    event_dict_list: list[dict[str, datetime | int | str]] = []
    for event_type, event_time in zip(event_type_list, event_time_list):
        if event_type == 0:
            event_dict['start_time'] = event_time.astimezone(utc)
        elif event_type == 2:
            event_dict['finish_time'] = event_time.astimezone(utc)
            event_dict['duration_sec'] = (event_dict['finish_time'] - event_dict['start_time']).seconds
            event_dict['finish_time'] = str(event_dict['finish_time'])
            event_dict['start_time'] = str(event_dict['start_time'])
            event_dict['station'] = location_name
            event_dict['status'] = 'Available'  # Неопределен
            event_dict_list.append(copy.copy(event_dict))
    return event_dict_list


def events_for_observers(satellite: EarthSatellite, observers: dict, ts_1: Timescale, ts_2: Timescale):
    events_list_for_all_observers: dict[str, list[dict[str, datetime | int | str]]] = {}
    for location_name, observer in observers.items():
        event_time_list, event_type_list = satellite.find_events(observer, ts_1, ts_2, altitude_degrees=9)
        if len(event_type_list) > 1:  # there is at least one available session
            event_type_list, event_time_list = skip_events_until_start(event_type_list, event_time_list)
            if len(event_type_list) == 0:
                continue
            event_dict_list = map_events(event_type_list, event_time_list, location_name)
            events_list_for_all_observers[location_name] = event_dict_list
    return events_list_for_all_observers


def get_sessions_for_sat(sat_name: str, observers: dict,
                         t_1: date | str, t_2: Optional[date | str] = None) -> list[dict[str, Any]]:
    satellite = get_sat_from_local_tle_file(sat_name.upper())
    if satellite is None:
        raise ValueError
    start_time = time.time()
    ts_1, ts_2 = convert_time_args(t_1, t_2)
    events_list_for_all_observers = events_for_observers(satellite, observers, ts_1, ts_2)
    # final_dict_list = [dict_array for dict_array in events_list_for_all_observers.values()]
    united_dicts = [value for internal_list in events_list_for_all_observers.values() for value in internal_list]
    print(f"Took {time.time() - start_time} seconds")
    print(f'united_dicts: {united_dicts}')
    return united_dicts


class SatellitePath:
    def __init__(self, altitude: Angle, azimute: Angle, distance: Distance,
                 alt_rate: AngleRate, az_rate: AngleRate, dist_rate: Velocity, time_points: list[datetime]):
        self.altitude = altitude
        self.azimuth = azimute
        self.dist: np.ndarray = distance.km
        self.alt_rate: np.ndarray = alt_rate.degrees.per_second
        self.az_rate: np.ndarray = az_rate.degrees.per_second
        self.dist_rate: np.ndarray = dist_rate.km_per_s
        self.t_points = time_points
        self.max_alt_rate = self.alt_rate.max()
        self.max_az_rate = self.az_rate.max()
        self.__index = 0

    def __repr__(self):
        return f'Altitude: {self.altitude}\n' \
               f'Azimuth: {self.azimuth}\n' \
               f'Distance: {self.dist}\n' \
               f'Altitude rate deg/s: {self.alt_rate}\n' \
               f'Azimuth rate deg/s: {self.az_rate}\n' \
               f'Distance rate km/s: {self.dist_rate}\n' \
               f'Time points: {len(self.t_points)} values from {self.t_points[0]} to {self.t_points[-1]}\n'

    def __getitem__(self, key):
        return (self.altitude.degrees.__getitem__(key), self.azimuth.degrees.__getitem__(key),
               self.t_points.__getitem__(key))

    def __iter__(self):
        return self

    def __next__(self):
        if self.__index < len(self.altitude.degrees):
            var = (self.altitude.degrees[self.__index], self.azimuth.degrees[self.__index],
                    self.t_points[self.__index])
            self.__index += 1
            return var
        raise StopIteration


def angle_points_for_linspace_time(sat: str, observer: str, t_1: datetime, t_2: datetime,
                                   sampling_rate=3.3333) -> SatellitePath:
    timescale: Timescale = load.timescale()
    time_points = timescale.linspace(timescale.from_datetime(t_1), timescale.from_datetime(t_2),
                                     int((t_2 - t_1).seconds * sampling_rate))
    sat_position: VectorSum = (get_sat_from_local_tle_file(sat) - OBSERVERS[observer])
    topocentric = sat_position.at(time_points)
    return SatellitePath(*topocentric.frame_latlon_and_rates(OBSERVERS[observer]), time_points.utc_datetime())


if __name__ == '__main__':
    # print(datetime(2022, 6, 20, 10, 10, 10, 0, utc))
    # sessions = get_sessions_for_sat('NORBI', '19.06.2022', '19.06.2022')
    # print('response:', sessions, len(sessions))
    # print(request_celestrak_sat_tle('NORBI'))
    start_time_ = datetime(2022, 4, 15, 19, 5, 0, tzinfo=timezone.utc)
    points = angle_points_for_linspace_time('NORBI', 'Новосибирск', start_time_, start_time_ + timedelta(seconds=4))
    print(points)
    print([point for point in points])
    # print(np.gradient(az))
