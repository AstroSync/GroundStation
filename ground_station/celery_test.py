
import os
from celery import Celery
from ground_station.hardware.naku_device_api import device


device.connect(tx_port_or_serial_id=f'{os.environ.get("TX_PORT", "/dev/ttyUSB1")}',
                  rx_port_or_serial_id=f'{os.environ.get("RX_PORT", "A50285BI")}',
                  radio_port_or_serial_id=f'{os.environ.get("RADIO_PORT", "AH06T3YJ")}')


app = Celery('celery_worker', broker='redis://redis:6379/0', backend='redis://redis:6379/0')
print('start celery worker')


@app.task
def add(x, y):
    return x + y
