from __future__ import annotations
from datetime import datetime, timedelta
import time
from pymongo import MongoClient # , timedelta
from func_timeout import func_timeout, FunctionTimedOut, func_set_timeout
from serial.serialutil import SerialException
from apscheduler.events import EVENT_ALL, SchedulerEvent
from apscheduler.events import __all__ as apschedule_events_str
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from ground_station.hardware.radio.radio_controller import RadioController
from ground_station.hardware.rotator.rotator_driver import RotatorDriver
from ground_station.hardware.serial_utils import convert_to_port, get_available_ports

apscheduler_events: dict[int, str] = dict(zip([1 << x for x in range(0, 17)], apschedule_events_str))

class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NAKU(metaclass=Singleton):
    def __init__(self) -> None:
        print('Initializing NAKU')
        self.observer: dict = {'name': 'Новосибирск', 'latitude': 54.842625, 'longitude': 83.095025, 'height': 170}

        self.tle_list_struct: dict[str, datetime | list[str] | None] = {'last_update': None, 'tle_string_list': None}

        self.rotator: RotatorDriver = RotatorDriver()
        self.radio: RadioController = RadioController()

        self.connection_status: bool = False
        self.scheduler: BaseScheduler = BackgroundScheduler(
            jobstores={'default': MongoDBJobStore(database='apscheduler',
                                                  collection='jobs',
                                                  client=MongoClient(host=f'mongodb://10.6.1.74',
                                                                     port=27017,
                                                                     username=f'root',
                                                                     password=f'rootpassword',
                                                                     authMechanism='DEFAULT',
                                                                     serverSelectionTimeoutMS=2000))
                       }
        )
        self.scheduler.add_listener(self.job_listener, mask=EVENT_ALL)

        # self.connect_default()

    def job_listener(self, event: SchedulerEvent) -> None:
        event_str: str = apscheduler_events[event.code]
        # if len(event_str) != 0:
        #     event_str = event_str[0]
        print(f'{event_str}')

    # def get_device_state(self) -> dict[str, tuple[float, float]]:
    #     if self.rotator.current_position is None:
    #         raise RuntimeError('Rotator current position still None. Probably there is no connection with \
    #                            RX or Tx channels.')
    #     return {'position': self.rotator.current_position}

    def connect(self, rx_port_or_serial_id: str, tx_port_or_serial_id: str, radio_port_or_serial_id: str) -> None:
        if not self.connection_status:
            ports: dict[str, str | None] = convert_to_port(rx_port=rx_port_or_serial_id, tx_port=tx_port_or_serial_id,
                                    radio_port=radio_port_or_serial_id)
            if not all(ports.values()):
                raise RuntimeError(f'Some ports are unavailable {ports}. There are only next ports: '\
                                   f'{get_available_ports()}')
            radio_port: str | None = ports['radio_port']
            rotator_rx_port: str | None = ports['rx_port']
            rotator_tx_port: str | None = ports['tx_port']
            if rotator_rx_port is not None and rotator_tx_port is not None:
                self.rotator.connect(rx_port=rotator_rx_port, tx_port=rotator_tx_port)
            if radio_port is not None:
                try:
                    self.radio.connect(port=radio_port)
                    self.connection_status = True
                except SerialException as err:
                    print(f'NAKU connection error:', err)
                    raise
        else:
            print('NAKU already connected')
        if self.connection_status:
            self.scheduler.start()

    def connect_default(self) -> None:
        self.connect(tx_port_or_serial_id=f'/dev/ttyUSB1',
                     rx_port_or_serial_id=f'/dev/ttyUSB0',
                     radio_port_or_serial_id=f'/dev/ttyUSB2')

    def disconnect(self) -> None:
        if self.connection_status:
            self.scheduler.shutdown()
            self.radio.disconnect()
            print('Radio disconnected')
            self.rotator.disconnect()
            self.connection_status = False
            print('NAKU disconnected')

@func_set_timeout(3)
def test_job(start_time: datetime, duration: int, script_id: int) -> None:
    for i in range(5):
        time.sleep(1)
        print(i)

def session(start_time: datetime, duration: int, script_id: int = 32322134):
    try:
        test_job(start_time, duration, script_id)
    except FunctionTimedOut as err:
        print(err)
    return 'success'


if __name__ == '__main__':
    device: NAKU = NAKU()
    device.connect_default()
    # device.scheduler._jobstores['default'].collection.delete_one({'_id': 'my_job'})
    # device.scheduler.add_job(session, 'date', run_date=datetime.now() + timedelta(seconds=60), id='my_job',
    #                          kwargs={'start_time': datetime.now() + timedelta(seconds=6), 'duration': 10})
    device.scheduler.print_jobs()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        device.disconnect()
        print('Shutting down...')