
from celery import Celery
import os

from ground_station.hardware.naku_device_api import device
print('Created celery app')


celery_app = Celery('celery_worker', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

@celery_app.task
def add(x, y):
    return x + y

@celery_app.task
def connect():
    device.connect(tx_port_or_serial_id=f'{os.environ.get("TX_PORT", "/dev/ttyUSB1")}',
                  rx_port_or_serial_id=f'{os.environ.get("RX_PORT", "A50285BI")}',
                  radio_port_or_serial_id=f'{os.environ.get("RADIO_PORT", "AH06T3YJ")}')

@celery_app.task
def set_angle(az, el):
    device.rotator.set_angle(az, el)

@celery_app.task
def get_angle():
    # model = device.rotator.rotator_model.__dict__
    print(device.rotator.rotator_model)

