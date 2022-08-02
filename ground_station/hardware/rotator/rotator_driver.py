import glob
import queue
import sys
import threading
import time
from queue import Queue
from typing import Optional
import serial.tools.list_ports
import serial
from serial import SerialBase

from GS_backend.hardware.rotator.rotator_models import RotatorModel, RotatorAxisModel


def get_available_ports():
    available_port = []
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            available_port.append(port)
        except (OSError, serial.SerialException):
            pass
    return available_port


def try_to_connect(com_port: str, baudrate: int) -> Optional[SerialBase]:
    try:
        bus = serial.Serial(com_port, baudrate)
        return bus
    except serial.SerialException as err:
        print(f'Rotator connection error: {err}')
        return None


class RotatorDriver:
    def __init__(self, api_name='rotator'):
        self.api_name = api_name
        self.rx: Optional[SerialBase] = None
        self.tx: Optional[SerialBase] = None
        self.restart_counter = 0
        self.error_counter = 0
        self.__lock = threading.Lock()
        self.rotator_model: RotatorModel = RotatorModel()
        self.current_position = None
        self.__previous_position = None
        self.rx_thread = threading.Thread(target=self.rx_loop, daemon=True)
        self.tx_thread = threading.Thread(target=self.tx_loop, daemon=True)
        self.print_flag = False
        self.connection_flag = False

        self.tx_queue = Queue()
        self.is_need_to_update_model = False

    def connect(self, rx_port: str, tx_port: str):
        self.rx = try_to_connect(rx_port, 115200)
        self.tx = try_to_connect(tx_port, 115200)
        if self.rx is not None and self.tx is not None:
            try:
                rotator_version = self.get_version()
                print(f'Rotator version: {rotator_version}')
            except Exception as e:
                raise RuntimeError(f'Tx line has issue: {e}')
            if not self.rx.is_open or not self.tx.is_open:
                raise RuntimeError(f'Tx or Rx line is not open')
            else:
                self.connection_flag = True
                self.rx_thread.start()
                self.tx_thread.start()
        else:
            print('Rotator does not connected')

    def set_config(self, kwargs):
        """
        set rotator's config
        :param kwargs:
        :return:
        """
        az = RotatorAxisModel(**kwargs['az'])
        el = RotatorAxisModel(**kwargs['el'])
        if abs(az.speed - self.rotator_model.azimuth.speed) > 0.05 or \
                abs(el.speed - self.rotator_model.elevation.speed) > 0.05:
            self.set_speed(az.speed, el.speed)
            print(f'set speed: {az.speed}, {el.speed}')
        if abs(az.acceleration - self.rotator_model.azimuth.acceleration) > 0.05 \
                or abs(el.acceleration - self.rotator_model.elevation.acceleration) > 0.05:
            self.set_acceleration(az.acceleration, el.acceleration)
            print(f'set acceleration: {az.acceleration}, {el.acceleration}')
        if int(az.limits) != int(self.rotator_model.azimuth.limits):
            self.set_axis_limit_flag('0', int(az.limits))
            print(f'set limits: {az.limits}')
        if int(el.limits) != int(self.rotator_model.elevation.limits):
            self.set_axis_limit_flag('1', int(el.limits))
            print(f'set limits: {el.limits}')
        if abs(az.boundary_end - self.rotator_model.azimuth.boundary_end) > 0.05:
            self.set_boundary_maximum_angle('0', az.boundary_end)
            print(f'set boundary_end: {az.boundary_end}')
        if abs(el.boundary_end - self.rotator_model.elevation.boundary_end) > 0.05:
            self.set_boundary_maximum_angle('1', el.boundary_end)
            print(f'set boundary_end: {el.boundary_end}')
        if abs(az.boundary_start - self.rotator_model.azimuth.boundary_start) > 0.05:
            self.set_boundary_minimum_angle('0', az.boundary_start)
            print(f'set boundary_start: {az.boundary_start}')
        if abs(el.boundary_start - self.rotator_model.elevation.boundary_start) > 0.05:
            self.set_boundary_minimum_angle('1', el.boundary_start)
            print(f'set boundary_start: {el.boundary_start}')
        if abs(az.position - self.rotator_model.azimuth.position) > 0.05\
                or abs(el.position - self.rotator_model.elevation.position) > 0.05:
            self.set_angle(az.position, el.position)
        else:
            self.queue_request_condition()

    def queue_request_condition(self):
        self.tx_queue.put(b'Y\r')
        self.tx_queue.put(b'H\r')
        self.tx_queue.put(b'G0I\r')
        self.tx_queue.put(b'G1I\r')

    def _print(self, message: str):
        if self.print_flag:
            print(message)

    def tx_loop(self):
        while True:
            time.sleep(0.2)
            with self.__lock:
                try:
                    # print(self.tx_queue.queue)
                    cmd = self.tx_queue.get_nowait()
                    self.tx.write(cmd)
                except Exception:
                    self.tx_queue.put(b'Y\r')

    # 'Y' command terminated by \r
    # 'G0I' command terminated by \r\r

    def rx_loop(self):
        try:
            while True:
                try:
                    data = self.rx.read_until(b'\r')
                    data = data.decode('cp1251')
                    if 'Контроллер "РАДАНТ"' in data:
                        self.restart_counter += 1
                        self._print(f'Rotator has been restarted. Restart counter: {self.restart_counter}')
                    elif 'OK' in data:
                        with self.__lock:
                            self.__previous_position = self.current_position
                            self.current_position = [eval(x.lstrip('0')) for x in data[2:].split(' ')]
                            self.rotator_model.azimuth.position = self.current_position[0]
                            self.rotator_model.elevation.position = self.current_position[1]
                            # if self.__previous_position != self.current_position:
                            #     self.is_need_to_update_model = True
                            # else:
                            #     if self.is_need_to_update_model:
                            #         self.queue_request_condition()
                            #         self.is_need_to_update_model = False
                    elif 'ERR!' in data:
                        with self.__lock:
                            self.error_counter += 1
                            self._print(f'Get error. Error counter: {self.error_counter}')
                    elif 'Ось' in data:
                        splitted_data = data.split(' ')
                        axis = splitted_data[1]

                        data = self.rx.read_until(b'\r\r')
                        data = data.decode('cp1251').replace('\r', '\n')
                        data = data.split('\n')
                        attributes = [float(val.split(': ')[1]) for val in data if val != 'ACK' and val != ''][:-1]
                        if axis == 'А':
                            axis_obj = self.rotator_model.azimuth
                        elif axis == 'Э':
                            axis_obj = self.rotator_model.elevation
                        else:
                            raise ValueError('Incorrect rotator axis')
                        # axis_obj.update(accel=float(attributes[0]), )
                        axis_obj.acceleration = float(attributes[0])
                        axis_obj.limits = bool(int(attributes[1]))
                        axis_obj.boundary_start = float(attributes[2])
                        axis_obj.boundary_end = float(attributes[3])
                        if axis == 'Э':
                            self._print(self.rotator_model.__str__())
                    elif 'ACK' in data:
                        print('CMD OK')
                    elif data == '\r':
                        pass
                    else:
                        speed = data.split(' ')
                        try:
                            self.rotator_model.azimuth.speed = float(speed[0])
                            self.rotator_model.elevation.speed = float(speed[1])
                        except Exception as e:
                            print(f'Get incorrect data: {data.encode()}')

                except Exception as e:
                    print(f'rx_loop error: {e}')
        except KeyboardInterrupt:
            print('Shutdown rotator driver')

    def set_angle(self, az: float, el: float) -> None:
        """aaa.aa eee.ee"""
        self.tx_queue.put(bytes(f'Q{az:.2f} {el:.2f}\r'.encode()))

    def set_speed(self, az_speed: float, el_speed: float) -> None:
        """a.a e.e"""
        self.tx_queue.put(bytes(f'X{az_speed} {el_speed}\r'.encode()))

    def set_acceleration(self, az_acc: float, el_acc: float) -> None:
        """a.a e.e"""
        self.tx_queue.put(bytes(f'I{az_acc} {el_acc}\r'.encode()))

    def set_calibration(self, axis, degree) -> None:
        """ddd.dd
        Calibration makes current angle equal to argument e.g. azimuth rotated to 20 deg and if calibrate it to 1 deg
        it will think that current angle is 1 deg.
        """
        self.tx_queue.put(bytes(f'G{axis}C{degree}\r'.encode()))

    def set_axis_limit_flag(self, axis, flag: int) -> None:
        """0: disable, 1: enable"""
        self.tx_queue.put(bytes(f'G{axis}L{flag}\r'.encode()))

    def set_boundary_maximum_angle(self, axis, degree) -> None:
        """ddd"""
        self.tx_queue.put(bytes(f'G{axis}B{degree}\r'.encode()))

    def set_boundary_minimum_angle(self, axis, degree) -> None:
        """ddd"""
        self.tx_queue.put(bytes(f'G{axis}A{degree}\r'.encode()))

    def __request(self, cmd: bytes):
        with self.__lock:
            self.tx.write(cmd)
            return self.rx.read_until(b'\r').decode('cp1251')

    def get_axis_parameters(self, axis: str) -> str:
        """
        axis = 0 or 1
        returns axis parameters
        :param axis:
        :return:
        """
        return self.__request(f'G{axis}I\r'.encode())

    def get_position(self) -> str:
        return self.__request(b'Y\r')

    def get_speed(self) -> str:
        return self.__request(b'H\r')

    def get_version(self) -> str:
        return self.__request(b'G0H\r')

    def stop_rotation(self) -> None:
        self.tx_queue.put(b'S\r')


if __name__ == '__main__':
    print(get_available_ports())
    print([(device_info.device, device_info.serial_number) for device_info in serial.tools.list_ports.comports()])
    rotator = RotatorDriver()
    rotator.connect(rx_port='COM36', tx_port='COM42')
    # print(rotator.get_axis_parameters('1'))
    # time.sleep(2)
    rotator.print_flag = True
    time.sleep(1)
    rotator.set_angle(2, 2)
    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Shutdown rotator driver')
