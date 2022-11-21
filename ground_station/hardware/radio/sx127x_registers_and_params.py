from dataclasses import dataclass

@dataclass(frozen=True)
class SX127x_Registers:
    REG_FIFO: int = 0x00
    REG_OP_MODE: int = 0x01
    REG_FR_MSB: int = 0x06
    REG_FR_DIM: int = 0x07
    REG_FR_LSB: int = 0x08
    REG_PA_CONFIG: int = 0x09
    REG_OCP: int = 0x0B
    REG_LNA: int = 0x0C
    REG_FIFO_ADDR_PTR: int = 0x0D
    REG_FIFO_TX_BASE_ADDR: int = 0x0E
    REG_FIFO_RX_BASE_ADDR: int = 0x0F
    REG_FIFO_RX_CURRENT_ADDR: int = 0x10
    REG_IRQ_FLAGS: int = 0x12
    REG_RX_NB_BYTES: int = 0x13
    REG_RX_HEADER_CNT_VALUE_MSB: int = 0x14
    REG_RX_HEADER_CNT_VALUE_LSB: int = 0x15
    REG_RX_PACKET_CNT_VALUE_MSB: int = 0x16
    REG_RX_PACKET_CNT_VALUE_LSB: int = 0x17
    REG_PKT_SNR_VALUE: int = 0x19
    REG_PKT_RSSI_VALUE: int = 0x1A
    REG_RSSI_VALUE: int = 0x1B
    REG_MODEM_CONFIG_1: int = 0x1D
    REG_MODEM_CONFIG_2: int = 0x1E
    REG_MODEM_CONFIG_3: int = 0x26
    REG_PAYLOAD_LENGTH: int = 0x22
    REG_FIFO_RX_BYTE_ADDR: int = 0x25
    REG_PA_DAC: int = 0x4d
    REG_DIO_MAPPING_1: int = 0x40
    REG_DIO_MAPPING_2: int = 0x41
    REG_TEMP: int = 0x3c
    REG_SYNC_WORD: int = 0x39
    REG_PREAMBLE_MSB: int = 0x20
    REG_PREAMBLE_LSB: int = 0x21
    REG_DETECT_OPTIMIZE: int = 0x31
    REG_DETECTION_THRESHOLD: int = 0x37

@dataclass(frozen=True)
class SX127x_Mode:
    LORA_MODE: int = 0x80
    SLEEP_MODE: int = 0x00
    STDBY_MODE: int = 0x01
    TX_MODE: int = 0x03
    RXCONT_MODE: int = 0x05

@dataclass(frozen=True)
class SX127x_ISR:
    IRQ_RX_TIMEOUT: int = 0x80
    IRQ_RXDONE: int = 0x40
    IRQ_TXDONE: int = 0x08
    IRQ_CRC: int = 0x20

@dataclass(frozen=True)
class SX127x_BW:
    BW7_8: int = 0
    BW10_4: int = 1 << 4
    BW15_6: int = 2 << 4
    BW20_8: int = 3 << 4
    BW31_25: int = 4 << 4
    BW41_7: int = 5 << 4
    BW62_5: int = 6 << 4
    BW125: int = 7 << 4
    BW250: int = 8 << 4
    BW500: int = 9 << 4

@dataclass(frozen=True)
class SX127x_SF:
    SF7: int = 7 << 4
    SF8: int = 8 << 4
    SF9: int = 9 << 4
    SF10: int = 10 << 4
    SF11: int = 11 << 4
    SF12: int = 12 << 4

@dataclass(frozen=True)
class SX127x_CR:
    CR5: int = 1 << 1
    CR6: int = 2 << 1
    CR7: int = 3 << 1
    CR8: int = 4 << 1

if __name__ == '__main__':
    print(SX127x_Registers())
