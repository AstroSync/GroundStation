from threading import Thread
import time
from websocket import create_connection
ws = create_connection("ws://localhost:8080/websocket_api/ws/NSU_GS/123")

def send_data() -> None:
    try:
        while True:
            time.sleep(0.1)
            data = input('>')
            ws.send(data)
    except (KeyboardInterrupt, EOFError):
        return

thread: Thread = Thread(target=send_data, daemon=True)
thread.start()

try:
    while True:
        result =  ws.recv()
        print(f"Received: {result}")
except KeyboardInterrupt:
    print('\nShutdown client')
    ws.close()
# import websocket
# import _thread
# import time
# import rel

# def on_message(ws, message):
#     print(f'{message=}')

# def on_error(ws, error):
#     print(error)

# def on_close(ws, close_status_code, close_msg):
#     print(f"### closed {close_status_code=} {close_msg=}###")

# def on_open(ws):
#     print("Opened connection")

# if __name__ == "__main__":
#     # websocket.enableTrace(True)
#     ws = websocket.WebSocketApp("ws://localhost:8080/websocket_api/ws/123",
#                               on_open=on_open,
#                               on_message=on_message,
#                               on_error=on_error,
#                               on_close=on_close)

#     ws.run_forever()  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    # rel.signal(2, rel.abort)  # Keyboard Interrupt
    # rel.dispatch()