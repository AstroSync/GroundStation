import sys
import glob
from typing import Optional

import serial.tools.list_ports
import serial


def get_available_ports():
    """Возвращает список доступных com портов.
    Пример: get_available_ports() -> ['COM1', 'COM2', ..., 'COMn']
    """
    available_port = []
    if sys.platform.startswith('win'):
        ports = [f'COM{i + 1}s' for i in range(256)]
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


def convert_to_port(**ports_or_serial_nums) -> dict[str, Optional[str]]:
    """Принимает на вход аргументы с портом или серийным номером и заменяет серийный номер на соответствующий порт.
    Если указан некорректный порт или серийник, которого нет в списке доступных устройств, то значение для этого
    аргумента будет None.
    Пример:
        convert_to_port(rx_port='COM36', tx_port='6', radio_port='AH06T3YJA'}) ->
            -> {'rx_port': ['COM36'], 'tx_port': ['COM46'], 'radio_port': ['COM3']}
    """
    comports = serial.tools.list_ports.comports()
    ports = {}
    for k, port in ports_or_serial_nums.items():
        try:
            port = [comport.device for comport in comports if port in (comport.device, comport.serial_number)][0]
            ports.update({k: port})
        except IndexError:
            print(f'{k} has incorrect port os serial number value: {port}')
            ports.update({k: None})
    return ports


if __name__ == '__main__':
    print([(device_info.device, device_info.serial_number) for device_info in serial.tools.list_ports.comports()])
    print(convert_to_port(rx_port='A50285BIA', tx_port='6', radio_port='AH06T3YJA'))
