from __future__ import annotations
import time

from ground_station.hardware.radio.serial_interface import SerialInterface
from ground_station.hardware.radio.sx127x_registers_and_params import SX127x_Registers, SX127x_Mode, SX127x_ISR, \
    SX127x_BW, SX127x_SF, SX127x_CR


class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SX127x_Driver(metaclass = Singleton):
    reg: SX127x_Registers = SX127x_Registers()
    mode: SX127x_Mode = SX127x_Mode()
    isr: SX127x_ISR = SX127x_ISR()
    bw: SX127x_BW = SX127x_BW()
    sf: SX127x_SF = SX127x_SF()
    cr: SX127x_CR = SX127x_CR()

    rfo: int = 0x70
    pa_boost: int = 0xf0

    def __init__(self) -> None:
        self.interface: SerialInterface = SerialInterface()


    def connect(self, port: str) -> bool:
        return self.interface.connect(port=port)

    def disconnect(self):
        return self.interface.disconnect()

    def reset(self) -> None:
        self.interface.reset()

    def set_sleep_mode(self) -> None:
        current_mode: int = self.interface.read(self.reg.REG_OP_MODE) & 0xf8
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.SLEEP_MODE])

    def set_standby_mode(self) -> None:
        current_mode: int = self.interface.read(self.reg.REG_OP_MODE) & 0xf8
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.STDBY_MODE])

    def set_lora_mode(self) -> None:
        self.set_sleep_mode()
        current_mode: int = self.interface.read(self.reg.REG_OP_MODE) & 0x7f
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.LORA_MODE])

    def set_implicit_header(self) -> None:
        current_mode: int = self.interface.read(self.reg.REG_MODEM_CONFIG_1)
        self.interface.write(self.reg.REG_MODEM_CONFIG_1, [current_mode | 0x01])

    def set_explicit_header(self) -> None:
        current_mode: int = self.interface.read(self.reg.REG_MODEM_CONFIG_1)
        self.interface.write(self.reg.REG_MODEM_CONFIG_1, [current_mode | 0xfe])

    def set_payload(self, size: int) -> None:
        self.interface.write(self.reg.REG_PAYLOAD_LENGTH, [size])

    def set_coding_rate(self, coding_rate: int) -> None:
        current_mode: int = self.interface.read(self.reg.REG_MODEM_CONFIG_1) & 0xf1
        self.interface.write(self.reg.REG_MODEM_CONFIG_1, [current_mode | coding_rate])

    def set_bandwidth(self, bandwidth: int) -> None:
        current_mode: int = self.interface.read(self.reg.REG_MODEM_CONFIG_1) & 0x0F
        self.interface.write(self.reg.REG_MODEM_CONFIG_1, [current_mode | bandwidth])

    def set_sf(self, spreading_factor: int) -> None:
        current_mode: int = self.interface.read(self.reg.REG_MODEM_CONFIG_2) & 0x0F
        self.interface.write(self.reg.REG_MODEM_CONFIG_2, [current_mode | spreading_factor])

    def set_crc_mode(self, enable: bool) -> None:
        current_mode: int = self.interface.read(self.reg.REG_MODEM_CONFIG_2) & 0xfb
        self.interface.write(self.reg.REG_MODEM_CONFIG_2, [current_mode | (enable << 2)])

    def __disable_ocp(self) -> None:
        self.interface.write(self.reg.REG_OCP, [0x1f])

    def set_tx_power(self, power: int, pa_pin: int = 0xf0) -> None:
        """ power: from 0 to 20 """
        self.__disable_ocp()
        if pa_pin == self.rfo:
            power = 15 if power >= 15 else power
            self.interface.write(self.reg.REG_PA_DAC, [0x84])
            self.interface.write(self.reg.REG_PA_CONFIG, [power])
        else:
            if power >= 20:
                self.interface.write(self.reg.REG_PA_DAC, [0x87])
            else:
                power = 17 if power <= 2 else power
                self.interface.write(self.reg.REG_PA_DAC, [0x84])
            self.interface.write(self.reg.REG_PA_CONFIG, [pa_pin | (power - 2)])

    def set_sync_word(self, sync_word: int) -> None:
        self.interface.write(self.reg.REG_SYNC_WORD, [sync_word])

    def set_preamble_length(self, length: int) -> None:
        length = 6 if length < 6 else length
        self.interface.write(self.reg.REG_PREAMBLE_MSB, [length >> 8, length & 0xFF])

    def set_auto_gain_control(self, agc_flag: bool) -> None:
        self.interface.write(self.reg.REG_MODEM_CONFIG_3, [agc_flag << 2])

    def set_low_noize_amplifier(self, lna_gain: int, lna_boost: bool) -> None:
        """lna_gain = 1 - min gain; 6 - max gain"""
        self.interface.write(self.reg.REG_LNA, [(lna_gain << 5) + 3 * lna_boost])

    def set_freq(self, freq_hz: int) -> None:
        frf = int((freq_hz / 32000000) * 524288)
        self.interface.write(self.reg.REG_FR_MSB, [frf >> 16, (frf >> 8) & 0xFF, frf & 0xFF])

    def set_fifo_addr_ptr(self, address: int) -> None:
        self.interface.write(self.reg.REG_FIFO_ADDR_PTR, [address])

    def set_rx_tx_fifo_base_addr(self, rx_ptr: int, tx_ptr: int) -> None:
        self.interface.write(self.reg.REG_FIFO_TX_BASE_ADDR, [tx_ptr])
        self.interface.write(self.reg.REG_FIFO_RX_BASE_ADDR, [rx_ptr])

    def write_fifo(self, data: list[int] | bytes) -> None:
        self.set_fifo_addr_ptr(0)
        self.set_payload(len(data))
        self.interface.write(self.reg.REG_FIFO, [*data])

    def get_operation_mode(self) -> int:
        return self.interface.read(self.reg.REG_OP_MODE) & 0x07

    def get_isr_registers(self) -> int:
        return self.interface.read(self.reg.REG_IRQ_FLAGS)

    def get_rx_done_flag(self) -> int:
        return self.interface.read(self.reg.REG_IRQ_FLAGS) & self.isr.IRQ_RXDONE

    def get_tx_done_flag(self) -> int:
        return self.interface.read(self.reg.REG_IRQ_FLAGS) & self.isr.IRQ_TXDONE

    def get_crc_flag(self) -> int:
        return self.interface.read(self.reg.REG_IRQ_FLAGS) & self.isr.IRQ_CRC

    def reset_irq_flags(self) -> None:
        self.interface.write(self.reg.REG_IRQ_FLAGS, [0xff])

    def set_low_data_rate_optimize(self, optimization_flag: bool) -> None:
        current_state: int = self.interface.read(self.reg.REG_MODEM_CONFIG_3) & 0xf7
        self.interface.write(self.reg.REG_MODEM_CONFIG_3, [current_state | (optimization_flag * (1 << 3))])

    def set_tx_mode(self) -> None:
        current_mode: int = self.interface.read(self.reg.REG_OP_MODE) & 0xf8
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.TX_MODE])

    def set_rx_continuous_mode(self) -> None:
        current_mode: int = self.interface.read(self.reg.REG_OP_MODE) & 0xf8
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.RXCONT_MODE])

    def get_all_registers(self) -> list[int]:
        return self.interface.read_several(0x01, 0x70)


if __name__ == '__main__':
    lora: SX127x_Driver = SX127x_Driver()
    # print(lora.mode)
    lora.connect('COM3')
    time.sleep(0.1)
    print(f'{lora.interface.read_several(6, 2)}')
    print(f'{lora.interface.read_several(6, 2)}')
    print(f'{lora.interface.read_several(6, 2)}')
