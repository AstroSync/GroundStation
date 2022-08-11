from typing import Optional

import serial
from serial import SerialBase


class SerialInterface:
    def __init__(self) -> None:
        self.connected_port: Optional[SerialBase] = None

    def connect(self, port: str) -> bool:
        try:
            self.connected_port = serial.Serial(port, 500000)
            if self.connected_port.isOpen():
                return True
            raise Exception("Device is not open")
        except serial.SerialException:
            return False

    def read(self, address: int) -> int:
        if self.connected_port:
            self.connected_port.write(bytes([1, address]))
            return int.from_bytes(self.__try_read(), "big")
        raise RuntimeError('Radio is not connected')

    def write(self, address: int, data: list[int]) -> int:
        if self.connected_port:
            if len(data) == 1:
                self.connected_port.write(bytes([2, address, data[0]]))
            self.connected_port.write(bytes([8, address, len(data), *data]))
            return int.from_bytes(self.__try_read(), "big")
        raise RuntimeError('Radio is not connected')

    def run_tx_then_rx_cont(self) -> int:
        if self.connected_port:
            self.connected_port.write(bytes([21]))
            return int.from_bytes(self.__try_read(), "big")
        raise RuntimeError('Radio is not connected')

    def run_tx_then_rx_single(self) -> int:
        if self.connected_port:
            self.connected_port.write(bytes([22]))
            return int.from_bytes(self.__try_read(), "big")
        raise RuntimeError('Radio is not connected')

    def read_several(self, address: int, amount: int) -> list[int]:
        if self.connected_port:
            self.connected_port.write(bytes([7, address, amount]))
            return list(self.__try_read(amount))
        raise RuntimeError('Radio is not connected')

    def reset(self) -> int:
        if self.connected_port:
            self.connected_port.write(bytes([6]))
            return int.from_bytes(self.__try_read(), "big")
        raise RuntimeError('Radio is not connected')

    def __try_read(self, amount: int = 1) -> bytes:
        if self.connected_port is None:
            raise RuntimeError('Radio transciever object must not be None')
        try:
            data: Optional[bytes]= self.connected_port.read(amount)
            if data is None:
                raise RuntimeError('Radio somehow read None data')
            return data
        except TimeoutError as exc:
            raise TimeoutError(f'Radio reading timeout: {exc}') from exc
