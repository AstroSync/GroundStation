from __future__ import annotations
import time

from ground_station.hardware.radio.lora_serial_driver import LoRaDriver, Registers


class LoRaController(LoRaDriver):
    def __init__(self, api_name='radio', **kwargs):
        super().__init__(**kwargs)  # super(LoRa_Controller, self).__init__(**kwargs)
        self.api_name = api_name
        self.coding_rate = kwargs.get('ecr', self.cr.CR5)  # error coding rate
        self.bandwidth = kwargs.get('bw', self.bw.BW250)  # bandwidth
        self.spread_factor = kwargs.get('sf', self.sf.SF10)  # spreading factor
        self.freq = kwargs.get('freq', 436700000)   # 436700000
        self.crc = kwargs.get('crc', True)  # check crc
        self.tx_power = kwargs.get('tx_power', 11)  # dB
        self.sync_word = kwargs.get('sync_word', 0x12)
        self.preamble_len = kwargs.get('preamble_len', 8)
        self.auto_gain_control = kwargs.get('agc', True)  # auto gain control
        self.payload_size = kwargs.get('payload_size', 10)  # for implicit mode
        self.lna_gain = kwargs.get('lna_gain', 3)  # 1 - min; 6 - max
        self.lna_boost = kwargs.get('lna_boost', False)  # 150% LNA current
        self.implicit_mode = kwargs.get('implicit_mode', False)  # fixed payload size
        self.rx_timeout = 30

    def init(self):
        self.interface.reset()
        time.sleep(0.1)
        self.set_lora_mode()
        self.set_explicit_header()
        self.set_coding_rate(self.coding_rate)
        self.set_bandwidth(self.bandwidth)
        self.set_sf(self.spread_factor)
        _ = self.set_crc_on() if self.crc else self.set_crc_off()
        self.set_tx_power(self.tx_power, self.rfo)
        self.set_sync_word(self.sync_word)
        self.set_preamble_length(self.preamble_len)
        self.set_agc(self.auto_gain_control)
        self.set_lna(self.lna_gain, self.lna_boost)
        self.interface.write(self.reg.REG_FIFO_TX_BASE_ADDR, [0])
        self.interface.write(self.reg.REG_FIFO_RX_BASE_ADDR, [0])
        self.interface.write(self.reg.REG_DETECT_OPTIMIZE, [0xc3])  # default value
        self.interface.write(self.reg.REG_DETECT_OPTIMIZE, [0x0a])  # SF7 to SF12
        self.set_freq(self.freq)
        self.set_low_data_rate_optimize(True)

    def connect(self, port: str):
        connection_status = super(LoRaController, self).connect(port)
        if connection_status:
            print('Radio connected.\nStart initialization...')
            self.init()
            print('Radio inited')
        else:
            print('Radio is not connected!')
            # raise Exception("Can't connect to radio.")

    def send(self, data: list[int] | bytes):
        if self.get_op_mode() != self.mode.STDBY_MODE:
            self.set_standby_mode()
        # optimization_flag, _, _ = self.__calculate_packet(data)
        # self.set_low_data_rate_optimize(True)
        self.write_fifo(data)
        # self.set_tx_mode()
        self.interface.run_tx_then_rx_single()

    def set_rx_timeout(self, sec: int):
        self.rx_timeout = sec

    def receive(self):
        # optimization_flag, _, _ = self.__calculate_packet(data)
        # self.set_low_data_rate_optimize(optimization_flag)
        if self.get_op_mode() != self.mode.STDBY_MODE:
            self.set_standby_mode()
        self.set_rx_continuous_mode()

    # def __calculate_packet(self, packet: list[int], force_optimization=True) -> tuple[bool, int, int]:
    #     ecr = 4 + self.coding_rate // 2
    #     if self.implicit_mode:
    #         payload_size = self.payload_size
    #     else:
    #         payload_size = len(packet)
    #     t_sym = 2 ** self.spread_factor / self.bandwidth * 1000
    #     optimization_flag = True if force_optimization else t_sym > 16
    #     preamble_time = (self.preamble_len + 4.25) * t_sym
    #     tmp_poly = max((8 * payload_size - 4 * self.spread_factor + 28 + 16 - 20 * self.implicit_mode), 0)
    #     payload_symbol_nb = 8 + (tmp_poly / (4 * (self.spread_factor - 2 * optimization_flag))) * ecr
    #     payload_time = payload_symbol_nb * t_sym
    #     packet_time = payload_time + preamble_time
    #     return optimization_flag, packet_time, payload_time

    def get_rssi_packet(self) -> int:
        return self.interface.read(self.reg.REG_PKT_RSSI_VALUE) - (164 if self.freq < 0x779E6 else 157)

    def get_rssi_value(self) -> int:
        return self.interface.read(self.reg.REG_RSSI_VALUE) - (164 if self.freq < 0x779E6 else 157)

    def get_snr(self) -> int:
        return self.interface.read(self.reg.REG_PKT_SNR_VALUE) // 4

    def get_snr_and_rssi(self) -> tuple[int, int]:
        snr, rssi = self.interface.read_several(self.reg.REG_PKT_SNR_VALUE, 2)
        return snr // 4, rssi - (164 if self.freq < 0x779E6 else 157)

    def rx_done_isr(self) -> tuple[list[int], int, int]:
        start_time = time.perf_counter()
        while True:
            current_time = time.perf_counter()
            if current_time - start_time > self.rx_timeout:
                print('no data =(')
                return [], None, None
            data, snr, rssi_pkt = self.check_rx_input()
            if len(data) > 0:
                return data, snr, rssi_pkt
            time.sleep(0.1)
            # gevent.sleep(0.1)

    def check_rx_input(self) -> tuple[list[int], int, int]:
        if self.get_rx_done_flag():  # TODO: check this method works is correct
            current_address = self.interface.read(self.reg.REG_FIFO_RX_CURRENT_ADDR)
            # TODO: remember previous address to minimize tcp packet (do not need to set fifo address ptr every time)
            self.interface.write(self.reg.REG_FIFO_ADDR_PTR, [current_address])
            if self.implicit_mode:
                data = self.interface.read_several(self.reg.REG_FIFO, self.payload_size)
            else:
                rx_data_amount = self.interface.read(self.reg.REG_RX_NB_BYTES)
                data = self.interface.read_several(self.reg.REG_FIFO, rx_data_amount)
            # crc = self.get_crc_flag()
            snr, rssi_pkt = self.get_snr_and_rssi()
            self.reset_irq_flags()
            return data, snr, rssi_pkt
        return [], None, None

    def dump_memory(self):
        dump_mem = self.get_all_registers()
        mem = {k: dump_mem[v - 1] for k, v in self.reg.items()}
        return Registers(mem)


if __name__ == '__main__':
    lora = LoRaController()
    lora.connect(port='COM3')
    print(lora.dump_memory())
    # lora.send(b'hello' * 50)
    # lora.send(b'hello' * 50)
    # lora.send(b'hello' * 50)
    lora.receive()
    print(lora.rx_done_isr())
    # print(lora.dump_memory())
