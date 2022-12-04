from datetime import timedelta
import os
import time
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import task_prerun, task_postrun
from ground_station.celery_worker import celery_app
from ground_station.hardware.naku_device_api import gs_device, session_routine
# from ground_station.hardware.rotator.rotator_models import RotatorModel
from ground_station.models.db import Model

from ground_station.propagator.propagate import SatellitePath, angle_points_for_linspace_time
from ground_station.database_api import user_scripts
from ground_station.sessions_store.session import Session


@celery_app.task
def connect() -> None:
    gs_device.connect(tx_port_or_serial_id=f'{os.environ.get("TX_PORT", "/dev/ttyUSB1")}',
                      rx_port_or_serial_id=f'{os.environ.get("RX_PORT", "A50285BI")}',
                      radio_port_or_serial_id=f'{os.environ.get("RADIO_PORT", "AH06T3YJ")}')

@celery_app.task
def set_angle(az, el) -> None:
    gs_device.rotator.set_angle(az, el)


@celery_app.task(bind=True)
def get_angle(self, **kwargs) -> dict:
    # model = device.rotator.rotator_model.__dict__
    print(self.request.retries)
    time.sleep(10)
    return Model().dict()


@celery_app.task(bind=True)
def radio_task(model: Session):
    result = None
    try:
        script_file = list(user_scripts.find({'script_id': model.script_id}))
        if len(script_file) > 0:
            loc = {}
            exec(script_file[0], globals(), loc)
            result = loc['script_result']
    except SoftTimeLimitExceeded as exc:
        print(exc)
    return result


@celery_app.task(bind=True)
def rotator_task(model: Session) -> None:
    try:
        path_points: SatellitePath = angle_points_for_linspace_time(model.sat_name, model.station, model.start,
                                                                    model.start + timedelta(model.duration_sec))
        session_routine(path_points)
    except SoftTimeLimitExceeded as exc:
        print(exc)

@task_prerun.connect(sender=radio_task)
def task_prerun_notifier(**kwargs):
    task_id = kwargs.get('task_id')
    task = kwargs.get('task')
    keywargs = kwargs.get('kwargs')
    args = kwargs.get('args')
    print(f'task_prerun. task_id: {task_id} task: {task}')

@task_postrun.connect(sender=radio_task)
def task_postrun_notifier(**kwargs):
    task_id = kwargs.get('task_id')
    task = kwargs.get('task')
    keywargs = kwargs.get('kwargs')
    args = kwargs.get('args')
    result = kwargs.get('retval')
    state = kwargs.get('state')
    print(f'task_postrun. task_id: {task_id} task: {task} result{result} state: {state}')
