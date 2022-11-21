import ast
import threading
import time
from queue import Empty, Queue
from typing import Any, NoReturn, Optional
from serial import SerialBase
import serial

from ground_station.hardware.rotator.rotator_models import RotatorModel, RotatorAxisModel


def try_to_connect(com_port: str, baudrate: int) -> Optional[SerialBase]:
    try:  # TODO: мб стоит поднимать исключение?
        bus = serial.Serial(com_port, baudrate, write_timeout=2)
        bus.reset_input_buffer()
        bus.reset_output_buffer()
        return bus
    except serial.SerialException as err:
        print(f'Rotator connection error: {err}')
        return None


class RotatorDriver:
    def __init__(self, api_name='rotator') -> None:
        self.api_name: str = api_name
        self.reciever: Optional[SerialBase] = None
        self.transmitter: Optional[SerialBase] = None
        self.restart_counter: int = 0
        self.error_counter: int = 0
        self.__lock: threading.Lock = threading.Lock()
        self.rotator_model: RotatorModel = RotatorModel()
        self.current_position: Optional[tuple[float, float]] = None
        # self.__previous_position = None
        self.rx_thread: threading.Thread = threading.Thread(name="rotator RX thread", target=self.rx_loop, daemon=True)
        self.tx_thread: threading.Thread = threading.Thread(name="rotator TX thread", target=self.tx_loop, daemon=True)
        self.print_flag: bool = False
        self.connection_flag: bool = False

        self.tx_queue = Queue()
        self.is_need_to_update_model: bool = False
        self.tx_thread_sleep_time: float = 0.1

    def connect(self, rx_port: str, tx_port: str) -> None:
        self.reciever = try_to_connect(rx_port, 115200)
        self.transmitter = try_to_connect(tx_port, 115200)
        if self.reciever is not None and self.transmitter is not None:
            try:
                rotator_version = self.get_version()
                print(f'Rotator version: {rotator_version}')
            except Exception as err:
                raise RuntimeError(f'Tx line has issue: {err}') from err
            if not self.reciever.is_open or not self.transmitter.is_open:
                raise RuntimeError(f'Tx or Rx line is not open')
            self.connection_flag = True
            self.rx_thread.start()
            self.tx_thread.start()
            self.queue_request_condition()
        else:
            print('Rotator does not connected')

    def __repr__(self) -> str:
        return f'{self.rotator_model.__repr__}'

    def set_config(self, kwargs)-> None:
        """
        set rotator's config
        :param kwargs:
        :return:
        """
        azimuth: RotatorAxisModel = RotatorAxisModel(**kwargs['az'])
        elevation: RotatorAxisModel = RotatorAxisModel(**kwargs['el'])
        if abs(azimuth.speed - self.rotator_model.azimuth.speed) > 0.05 or \
                abs(elevation.speed - self.rotator_model.elevation.speed) > 0.05:
            self.set_speed(azimuth.speed, elevation.speed)
        if abs(azimuth.acceleration - self.rotator_model.azimuth.acceleration) > 0.05 \
                or abs(elevation.acceleration - self.rotator_model.elevation.acceleration) > 0.05:
            self.set_acceleration(azimuth.acceleration, elevation.acceleration)
        if int(azimuth.limits) != int(self.rotator_model.azimuth.limits):
            self.set_axis_limit_flag('0', int(azimuth.limits))
        if int(elevation.limits) != int(self.rotator_model.elevation.limits):
            self.set_axis_limit_flag('1', int(elevation.limits))
        if abs(azimuth.boundary_end - self.rotator_model.azimuth.boundary_end) > 0.05:
            self.set_boundary_maximum_angle('0', azimuth.boundary_end)
        if abs(elevation.boundary_end - self.rotator_model.elevation.boundary_end) > 0.05:
            self.set_boundary_maximum_angle('1', elevation.boundary_end)
        if abs(azimuth.boundary_start - self.rotator_model.azimuth.boundary_start) > 0.05:
            self.set_boundary_minimum_angle('0', azimuth.boundary_start)
        if abs(elevation.boundary_start - self.rotator_model.elevation.boundary_start) > 0.05:
            self.set_boundary_minimum_angle('1', elevation.boundary_start)
        if abs(azimuth.position - self.rotator_model.azimuth.position) > 0.05\
                or abs(elevation.position - self.rotator_model.elevation.position) > 0.05:
            self.set_angle(azimuth.position, elevation.position)
        else:
            self.queue_request_condition()

    def queue_request_condition(self) -> None:
        self.tx_queue.put(b'Y\r')
        self.tx_queue.put(b'H\r')
        self.tx_queue.put(b'G0I\r')
        self.tx_queue.put(b'G1I\r')

    def _print(self, message: Any) -> None:
        if self.print_flag:
            print(f'{message}')

    def tx_loop(self) -> NoReturn:
        if self.transmitter is None:
            raise RuntimeError('Rotator TX channel object must not be None')
        while True:
            time.sleep(self.tx_thread_sleep_time)
            with self.__lock:
                try:
                    # print(self.tx_queue.queue)
                    cmd: bytes = self.tx_queue.get_nowait()
                    self.transmitter.write(cmd)
                    if self.tx_queue.qsize() > 10:
                        print(f'self.tx_queue.qsize(): {self.tx_queue.qsize()}')
                        self.tx_thread_sleep_time = 0.05
                    else:
                        self.tx_thread_sleep_time = 0.1
                except Empty:
                    self.tx_queue.put(b'Y\r')

    # 'Y' command terminated by \r
    # 'G0I' command terminated by \r\r

    def rx_loop(self) -> None:
        # TODO: add checking exception of "access error, permission denied"
        if self.reciever is None:
            raise RuntimeError('Rotator RX channel must not be None')
        try:
            while True:
                try:
                    raw_data: bytes = self.reciever.read_until(b'\r')

                    decoded_data: str = raw_data.decode('cp1251')
                    if 'Контроллер "РАДАНТ"' in decoded_data:
                        self.restart_counter += 1
                        self._print(f'Rotator has been restarted. Restart counter: {self.restart_counter}')
                        self._print(decoded_data)
                        self._print(self.reciever.read_until(b'\r').decode('cp1251'))
                        self._print(self.reciever.read_until(b'\r').decode('cp1251'))

                    elif 'OK' in decoded_data:
                        with self.__lock:
                            # self.__previous_position = self.current_position
                            position: list[int] = [int(ast.literal_eval(x.lstrip('0'))) for x in decoded_data[2:].split(' ')]
                            self.current_position = (position[0], position[1])
                            self.rotator_model.azimuth.position = self.current_position[0]
                            self.rotator_model.elevation.position = self.current_position[1]
                            # if self.__previous_position != self.current_position:
                            #     self.is_need_to_update_model = True
                            # else:
                            #     if self.is_need_to_update_model:
                            #         self.queue_request_condition()
                            #         self.is_need_to_update_model = False
                    elif 'ERR!' in decoded_data:
                        with self.__lock:
                            self.error_counter += 1
                            self._print(f'Get error. Error counter: {self.error_counter}')
                    elif 'Ось' in decoded_data:
                        # data = ['Ось:', 'А', '0', '360\r'] or ['Ось:', 'Э', '-90', '270\r']
                        splitted_data: list[str] = decoded_data.split(' ')
                        axis: str = splitted_data[1]

                        remaining_raw_data: bytes = self.reciever.read_until(b'\r\r')
                        remaining_decoded_data: str = remaining_raw_data.decode('cp1251').replace('\r', '\n')
                        # self._print(f"\ndata: {data}")

                        data: list[str] = remaining_decoded_data.split('\n')
                        attributes: list[float] = [float(val.split(': ')[1]) for val in data if val not in ('ACK', '')][:-1]
                        if axis == 'А':
                            axis_obj: RotatorAxisModel = self.rotator_model.azimuth
                        elif axis == 'Э':
                            axis_obj: RotatorAxisModel = self.rotator_model.elevation
                        else:
                            raise ValueError('Incorrect rotator axis')
                        axis_obj.min_angle = float(splitted_data[2])
                        axis_obj.max_angle = float(splitted_data[3])
                        axis_obj.acceleration = float(attributes[0])
                        axis_obj.limits = bool(int(attributes[1]))
                        axis_obj.boundary_start = float(attributes[2])
                        axis_obj.boundary_end = float(attributes[3])
                        if axis == 'Э':
                            self._print(self.rotator_model)
                    elif 'ACK' in decoded_data:
                        # print('CMD OK')
                        pass
                    elif decoded_data == '\r':
                        pass
                    else:
                        speed: list[str] = decoded_data.split(' ')
                        try:
                            self.rotator_model.azimuth.speed = float(speed[0])
                            self.rotator_model.elevation.speed = float(speed[1])
                        except ValueError:
                            print(f'Get incorrect data: {decoded_data.encode()}')
                except ValueError as err:
                    print(f'rx_loop error: {err}')
        except KeyboardInterrupt:
            print('Shutdown rotator driver')

    def set_angle(self, azimuth: float, elevation: float) -> None:
        """aaa.aa eee.ee"""
        self.tx_queue.put(bytes(f'Q{azimuth:.2f} {elevation:.2f}\r'.encode()))

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

    def set_axis_limit_flag(self, axis: str, flag: int) -> None:
        """0: disable, 1: enable"""
        self.tx_queue.put(bytes(f'G{axis}L{flag}\r'.encode()))

    def set_boundary_maximum_angle(self, axis: str, degree: float) -> None:
        """Set boundary max angle

        Args:
            axis (int): 0 - azimuth, 1 - elevation
            degree (float): degree value
        """
        self.tx_queue.put(bytes(f'G{axis}B{degree:.2f}\r'.encode()))

    def set_boundary_minimum_angle(self, axis: str, degree: float) -> None:
        """ddd"""
        self.tx_queue.put(bytes(f'G{axis}A{degree:.2f}\r'.encode()))

    def __request(self, cmd: bytes, answer_length: int = 1) -> str:
        with self.__lock:
            if self.transmitter and self.reciever is not None:
                self.transmitter.write(cmd)
                answer = []
                while answer_length:
                    answer.append(self.reciever.read_until(b'\r').decode('cp1251'))
                    answer_length -= 1
                return ''.join(answer).replace('\r', '\n')
            raise Exception('Rotator ports have issues!')

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
        return self.__request(b'G0H\r', 3)

    def queue_request_version(self) -> None:
        self.tx_queue.put(b'G0H\r')

    def stop_rotation(self) -> None:
        self.tx_queue.put(b'S\r')


if __name__ == '__main__':
    import serial.tools.list_ports
    # print([(device_info.device, device_info.serial_number)
    #       for device_info in serial.tools.list_ports.comports()])
    rotator = RotatorDriver()
    rotator.connect(rx_port='COM36', tx_port='COM46')
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
