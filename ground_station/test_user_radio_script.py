import time
from ground_station.hardware.naku_device_api import gs_device
from ground_station.web_secket_client import WebSocketClient

radio = gs_device.radio
ws_client = WebSocketClient()

while True:
    radio.send_single([14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 1])
    ws_client.send(f'tx > {[14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 1]}')
    time.sleep(1)
    radio.send_single([14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 3])
    ws_client.send(f'tx > {[14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 3]}')
    time.sleep(1)
    radio.send_single([14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 5])
    ws_client.send(f'tx > {[14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 5]}')
    time.sleep(1)
    radio.send_single([14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 7])
    ws_client.send(f'tx > {[14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 7]}')
    time.sleep(1)
    radio.send_single([14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 9])
    ws_client.send(f'tx > {[14, 10, 6, 1, 201, 1, 1, 1, 1, 0, 28, 0, 0, 0, 9]}')
    time.sleep(1)
    radio.send_single([26, 10, 6, 1, 201, 1, 1, 1, 1, 0, 32, 0, 0, 0, 13, 128, 8, 0, 69, 116, 0, 0, 0, 0, 0, 0, 0])
    ws_client.send(f'tx > {[26, 10, 6, 1, 201, 1, 1, 1, 1, 0, 32, 0, 0, 0, 13, 128, 8, 0, 69, 116, 0, 0, 0, 0, 0, 0, 0]}')
    time.sleep(1)
    radio.send_single([26, 10, 6, 1, 201, 1, 1, 1, 1, 0, 33, 0, 0, 0, 13, 32, 12, 0, 69, 116, 0, 0, 0, 0, 0, 0, 0])
    ws_client.send(f'tx > {[26, 10, 6, 1, 201, 1, 1, 1, 1, 0, 33, 0, 0, 0, 13, 32, 12, 0, 69, 116, 0, 0, 0, 0, 0, 0, 0]}')
    time.sleep(1)
    radio.send_single([26, 10, 6, 1, 201, 1, 1, 1, 1, 0, 34, 0, 0, 0, 13, 136, 4, 0, 53, 116, 0, 0, 0, 0, 0, 0, 0])
    ws_client.send(f'tx > {[26, 10, 6, 1, 201, 1, 1, 1, 1, 0, 34, 0, 0, 0, 13, 136, 4, 0, 53, 116, 0, 0, 0, 0, 0, 0, 0]}')
    time.sleep(1)
    radio.send_single([26, 10, 6, 1, 201, 1, 1, 1, 1, 0, 35, 0, 0, 0, 13, 40, 8, 0, 53, 116, 0, 0, 0, 0, 0, 0, 0])
    ws_client.send(f'tx > {[26, 10, 6, 1, 201, 1, 1, 1, 1, 0, 35, 0, 0, 0, 13, 40, 8, 0, 53, 116, 0, 0, 0, 0, 0, 0, 0]}')
    time.sleep(1)
