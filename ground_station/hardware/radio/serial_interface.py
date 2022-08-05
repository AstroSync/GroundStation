import glob
import sys
from typing import Optional

import serial
from serial import SerialBase


def get_available_ports():
    available_port = []
    if sys.platform.startswith('win'):
        ports = [f'COM{i + 1}' for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    for port in ports:
        try:
            ser = serial.Serial(port)
            ser.close()
            available_port.append(port)
        except (OSError, serial.SerialException):
            pass
    return available_port


class SerialInterface:
    def __init__(self):
        self.connected_port: Optional[SerialBase] = None

    def connect(self, port: str) -> bool:
        try:
            self.connected_port = serial.Serial(port, 500000)
            if self.connected_port.isOpen():
                return True
            raise Exception("Device is not open")
        except serial.SerialException:
            return False

    def read(self, address: int) -> Optional[int]:
        if self.connected_port:
            self.connected_port.write(bytes([1, address]))
            return int.from_bytes(self.connected_port.read(), "big")
        return None

    def write(self, address: int, data: list[int]) -> Optional[int]:
        if self.connected_port:
            if len(data) == 1:
                self.connected_port.write(bytes([2, address, data[0]]))
            self.connected_port.write(bytes([8, address, len(data), *data]))
            return int.from_bytes(self.connected_port.read(), "big")
        return None

    def run_tx_then_rx_cont(self) -> Optional[int]:
        if self.connected_port:
            self.connected_port.write(bytes([21]))
            return int.from_bytes(self.connected_port.read(), "big")
        return None

    def run_tx_then_rx_single(self) -> Optional[int]:
        if self.connected_port:
            self.connected_port.write(bytes([22]))
            return int.from_bytes(self.connected_port.read(), "big")
        return None

    def read_several(self, address: int, amount: int) -> Optional[list[int]]:
        if self.connected_port:
            self.connected_port.write(bytes([7, address, amount]))
            return list(self.connected_port.read(amount))
        return None

    def reset(self) -> Optional[int]:
        if self.connected_port:
            self.connected_port.write(bytes([6]))
            return int.from_bytes(self.connected_port.read(), "big")
        return None
