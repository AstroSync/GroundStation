from __future__ import annotations
import serial
from serial import SerialBase


def check_connection(func):
    def _wrapper(*args, **kwargs):
        if not args[0].connection_status:
            raise RuntimeError('Radio is not connected')
        return func(*args, **kwargs)
    return _wrapper


class SerialInterface:
    __interface: SerialBase
    connection_status: bool = False

    def connect(self, port: str) -> bool:
        if self.connection_status:
            return True
        try:
            self.__interface = serial.Serial(port, 500000)
            if self.__interface.isOpen():
                self.connection_status = True
                return True
            raise ConnectionError(f"Can\'t connect to {port}. Probably device is busy")
        except serial.SerialException:
            return False

    def disconnect(self):
        if self.connection_status:
            self.__interface.close()
            self.connection_status = False

    @check_connection
    def read(self, address: int) -> int:
        self.__interface.write(bytes([1, address]))
        return int.from_bytes(self.__try_read(), "big")

    @check_connection
    def write(self, address: int, data: list[int]) -> int:
        if len(data) == 1:
            self.__interface.write(bytes([2, address, data[0]]))
        else:
            self.__interface.write(bytes([8, address, len(data), *data]))
        return int.from_bytes(self.__try_read(), "big")

    @check_connection
    def run_tx_then_rx_cont(self) -> int:
        self.__interface.write(bytes([21]))
        return int.from_bytes(self.__try_read(), "big")

    @check_connection
    def run_tx_then_rx_single(self) -> int:
        self.__interface.write(bytes([22]))
        return int.from_bytes(self.__try_read(), "big")

    @check_connection
    def read_several(self, address: int, amount: int) -> list[int]:
        self.__interface.write(bytes([7, address, amount]))
        return list(self.__try_read(amount))

    @check_connection
    def reset(self) -> int:
        self.__interface.write(bytes([6]))
        return int.from_bytes(self.__try_read(), "big")

    def __try_read(self, amount: int = 1) -> bytes:
        try:
            data: bytes | None= self.__interface.read(amount)
            if data is None:
                raise RuntimeError('Radio somehow read None data')
            return data
        except TimeoutError as exc:
            raise TimeoutError(f'Radio reading timeout: {exc}') from exc

if __name__ == '__main__':
    ser: SerialInterface = SerialInterface()
    print(ser.connect('COM3'))
