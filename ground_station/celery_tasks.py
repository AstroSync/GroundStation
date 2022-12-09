from __future__ import annotations
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import task_prerun, task_postrun
from ground_station.main import celery_app
from ground_station.hardware.naku_device_api import NAKU, session_routine
from ground_station.hardware.rotator.rotator_driver import RotatorDriver
from ground_station.models.db import ResultSessionModel, UserScriptModel, SessionModel

from ground_station.propagator.propagate import SatellitePath, angle_points_for_linspace_time, TestSatellitePath
from ground_station.scripts_store import UserStore, script_store
from ground_station.web_secket_client import WebSocketClient


@celery_app.task
def init_devices():
    RotatorDriver()
    NAKU()


@celery_app.task
def set_angle(az, el) -> None:
    print(f'set angle {az=}, {el=}')
    RotatorDriver().set_angle(az, el)


@celery_app.task
def get_angle():
    # model = device.rotator.rotator_model.__dict__
    return RotatorDriver().current_position


@celery_app.task(bind=True)
def radio_task(self, **kwargs) -> str | None:
    session: SessionModel = SessionModel.parse_obj(kwargs)
    script: UserScriptModel | None = None
    loc = {}
    ws_client = WebSocketClient()
    try:
        if session.script_id is not None:
            script = script_store.download_script(session.script_id)
            if script is not None:
                print(script.content)
                if len(script.content) > 0:
                    exec(script.content, globals(), loc)
            else:
                ws_client.send('there is no script')
        else:
            ws_client.send('start without script')
    except SoftTimeLimitExceeded as exc:
        print(exc)
    ws_client.send('time is over')
    ws_client.close()
    result = loc.get('result', None)
    print(f'RADIO RESULT: {result}')
    session_result = ResultSessionModel(user_id=session.user_id, username=session.username,
                                        script_id=session.script_id, sat_name=session.sat_name, station=session.station,
                                        registration_time=session.registration_time, start_time=session.start,
                                        priority=session.priority, duration_sec=session.duration_sec)
    session_result.result = NAKU().radio.get_rx_buffer()
    UserStore('10.6.1.74', 'root', 'rootpassword').save_session_result(session_result)
    NAKU().radio.clear_rx_buffer()
    return result


@celery_app.task(bind=True)
def rotator_task_emulation(self, **kwargs) -> None:
    session = SessionModel.parse_obj(kwargs)
    try:
        path_points: SatellitePath = angle_points_for_linspace_time(session.sat_name, session.station, session.start,
                                                                    session.finish)
        session_routine(TestSatellitePath(kwargs.get('duration_sec', 45)))  # type: ignore
    except SoftTimeLimitExceeded as exc:
        print(exc)


@celery_app.task(bind=True)
def rotator_task(self, **kwargs) -> None:
    session = SessionModel.parse_obj(kwargs)
    try:
        path_points: SatellitePath = angle_points_for_linspace_time(session.sat_name, session.station, session.start,
                                                                    session.finish)
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
