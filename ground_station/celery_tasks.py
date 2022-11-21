from datetime import timedelta
import time
import os
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import task_prerun, task_postrun
from ground_station.celery_worker import celery_app
from ground_station.hardware.naku_device_api import gs_device, session_routine
from ground_station.models import DbTaskModel
from ground_station.propagator.propagate import SatellitePath, angle_points_for_linspace_time
from ground_station.database_api import user_scripts, sessions


@celery_app.task
def connect():
    gs_device.connect(tx_port_or_serial_id=f'{os.environ.get("TX_PORT", "/dev/ttyUSB1")}',
                      rx_port_or_serial_id=f'{os.environ.get("RX_PORT", "A50285BI")}',
                      radio_port_or_serial_id=f'{os.environ.get("RADIO_PORT", "AH06T3YJ")}')

@celery_app.task
def set_angle(az, el):
    gs_device.rotator.set_angle(az, el)


@celery_app.task
def get_angle():
    # model = device.rotator.rotator_model.__dict__
    return gs_device.rotator.rotator_model


@celery_app.task
def radio_task(model: DbTaskModel):
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


@celery_app.task
def rotator_task(model: DbTaskModel) -> None:
    try:
        path_points: SatellitePath = angle_points_for_linspace_time(model.sat_name, model.station, model.start_time,
                                                                    model.start_time + timedelta(model.duration_sec))
        session_routine(path_points)
    except SoftTimeLimitExceeded as exc:
        print(exc)
        return None

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