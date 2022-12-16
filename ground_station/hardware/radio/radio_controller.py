from __future__ import annotations
import threading
import time
from typing import Callable
from dataclasses import dataclass
from ast import literal_eval
from ground_station.hardware.radio.sx127x_driver import SX127x_Driver


@dataclass
class LoRaRxPacket:
    data: list[int]
    snr: int
    rssi_pkt: int
    crc_flag: int

@dataclass
class LoRaTxPacket:
    Tsym: float
    Tpkt: float
    low_datarate_opt_flag: bool


class RadioController(SX127x_Driver):
    def __init__(self, api_name='radio', **kwargs) -> None:
        super().__init__(**kwargs)  # super(LoRa_Controller, self).__init__(**kwargs)
        self.api_name: str = api_name
        self.coding_rate: int = kwargs.get('ecr', self.cr.CR5)  # error coding rate
        self.bandwidth: int = kwargs.get('bw', self.bw.BW250)  # bandwidth  BW250
        self.spread_factor: int = kwargs.get('sf', self.sf.SF10)  # spreading factor  SF10
        self.freq: int = kwargs.get('freq', 436700000)   # 436700000
        self.crc: bool = kwargs.get('crc', True)  # check crc
        self.tx_power: int = kwargs.get('tx_power', 14)  # dB
        self.sync_word: int = kwargs.get('sync_word', 0x12)
        self.preamble_len: int = kwargs.get('preamble_len', 8)
        self.auto_gain_control: bool = kwargs.get('agc', True)  # auto gain control
        self.payload_size: int = kwargs.get('payload_size', 10)  # for implicit mode
        self.lna_gain: int = kwargs.get('lna_gain', 5)  # 1 - min; 6 - max
        self.lna_boost: bool = kwargs.get('lna_boost', False)  # 150% LNA current
        self.implicit_mode: bool = kwargs.get('implicit_mode', False)  # fixed payload size

        self.__rx_thread = threading.Thread(name='rx_thread', target=self.rx_routine, daemon=True)
        self.__rx_callback: Callable | None = None
        self.__tx_callback: Callable | None = None
        self.__stop_rx_routine_flag: bool = False
        self.__rx_timeout_sec: int = 30
        self.__rx_buffer: list = []

    def __init(self) -> None:
        self.interface.reset()
        time.sleep(0.1)
        self.set_lora_mode()
        self.set_explicit_header()
        self.set_coding_rate(self.coding_rate)
        self.set_bandwidth(self.bandwidth)
        self.set_sf(self.spread_factor)
        self.set_crc_mode(self.crc)
        self.set_tx_power(self.tx_power, self.rfo)
        self.set_sync_word(self.sync_word)
        self.set_preamble_length(self.preamble_len)
        self.set_auto_gain_control(self.auto_gain_control)
        self.set_low_noize_amplifier(self.lna_gain, self.lna_boost)
        self.set_rx_tx_fifo_base_addr(0, 0)
        self.set_freq(self.freq)
        self.set_low_data_rate_optimize(True)

    def onReceive(self, callback: Callable):
        self.__rx_callback = callback

    def onTrancieve(self, callback: Callable):
        self.__tx_callback = callback

    def start_rx_thread(self) -> None:
        if not self.__rx_thread.is_alive():
            print('Start Rx thread')
            self.__stop_rx_routine_flag = False
            self.__rx_thread = threading.Thread(name='radio_rx_thread', target=self.rx_routine, daemon=True)
            self.__rx_thread.start()

    def stop_rx_thread(self) -> None:
        self.__stop_rx_routine_flag = True
        # self.__rx_thread.join(timeout=0.8)

    def connect(self, port: str) -> bool:
        if super().connect(port):
            print('Radio connected.\nStart initialization...')
            self.__init()
            print('Radio inited.')
            self.receive()
            self.start_rx_thread()
            return True
            # print(self.get_operation_mode())
        print('Radio is not connected!')
        return False
            # raise Exception("Can't connect to radio.")
    def disconnect(self):
        self.stop_rx_thread()
        return super().disconnect()

    def send_single(self, data: list[int] | bytes) -> None:
        # if self.get_operation_mode() != self.mode.STDBY_MODE:
        #     self.set_standby_mode()
        # tx_pkt: LoRaTxPacket = self.calculate_packet(data)
        # self.set_low_data_rate_optimize(True)
        if not self.__stop_rx_routine_flag:
            self.stop_rx_thread()
        buffer_size = 255
        # timeout_counter_sec = 2
        if len(data) > buffer_size:
            chunks: list[list[int] | bytes] = [data[i:i + buffer_size] for i in range(0, len(data), buffer_size)]
            print(f'big parcel: {len(data)=}')
            for chunk in chunks:
                self.write_fifo(chunk)
                self.interface.run_tx_then_rx_cont()
                time.sleep(1.5)
                # while not self.get_tx_done_flag() and timeout_counter_sec > 0:
                #     time.sleep(0.1)
                #     timeout_counter_sec -= 0.1
                #     print(self.get_())
                #     self.reset_irq_flags()
        else:
            self.write_fifo(data)
            self.interface.run_tx_then_rx_cont()

        if self.__tx_callback is not None:
            self.__tx_callback(f'tx > {data}')

        if self.__stop_rx_routine_flag:
            self.start_rx_thread()

    def set_rx_timeout(self, sec: int) -> None:
        self.__rx_timeout_sec = sec

    def receive(self) -> None:
        # tx_ptk = self.__calculate_packet(data)
        # self.set_low_data_rate_optimize(optimization_flag)
        mode: int = self.get_operation_mode()
        if mode != self.mode.RXCONT_MODE:
            if mode != self.mode.STDBY_MODE:
                self.set_standby_mode()
            self.set_rx_continuous_mode()

    def calculate_packet(self, packet: list[int] | bytes, force_optimization=True) -> LoRaTxPacket:
        ecr: int = 4 + self.coding_rate // 2
        if self.implicit_mode:
            payload_size = self.payload_size
        else:
            payload_size: int = len(packet)
        t_sym: float = 2 ** self.spread_factor / self.bandwidth * 1000
        optimization_flag: bool = True if force_optimization else t_sym > 16
        preamble_time: float = (self.preamble_len + 4.25) * t_sym
        tmp_poly: int = max((8 * payload_size - 4 * self.spread_factor + 28 + 16 - 20 * self.implicit_mode), 0)
        payload_symbol_nb: float = 8 + (tmp_poly / (4 * (self.spread_factor - 2 * optimization_flag))) * ecr
        payload_time: float = payload_symbol_nb * t_sym
        packet_time: float = payload_time + preamble_time
        return LoRaTxPacket(payload_time, packet_time, optimization_flag)

    def get_rssi_packet(self) -> int:
        return self.interface.read(self.reg.REG_PKT_RSSI_VALUE) - (164 if self.freq < 0x779E6 else 157)

    def get_rssi_value(self) -> int:
        return self.interface.read(self.reg.REG_RSSI_VALUE) - (164 if self.freq < 0x779E6 else 157)

    def get_snr(self) -> int:
        return self.interface.read(self.reg.REG_PKT_SNR_VALUE) // 4

    def get_snr_and_rssi(self) -> tuple[int, int]:
        snr, rssi = self.interface.read_several(self.reg.REG_PKT_SNR_VALUE, 2)
        return snr // 4, rssi - (164 if self.freq < 0x779E6 else 157)

    def rx_done_isr(self) -> LoRaRxPacket | None:
        start_time: float = time.perf_counter()
        while True:
            current_time: float = time.perf_counter()
            if current_time - start_time > self.__rx_timeout_sec:
                print('SX1278 rx timeout')
                return None
            pkt: LoRaRxPacket | None = self.check_rx_input()
            if pkt is not None:
                if len(pkt.data) > 0:
                    return pkt
            time.sleep(0.2)

    def check_rx_input(self) -> LoRaRxPacket | None:
        rx_flag: int = self.get_rx_done_flag()
        if rx_flag:  # TODO: check this method works is correct
            current_address: int = self.interface.read(self.reg.REG_FIFO_RX_CURRENT_ADDR)
            # TODO: remember previous address to minimize tcp packet (do not need to set fifo address ptr every time)
            self.interface.write(self.reg.REG_FIFO_ADDR_PTR, [current_address])
            if self.implicit_mode:
                data: list[int] = self.interface.read_several(self.reg.REG_FIFO, self.payload_size)
            else:
                rx_data_amount: int = self.interface.read(self.reg.REG_RX_NB_BYTES)
                data = self.interface.read_several(self.reg.REG_FIFO, rx_data_amount)
            crc: int = self.get_crc_flag()
            self.reset_irq_flags()
            return LoRaRxPacket(data, *self.get_snr_and_rssi(), crc)
        return None

    # def dump_memory(self) -> SX127x_Registers:
    #     dump_mem: list[int] = self.get_all_registers()
    #     mem = {k: dump_mem[v - 1] for k, v in self.reg.items()}
    #     return SX127x_Registers(mem)

    def clear_rx_buffer(self):
        self.__rx_buffer.clear()

    def get_rx_buffer(self):
        return self.__rx_buffer

    def rx_routine(self) -> None:
        while not self.__stop_rx_routine_flag:
            pkt: LoRaRxPacket | None = self.check_rx_input()
            if pkt is not None:
                if len(pkt.data) > 0:
                    print(pkt)
                    self.__rx_buffer.append(pkt.data)
                    if self.__rx_callback is not None:
                        self.__rx_callback(f'rx < {pkt.data}')
            time.sleep(0.5)

    def user_cli(self) -> None:
        try:
            while(True):
                data = literal_eval(input('> '))
                if isinstance(data, tuple):
                    data = list(data)
                if isinstance(data, (list, bytes)):
                    self.send_single(data)
                else:
                    print('Incorrect data format. You can send list[int] or bytes.')
        except KeyboardInterrupt:
            print('Shutdown radio driver')

if __name__ == '__main__':
    lora: RadioController = RadioController()
    if lora.connect(port='COM3'):
        lora.user_cli()

    # print(lora.rx_done_isr())
    # print(lora.dump_memory())
