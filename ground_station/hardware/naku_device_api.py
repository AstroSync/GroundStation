from __future__ import annotations
import time
from datetime import datetime # , timedelta
from pytz import utc
from serial.serialutil import SerialException
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

        self.rotator: RotatorDriver = RotatorDriver()
        self.radio: RadioController = RadioController()

        self.connection_status: bool = False

        # self.connect_default()

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
            self.rotator.connect(rx_port=ports['rx_port'], tx_port=ports['tx_port'])    # type: ignore
            try:
                self.radio.connect(port=ports['radio_port'])  # type: ignore
                self.connection_status = True
            except SerialException as err:
                print(f'NAKU connection error:', err)
                raise
        else:
            print('NAKU already connected')

    def connect_default(self):
        self.connect(tx_port_or_serial_id=f'/dev/ttyUSB1',
                     rx_port_or_serial_id=f'/dev/ttyUSB0',
                     radio_port_or_serial_id=f'/dev/ttyUSB2')

    def disconnect(self):
        if self.connection_status:
            self.radio.disconnect()
            print('Radio disconnected')
            self.rotator.disconnect()
            self.connection_status = False
            print('NAKU disconnected')


def session_routine(path_points: SatellitePath) -> None:
    print(f'Start rotator session routine:\n{path_points.__repr__}')
    normal_speed: int = 4
    fast_speed: int = 6
    az_step: float = 0.15
    az_trim_angle: float = az_step * path_points.az_rotation_direction
    NAKU().rotator.set_speed(fast_speed, fast_speed)
    # prepare rotator position
    NAKU().rotator.set_angle(path_points.azimuth[0], path_points.altitude[0])
    if path_points.azimuth[-1] > 360:
        NAKU().rotator.set_boundary_maximum_angle('1', path_points.azimuth[-1] + 1)
    elif path_points.azimuth[-1] < 0:
        NAKU().rotator.set_boundary_minimum_angle('1', path_points.azimuth[-1] - 1)

    if path_points.t_points[0].tzinfo is None:
        path_points.t_points = [t.astimezone(utc) for t in path_points.t_points]

    while datetime.now().astimezone(utc) < path_points.t_points[0]:  # waiting for start session
        time.sleep(1)
        print(f'start time wating: {(path_points.t_points[0] - datetime.now().astimezone(utc)).seconds}')
    while NAKU().rotator.rotator_model.azimuth.speed is None:
        NAKU().rotator.set_speed(normal_speed, normal_speed)
        time.sleep(0.2)
    print('start rotator session routine')
    for altitude, azimuth, time_point in path_points:
        print(f'next point: {azimuth:.2f}, {altitude:.2f}')
        # if NAKU().rotator.rotator_model.azimuth.speed > normal_speed:
        #     NAKU().rotator.set_speed(normal_speed, normal_speed)
            # Unsupported operand types for > ("datetime" and "timedelta")
        if abs(datetime.now().astimezone(utc) - time_point.astimezone(utc)).seconds > 1.5:
            print(f'skip point: {datetime.now().astimezone(utc), time_point}')
            continue
        if datetime.now().astimezone(utc) < time_point:
            while datetime.now().astimezone(utc) < time_point:  # waiting for next point
                time.sleep(0.01)
        NAKU().rotator.set_angle(azimuth + az_trim_angle, altitude)

        current_pos = NAKU().rotator.current_position
        if current_pos is not None:
            az_diff: float = current_pos[0] - azimuth
            el_diff: float = current_pos[1] - altitude
            # if abs(az_diff) > 3:
            #     NAKU().rotator.set_speed(fast_speed, fast_speed)
            # elif abs(az_diff) < 2:
            #     NAKU().rotator.set_speed(normal_speed, normal_speed)
            if 0 < az_diff < 1:
                az_step = 0.15
            elif 0 < az_diff < 2:
                az_step = 1
            elif 0 < az_diff < 3:
                az_step = 2
            elif 0 > az_diff > -1:
                az_step = 0.15
            elif 0 > az_diff > -2:
                az_step = 0.05
            elif 0 > az_diff > -3:
                az_step = 0.02
            # print(f'current pos: {device.rotator.current_position} target pos: {azimuth:.2f}, {altitude:.2f}')
            print(f'Az,El diff: ({az_diff:.2f}, {el_diff:.2f}) '  # type: ignore
                  f'current pos: ({current_pos[0]:.2f}, {current_pos[1]:.2f})')  # type: ignore
