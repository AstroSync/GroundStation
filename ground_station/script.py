from ground_station.hardware.radio.lora_controller import LoRaController

lora = LoRaController()
lora.init()
data = lora.rx_done_isr()
if data is not None:
    lora.send(b'some_data')
else:
    lora.send(b'data')
lora.send(b'request two variables')
var1, var2, *_ = lora.rx_done_isr()
