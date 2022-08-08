import time
from datetime import datetime, timedelta, timezone

from apscheduler.events import EVENT_ALL
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from pymongo import MongoClient
from pytz import utc

from ground_station.hardware.naku_device_api import (device, run_user_script,
                                                     session_routine)
from ground_station.propagator.propagate import angle_points_for_linspace_time


def job_listener(event):
    print(f'job event: {event}')


# self.scheduler: BaseScheduler = BackgroundScheduler(executors={'processpool': ProcessPoolExecutor(3)})
scheduler: BaseScheduler = BackgroundScheduler(
    # TODO: переменные клента должны браться из .env
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
scheduler.add_listener(job_listener, mask=EVENT_ALL)


def add_new_session(user_script: str, sat_name: str, start_time: datetime, end_time: datetime,
                    prepare_time: timedelta = timedelta(seconds=60)):
    """Add a new session to the scheduler .

    Args:
        user_script (str): [description]
        sat_name (str): [description]
        start_time (datetime): [description]
        end_time (datetime): [description]
        prepare_time (timedelta, optional): [description]. Defaults to timedelta(seconds=60).
    """
    print(f'adding new session')
    path_points = angle_points_for_linspace_time(sat_name, device.observer['name'], start_time, end_time)
    print(path_points)
    start_time -= prepare_time
    scheduler.add_job(session_routine, 'date', run_date=start_time, args=[path_points])
    if user_script != '':
        scheduler.add_job(run_user_script, 'date', run_date=start_time, args=[user_script])


def abort_session(session_id: int):
    pass


def start():
    scheduler.start()


def shutdown():
    scheduler.shutdown()


def get_session_list_for_sat(sat_name: str):
    pass


if __name__ == '__main__':
    print('run naku_device_api')
    device.connect(tx_port_or_serial_id='COM46', rx_port_or_serial_id='COM36', radio_port_or_serial_id='COM3')
    # device.add_new_session(user_script, 'NORBI', datetime.now(tz=UTC), datetime.now(tz=UTC) + timedelta(seconds=5))
    start()
    start_from = timedelta(seconds=90)
    t_points = [datetime.now(tz=utc) + start_from + timedelta(seconds=x) for x in range(48)]

    t1 = datetime(2022, 4, 15, 19, 5, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=60)
    rotator_path = angle_points_for_linspace_time('NORBI', 'Новосибирск', t1, t2)
    print(f'starting at: {t_points[0]}')
    scheduler.add_job(session_routine, 'date', run_date=t_points[0] - timedelta(seconds=60), args=[rotator_path])
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        device.shutdown()
        print('Shutting down...')
