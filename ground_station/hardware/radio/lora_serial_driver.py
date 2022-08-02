from __future__ import annotations
import time

from GS_backend.hardware.radio.serial_interface import SerialInterface


class Registers(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    # def __init__.py(self, regs: list[str | tuple[str, int]], start: int):
    #     super(Registers, self).__init__.py()
    #     [self.__setattr__(reg, address) if type(reg) == str else self.__setattr__(reg[0], reg[1])
    #      for address, reg in enumerate(regs, start=start)]

    def __str__(self):
        return "".join([f'{k}: {v:#02x}\n' if type(v) == int else f'{k}: {v}\n' for k, v in self.items()])


class LoRa_Driver:
    reg = Registers({'REG_FIFO': 0x00,
                     'REG_OP_MODE': 0x01,
                     'REG_FR_MSB': 0x06,
                     'REG_FR_DIM': 0x07,
                     'REG_FR_LSB': 0x08,
                     'REG_PA_CONFIG': 0x09,
                     'REG_OCP': 0x0B,
                     'REG_LNA': 0x0C,
                     'REG_FIFO_ADDR_PTR': 0x0D,
                     'REG_FIFO_TX_BASE_ADDR': 0x0E,
                     'REG_FIFO_RX_BASE_ADDR': 0x0F,
                     'REG_FIFO_RX_CURRENT_ADDR': 0x10,
                     'REG_IRQ_FLAGS': 0x12,
                     'REG_RX_NB_BYTES': 0x13,
                     'REG_RX_HEADER_CNT_VALUE_MSB': 0x14,
                     'REG_RX_HEADER_CNT_VALUE_LSB': 0x15,
                     'REG_RX_PACKET_CNT_VALUE_MSB': 0x16,
                     'REG_RX_PACKET_CNT_VALUE_LSB': 0x17,
                     'REG_PKT_SNR_VALUE': 0x19,
                     'REG_PKT_RSSI_VALUE': 0x1A,
                     'REG_RSSI_VALUE': 0x1B,
                     'REG_MODEM_CONFIG_1': 0x1D,
                     'REG_MODEM_CONFIG_2': 0x1E,
                     'REG_MODEM_CONFIG_3': 0x26,
                     'REG_PAYLOAD_LENGTH': 0x22,
                     'REG_FIFO_RX_BYTE_ADDR': 0x25,
                     'REG_PA_DAC': 0x4d,
                     'REG_DIO_MAPPING_1': 0x40,
                     'REG_DIO_MAPPING_2': 0x41,
                     'REG_TEMP': 0x3c,
                     'REG_SYNC_WORD': 0x39,
                     'REG_PREAMBLE_MSB': 0x20,
                     'REG_PREAMBLE_LSB': 0x21,
                     'REG_DETECT_OPTIMIZE': 0x31,
                     'REG_DETECTION_THRESHOLD': 0x37})

    mode = Registers({'LORA_MODE': 0x80,
                      'SLEEP_MODE': 0x00,
                      'STDBY_MODE': 0x01,
                      'TX_MODE': 0x03,
                      'RXCONT_MODE': 0x05})

    isr = Registers({'IRQ_RX_TIMEOUT': 0x80,
                     'IRQ_RXDONE': 0x40,
                     'IRQ_TXDONE': 0x08,
                     'IRQ_CRC': 0x20})

    bw = Registers({'BW7_8': 0,
                    'BW10_4': 1 << 4,
                    'BW15_6': 2 << 4,
                    'BW20_8': 3 << 4,
                    'BW31_25': 4 << 4,
                    'BW41_7': 5 << 4,
                    'BW62_5': 6 << 4,
                    'BW125': 7 << 4,
                    'BW250': 8 << 4,
                    'BW500': 9 << 4})

    sf = Registers({'SF7': 7 << 4,
                    'SF8': 8 << 4,
                    'SF9': 9 << 4,
                    'SF10': 10 << 4,
                    'SF11': 11 << 4,
                    'SF12': 12 << 4})

    cr = Registers({'CR5': 1 << 1,
                    'CR6': 2 << 1,
                    'CR7': 3 << 1,
                    'CR8': 4 << 1})

    def __init__(self, **kwargs):
        self.interface = SerialInterface()
        self.rfo = 0x70
        self.pa_boost = 0xf0

    def connect(self, port: str) -> bool:
        return self.interface.connect(port=port)

    def set_sleep_mode(self):
        current_mode = self.interface.read(self.reg.REG_OP_MODE) & 0xf8
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.SLEEP_MODE])

    def set_standby_mode(self):
        current_mode = self.interface.read(self.reg.REG_OP_MODE) & 0xf8
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.STDBY_MODE])

    def set_lora_mode(self):
        self.set_sleep_mode()
        current_mode = self.interface.read(self.reg.REG_OP_MODE) & 0x7f
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.LORA_MODE])

    def set_implicit_header(self):
        current_mode = self.interface.read(self.reg.REG_MODEM_CONFIG_1)
        self.interface.write(self.reg.REG_MODEM_CONFIG_1, [current_mode | 0x01])

    def set_explicit_header(self):
        current_mode = self.interface.read(self.reg.REG_MODEM_CONFIG_1)
        self.interface.write(self.reg.REG_MODEM_CONFIG_1, [current_mode | 0xfe])

    def set_payload(self, size: int):
        self.interface.write(self.reg.REG_PAYLOAD_LENGTH, [size])

    def set_coding_rate(self, cr: int):
        current_mode = self.interface.read(self.reg.REG_MODEM_CONFIG_1) & 0xf1
        self.interface.write(self.reg.REG_MODEM_CONFIG_1, [current_mode | cr])

    def set_bandwidth(self, bw: int):
        current_mode = self.interface.read(self.reg.REG_MODEM_CONFIG_1) & 0x0F
        self.interface.write(self.reg.REG_MODEM_CONFIG_1, [current_mode | bw])

    def set_sf(self, sf: int):
        current_mode = self.interface.read(self.reg.REG_MODEM_CONFIG_2) & 0x0F
        self.interface.write(self.reg.REG_MODEM_CONFIG_2, [current_mode | sf])

    def set_crc_on(self):
        current_mode = self.interface.read(self.reg.REG_MODEM_CONFIG_2) & 0xfb
        self.interface.write(self.reg.REG_MODEM_CONFIG_2, [current_mode | (0x01 << 2)])

    def set_crc_off(self):
        current_mode = self.interface.read(self.reg.REG_MODEM_CONFIG_2) & 0xfb
        self.interface.write(self.reg.REG_MODEM_CONFIG_2, [current_mode])

    def __disable_ocp(self):
        self.interface.write(self.reg.REG_OCP, [0x1f])

    def set_tx_power(self, power: int, pa_pin: int = 'PA_BOOST'):
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

    def set_sync_word(self, sync_word: int):
        self.interface.write(self.reg.REG_SYNC_WORD, [sync_word])

    def set_preamble_length(self, length: int):
        length = 6 if length < 6 else length
        self.interface.write(self.reg.REG_PREAMBLE_MSB, [length >> 8, length & 0xFF])

    def set_agc(self, agc_flag: bool):
        self.interface.write(self.reg.REG_MODEM_CONFIG_3, [agc_flag << 2])

    def set_lna(self, lna_gain: int, lna_boost: bool):
        """lna_gain = 1 - min gain; 6 - max gain"""
        self.interface.write(self.reg.REG_LNA, [(lna_gain << 5) + 3 * lna_boost])

    def set_freq(self, freq_hz: int):
        frf = int((freq_hz / 32000000) * 524288)
        self.interface.write(self.reg.REG_FR_MSB, [frf >> 16, (frf >> 8) & 0xFF, frf & 0xFF])

    def set_addr_ptr(self, address: int):
        self.interface.write(self.reg.REG_FIFO_ADDR_PTR, [address])

    def write_fifo(self, data: list[int] | bytes):
        self.set_addr_ptr(0)
        self.set_payload(len(data))
        self.interface.write(self.reg.REG_FIFO, [*data])

    def get_op_mode(self):
        return self.interface.read(self.reg.REG_OP_MODE) & 0x07

    def get_rx_done_flag(self):
        return self.interface.read(self.reg.REG_IRQ_FLAGS) & self.isr.IRQ_RXDONE

    def get_tx_done_flag(self):
        return self.interface.read(self.reg.REG_IRQ_FLAGS) & self.isr.IRQ_TXDONE

    def get_crc_flag(self):
        return self.interface.read(self.reg.REG_IRQ_FLAGS) & self.isr.IRQ_CRC

    def reset_irq_flags(self):
        self.interface.write(self.reg.REG_IRQ_FLAGS, [0xff])

    def set_low_data_rate_optimize(self, optimization_flag: bool):
        current_state = self.interface.read(self.reg.REG_MODEM_CONFIG_3) & 0xf7
        self.interface.write(self.reg.REG_MODEM_CONFIG_3, [current_state | (optimization_flag * (1 << 3))])

    def set_tx_mode(self):
        current_mode = self.interface.read(self.reg.REG_OP_MODE) & 0xf8
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.TX_MODE])

    def set_rx_continuous_mode(self):
        current_mode = self.interface.read(self.reg.REG_OP_MODE) & 0xf8
        self.interface.write(self.reg.REG_OP_MODE, [current_mode | self.mode.RXCONT_MODE])

    def get_all_registers(self):
        return self.interface.read_several(0x01, 0x70)


if __name__ == '__main__':
    lora = LoRa_Driver()
    # print(lora.mode)
    lora.interface.reset()
    time.sleep(0.1)
    print(f'{lora.interface.read_several(6, 2)}')
    print(f'{lora.interface.read_several(6, 2)}')
    print(f'{lora.interface.read_several(6, 2)}')
