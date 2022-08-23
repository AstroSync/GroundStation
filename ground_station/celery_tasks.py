import time
import os
import bson
from celery.exceptions import SoftTimeLimitExceeded
from ground_station.celery_worker import celery_app
from ground_station.hardware.naku_device_api import gs_device


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
def long_task(var):
    for i in range(var):
        print(f'do task {i}')
        time.sleep(1)
    # raise RuntimeError('some shit')
SCRIPT = """
i = 0
while True:
    print(f'i={i}')
    time.sleep(1)
    i+=1
"""
def load_script_from_db(script_id: str):
    # script_file = db.find({'script_id': script_id})
    return 'jklgfdjklfdgjkl'  # script_file

@celery_app.task(bind=True)
def infinite_task(self, user_id: str, user_script_id: str):
    try:
        exec(SCRIPT)
    except SoftTimeLimitExceeded as exc:
        print(exc)
        data: dict = {'user_id': user_id, 'data': "OK"}
        return {'$set': data}
    # return 'OK'