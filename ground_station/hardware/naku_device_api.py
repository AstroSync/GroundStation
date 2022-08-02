from __future__ import annotations
import time
from datetime import datetime, timedelta, timezone
from apscheduler.events import EVENT_ALL
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
# from apscheduler.executors.pool import ProcessPoolExecutor
from pymongo import MongoClient
from pytz import UTC, utc
from skyfield.api import load

from ground_station.hardware.radio.lora_controller import LoRa_Controller
from ground_station.hardware.rotator.rotator_driver import RotatorDriver
from ground_station.propagator.propagate import rotator_track, RotatorPathData


user_script = """
import time
print('Running user script')
i = 0
while True:
    time.sleep(0.3)
    print(f'some processing {i}')
    i+=1
print('User script completed')
"""


def run_user_script(user_script):
    try:
        print('Running user script')
        start_time = time.time()
        exec(user_script)
        print('User script finished in %s seconds.' % (time.time() - start_time))
    except Exception as e:
        print(e)


def session_routine(path_data: RotatorPathData):
    print(f'rotator_track:\n{path_data}')
    normal_speed = 2
    fast_speed = 4
    device.rotator.set_speed(fast_speed, fast_speed)
    device.rotator.set_angle(path_data.az.degrees[0], path_data.alt.degrees[0])  # prepare rotator position
    while datetime.now(tz=utc) < path_data.t_points[0]:  # waiting for start session
        time.sleep(0.01)
    device.rotator.set_speed(normal_speed, normal_speed)
    print('start_session')
    for altitude, azimuth, time_point in zip(path_data.alt.degrees, path_data.az.degrees, path_data.t_points):
        if device.rotator.rotator_model.azimuth.speed > normal_speed:
            device.rotator.set_speed(normal_speed, normal_speed)
        if datetime.now(tz=utc) - time_point > timedelta(seconds=1.5):
            print('skip point')
            continue
        while datetime.now(tz=utc) < time_point:  # waiting for next point
            time.sleep(0.01)
        device.rotator.set_angle(azimuth, altitude)
        print(altitude, azimuth, time_point)
        print(f'current pos: {device.rotator.current_position}')


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NAKU(metaclass=Singleton):
    def __init__(self, observer: dict):
        print('Initializing NAKU')
        self.observer: dict = observer

        self.tle_list_struct: dict[str, datetime | list[str] | None] = {'last_update': None, 'tle_string_list': None}

        self.rotator: RotatorDriver = RotatorDriver()
        self.radio: LoRa_Controller = LoRa_Controller()

        # self.scheduler: BaseScheduler = BackgroundScheduler(executors={'processpool': ProcessPoolExecutor(3)})
        self.scheduler: BaseScheduler = BackgroundScheduler(
            jobstores={'default': MongoDBJobStore(database='apscheduler',
                                                  collection='jobs',
                                                  client=MongoClient(host=f'mongodb://astrosync.ru',
                                                                     port=27017,
                                                                     username=f'root',
                                                                     password=f'rootpassword',
                                                                     authMechanism='DEFAULT',
                                                                     serverSelectionTimeoutMS=2000))
                       }
        )
        self.scheduler.add_listener(self.job_listener, mask=EVENT_ALL)
        self.connection_status: bool = False

    def job_listener(self, event):
        print(event)

    def get_device_state(self):
        return {'position': self.rotator.current_position}

    def connect(self, rx_port: str, tx_port: str, radio_port: str):
        self.rotator.connect(rx_port=rx_port, tx_port=tx_port)
        self.radio.connect(port=radio_port)
        self.connection_status = True

    def add_new_session(self, user_script: str, sat_name: str, start_time: datetime, end_time: datetime, prepare_time: timedelta = timedelta(seconds=60)):
        print(f'adding new session')
        rotator_path = rotator_track(sat_name, self.observer['name'], start_time, end_time, per_n_sec=10)
        print(rotator_path)
        start_time -= prepare_time
        self.scheduler.add_job(session_routine, 'date', run_date=start_time, args=[rotator_path])
        if user_script != '':
            self.scheduler.add_job(run_user_script, 'date', run_date=start_time, args=[user_script])

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()

    def get_session_list_for_sat(self, sat_name: str):
        pass

    # def cancel_current_job(self):
    #     self.scheduler.remove_job(self.scheduler.get_jobs()[0].id)


device = NAKU({'name': 'Новосибирск', 'latitude': 54.842625, 'longitude': 83.095025, 'height': 170})

if __name__ == '__main__':
    print('run naku_device_api')
    device.connect(tx_port='COM43', rx_port='COM36', radio_port='COM3')
    # device.add_new_session(user_script, 'NORBI', datetime.now(tz=UTC), datetime.now(tz=UTC) + timedelta(seconds=5))
    device.start()
    start_from = timedelta(seconds=90)
    t_points = [datetime.now(tz=utc) + start_from + timedelta(seconds=x) for x in range(48)]

    t1 = datetime(2022, 4, 15, 19, 5, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=60)
    path_data = rotator_track('NORBI', 'Новосибирск', t1, t2, per_n_sec=1)

    rotator_path = RotatorPathData(path_data.alt, path_data.az, t_points)
    print(f'starting at: {t_points[0]}')
    device.scheduler.add_job(session_routine, 'date', run_date=t_points[0] - timedelta(seconds=60), args=[rotator_path])
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        device.shutdown()
        print('Shutting down...')
