from __future__ import annotations
import time
from datetime import datetime, timedelta
from pytz import utc
from ground_station.hardware.radio.lora_controller import LoRaController
from ground_station.hardware.rotator.rotator_driver import RotatorDriver
from ground_station.hardware.serial_utils import convert_to_port
from ground_station.propagator.propagate import SatellitePath


SCRIPT = """
import time
print('Running user script')
i = 0
while True:
    time.sleep(0.3)
    print(f'some processing {i}')
    i+=1
print('User script completed')
"""


def run_user_script(user_script: str):
    """Run a user script .

    Args:
        user_script (str): [description]
    """
    try:
        print('Running user script')
        start_time = time.time()
        exec(user_script)
        print(f'User script finished in {time.time() - start_time} seconds.' % ())
    except Exception as ex:
        print(ex)


def session_routine(path_points: SatellitePath):
    print(f'rotator_track:\n{path_points}')
    normal_speed = 4
    fast_speed = 6
    device.rotator.set_speed(fast_speed, fast_speed)
    # prepare rotator position
    device.rotator.set_angle(path_points.azimuth.degrees[0], path_points.altitude.degrees[0])
    while datetime.now(tz=utc) < path_points.t_points[0]:  # waiting for start session
        time.sleep(0.01)
    device.rotator.set_speed(normal_speed, normal_speed)
    print('start_session')
    for altitude, azimuth, time_point in path_points:
        if device.rotator.rotator_model.azimuth.speed > normal_speed:
            device.rotator.set_speed(normal_speed, normal_speed)
            # Unsupported operand types for > ("datetime" and "timedelta")
        if datetime.now(tz=utc) - time_point > timedelta(seconds=1.5):
            print('skip point')
            continue
        while datetime.now(tz=utc) < time_point:  # waiting for next point
            time.sleep(0.01)
        device.rotator.set_angle(azimuth, altitude)
        print(altitude, azimuth, time_point)
        print(f'current pos: {device.rotator.current_position}')


class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NAKU(metaclass=Singleton):
    def __init__(self, observer: dict):
        print('Initializing NAKU')
        self.observer: dict = observer

        self.tle_list_struct: dict[str, datetime | list[str] | None] = {'last_update': None, 'tle_string_list': None}

        self.rotator: RotatorDriver = RotatorDriver()
        self.radio: LoRaController = LoRaController()

        self.connection_status: bool = False


    def get_device_state(self):
        return {'position': self.rotator.current_position}

    def connect(self, rx_port_or_serial_id: str, tx_port_or_serial_id: str, radio_port_or_serial_id: str):
        ports = convert_to_port(rx_port=rx_port_or_serial_id, tx_port=tx_port_or_serial_id,
                                radio_port=radio_port_or_serial_id)
        if None in ports:
            raise Exception(f'Some ports are unavailable {ports}')
        self.rotator.connect(rx_port=ports['rx_port'], tx_port=ports['tx_port'])
        self.radio.connect(port=ports['radio_port'])
        self.connection_status = True


    # def cancel_current_job(self):
    #     self.scheduler.remove_job(self.scheduler.get_jobs()[0].id)


device = NAKU({'name': 'Новосибирск', 'latitude': 54.842625, 'longitude': 83.095025, 'height': 170})
