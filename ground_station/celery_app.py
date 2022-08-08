from celery import Celery
import os

from ground_station.hardware.naku_device_api import device
print('Created celery app')

device.connect(tx_port_or_serial_id=f'{os.environ.get("TX_PORT", "/dev/ttyUSB1")}',
                  rx_port_or_serial_id=f'{os.environ.get("RX_PORT", "A50285BI")}',
                  radio_port_or_serial_id=f'{os.environ.get("RADIO_PORT", "AH06T3YJ")}')
celery_app = Celery('celery_worker', broker='redis://redis:6379/0', backend='redis://redis:6379/0')
print('start celery worker')