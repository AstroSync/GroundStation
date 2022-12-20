from __future__ import annotations

from io import StringIO
import os
from threading import Thread
from tempfile import NamedTemporaryFile
from datetime import datetime, timezone
import time
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from celery.exceptions import SoftTimeLimitExceeded
from pytz import utc
# from celery.signals import task_prerun, task_postrun
from ground_station.main import app
from ground_station.hardware.naku_device_api import NAKU, session_routine
from ground_station.models.db import ResultSessionModel, UserScriptModel, SessionModel

from ground_station.propagator.propagate import SatellitePath, angle_points_for_linspace_time, TestSatellitePath
from ground_station.scripts_store import UserStore, script_store
from ground_station.web_secket_client import WebSocketClient


@app.task
def connect_naku():
    return NAKU().connect_default()

@app.task
def disconnect_naku():
    return NAKU().disconnect()

@app.task
def set_angle(az, el) -> None:
    if not NAKU().rotator.connection_flag:
        NAKU().rotator.connect_default()
        time.sleep(1)
    print(f'set angle {az=}, {el=}')
    NAKU().rotator.set_angle(az, el)

@app.task
def set_speed(az_speed, el_speed) -> None:
    if not NAKU().rotator.connection_flag:
        NAKU().rotator.connect_default()
        time.sleep(1)
    print(f'set speed {az_speed=}, {el_speed=}')
    NAKU().rotator.set_speed(az_speed, el_speed)

@app.task
def get_angle():
    # model = device.rotator.rotator_model.__dict__
    return NAKU().rotator.current_position

@app.task
def get_config():
    # model = device.rotator.rotator_model.__dict__
    return NAKU().rotator.get_config()

@app.task
def pylint_check(content: bytes) -> tuple[int, int, str]:
    file_copy = NamedTemporaryFile(delete=False)
    file_copy.write(content)  # copy the received file data into a new temp file.
    file_copy.seek(0)  # move to the beginning of the file

    pylint_output: StringIO = StringIO()  # Custom open stream
    reporter: TextReporter = TextReporter(pylint_output)
    results: Run = Run(['--disable=missing-module-docstring', 'temp.py'],
                  reporter=reporter, exit=False)
    errors: int = results.linter.stats.error
    fatal: int = results.linter.stats.fatal
    file_copy.close()  # Remember to close any file instances before removing the temp file
    os.unlink(file_copy.name)  # unlink (remove) the file
    return errors, fatal, pylint_output.getvalue()

@app.task
def calculate_angles(sat: str, t_1: str, t_2: str):
    path: SatellitePath = angle_points_for_linspace_time(sat, 'NSU', datetime.fromisoformat(t_1.replace('Z', '+00:00')),
                                                         datetime.fromisoformat(t_2.replace('Z', '+00:00')))
    print(path.to_dict())
    return path.to_dict()

@app.task
def radio_task(**kwargs) -> None:
    session: SessionModel = SessionModel.parse_obj(kwargs)
    session.start = session.start.astimezone(timezone.utc)
    session.finish = session.finish.astimezone(timezone.utc)
    if datetime.now().astimezone(timezone.utc) > session.finish:
        print('Task missed')
        return

    script: UserScriptModel | None = None
    loc: dict = {}
    ws_client: WebSocketClient = WebSocketClient(session.user_id)
    ws_client.send(f'start session with {session.sat_name}')
    NAKU().connect_default()
    NAKU().radio.onReceive(ws_client.send)
    NAKU().radio.onTrancieve(ws_client.send)
    test_flag = kwargs.get('test', None)
    if test_flag is None:
        rotator_callback = rotator_worker
        print('Run full-fledged session')
    else:
        rotator_callback = rotator_worker_test
        print('Run TEST session')
    rotator_thread: Thread = Thread(name='rotator_thread', target=rotator_callback, kwargs=kwargs, daemon=True)
    rotator_thread.start()
    # if test_flag is not None:
    #     time.sleep(60)
    try:
        if session.script_id is not None:
            script = script_store.download_script(session.script_id)
            if script is not None:
                print(script.content)
                if len(script.content) > 0:
                    exec(script.content, globals(), loc)
            else:
                ws_client.send('there is no script')
                print('there is not script')
        else:
            ws_client.send('start without script')
            while True:
                pass
    except SoftTimeLimitExceeded as exc:
        print(exc)
    ws_client.send('time is over')
    NAKU().disconnect()
    if rotator_thread.is_alive():
        print('rotator thread still alive!')
        rotator_thread.join(1)
        if rotator_thread.is_alive():
            print('rotator thread still alive!'.upper())

    ws_client.close()
    del ws_client
    result = loc.get('result', None)
    print(f'RADIO RESULT: {result}')
    session_result = ResultSessionModel(user_id=session.user_id, username=session.username,
                                        script_id=session.script_id, sat_name=session.sat_name, station=session.station,
                                        registration_time=session.registration_time, start_time=session.start,
                                        priority=session.priority, duration_sec=session.duration_sec, status='SUCCESS')
    session_result.result = NAKU().radio.get_rx_buffer()
    UserStore('10.6.1.74', 'root', 'rootpassword').save_session_result(session_result)
    print('result saved in database')
    NAKU().radio.clear_rx_buffer()

def rotator_worker_test(**kwargs):
    session = SessionModel.parse_obj(kwargs)
    try:
        path_points: SatellitePath = angle_points_for_linspace_time(session.sat_name, session.station, session.start,
                                                                    session.finish)
        session_routine(TestSatellitePath(kwargs.get('duration_sec', 45)))  # type: ignore
    except SoftTimeLimitExceeded as exc:
        print(exc)

def rotator_worker(**kwargs):
    session = SessionModel.parse_obj(kwargs)
    print(f'{session.start=}, {session.finish=}')
    try:
        path_points: SatellitePath = angle_points_for_linspace_time(session.sat_name, session.station,
                                                                    session.start, session.finish)
        session_routine(path_points)
    except SoftTimeLimitExceeded as exc:
        print(exc)

@app.task
def rotator_task_emulation(**kwargs) -> None:
    rotator_worker_test(**kwargs)


@app.task
def rotator_task(**kwargs) -> None:
    rotator_worker(**kwargs)

# @task_prerun.connect(sender=radio_task)
# def task_prerun_notifier(**kwargs):
#     task_id = kwargs.get('task_id')
#     task = kwargs.get('task')
#     keywargs = kwargs.get('kwargs')
#     args = kwargs.get('args')
#     print(f'task_prerun. task_id: {task_id} task: {task}')

# @task_postrun.connect(sender=radio_task)
# def task_postrun_notifier(**kwargs):
#     task_id = kwargs.get('task_id')
#     task = kwargs.get('task')
#     keywargs = kwargs.get('kwargs')
#     args = kwargs.get('args')
#     result = kwargs.get('retval')
#     state = kwargs.get('state')
#     print(f'task_postrun. task_id: {task_id} task: {task} result{result} state: {state}')

if __name__ == '__main__':
    print(datetime.fromisoformat('2022-12-15T09:36:01.617459Z'))