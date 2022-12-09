from __future__ import annotations
import time
from datetime import datetime, timedelta
from pytz import utc
from ground_station.hardware.radio.radio_controller import RadioController
from ground_station.hardware.rotator.rotator_driver import RotatorDriver
from ground_station.hardware.serial_utils import convert_to_port, get_available_ports
from ground_station.propagator.propagate import SatellitePath


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

        # self.rotator: RotatorDriver = RotatorDriver()
        self.radio: RadioController = RadioController()

        self.connection_status: bool = False

        self.connect(tx_port_or_serial_id=f'/dev/ttyUSB1',
                     rx_port_or_serial_id=f'/dev/ttyUSB0',
                     radio_port_or_serial_id=f'/dev/ttyUSB2')

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
                raise RuntimeError(f'Some ports are unavailable {ports}. There are only next ports: {get_available_ports()}')
            # self.rotator.connect(rx_port=ports['rx_port'], tx_port=ports['tx_port'])    # type: ignore
            self.radio.connect(port=ports['radio_port'])  # type: ignore
            self.connection_status = True

def session_routine(path_points: SatellitePath) -> None:
    print(f'Start session routine:\n{path_points}')
    normal_speed: int = 4
    fast_speed: int = 6
    az_trim_angle: float = 0.15 * path_points.az_rotation_direction
    RotatorDriver().set_speed(fast_speed, fast_speed)
    # prepare rotator position
    RotatorDriver().set_angle(path_points.azimuth[0], path_points.altitude[0])
    if path_points.azimuth[-1] > 360:
        RotatorDriver().set_boundary_maximum_angle('1', path_points.azimuth[-1] + 1)
    elif path_points.azimuth[-1] < 0:
        RotatorDriver().set_boundary_minimum_angle('1', path_points.azimuth[-1] - 1)
    while datetime.now(tz=utc) < path_points.t_points[0]:  # waiting for start session
        time.sleep(0.01)
    RotatorDriver().set_speed(normal_speed, normal_speed)
    print('start rotator session routine')
    for altitude, azimuth, time_point in path_points:
        if RotatorDriver().rotator_model.azimuth.speed > normal_speed:
            RotatorDriver().set_speed(normal_speed, normal_speed)
            # Unsupported operand types for > ("datetime" and "timedelta")
        if datetime.now(tz=utc) - time_point > timedelta(seconds=1.5):
            print(f'skip point: {datetime.now(tz=utc), time_point}')
            continue
        while datetime.now(tz=utc) < time_point:  # waiting for next point
            time.sleep(0.01)
        RotatorDriver().set_angle(azimuth + az_trim_angle, altitude)
        # print(f'current pos: {device.rotator.current_position} target pos: {azimuth:.2f}, {altitude:.2f}')
        print(f'Angle differrence: Az:{(RotatorDriver().current_position[0] - azimuth):.2f},'  # type: ignore
              f'Alt:{(RotatorDriver().current_position[1] - altitude):.2f}')  # type: ignore
