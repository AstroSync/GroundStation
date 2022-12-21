# from threading import Thread
# import time
from __future__ import annotations
from ssl import SSLError
from uuid import UUID
from websocket import create_connection
from websocket import WebSocket


# class Singleton(type):
#     _instances: dict = {}

#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
#         return cls._instances[cls]

host = 'api.astrosync.ru'
# host = '10.6.1.97:8080'
class WebSocketClient():
    ws : WebSocket | None = None
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        print(f'create ws client for {self.user_id} user')
        try:
            self.ws = create_connection(f"wss://{host}/websocket_api/ws/NSU_GS/{self.user_id}")
        except TimeoutError as err:
            print(err)
    def send(self, payload):
        if self.ws is not None:
            try:
                if not self.ws.connected:
                    print(f'create ws client for {self.user_id} user')
                    self.ws = create_connection(f"wss://{host}/websocket_api/ws/NSU_GS/{self.user_id}")
                try:
                    self.ws.send(payload)
                except BrokenPipeError as err:
                    print('websocket client broken pipe\n')
                    print(err)
                    self.resend(payload)
            except SSLError as err:
                print('ws has ssl error!')
                print(err)
                self.resend(payload)
        else:
            print('ws is not connected and can not send msg')

    def close(self):
        if self.ws is not None:
            return self.ws.close()

    def resend(self, payload):
        self.close()
        self.ws = create_connection(f"wss://{host}/websocket_api/ws/NSU_GS/{self.user_id}")
        self.ws.send(payload)



# def send_data() -> None:
#     try:
#         while True:
#             time.sleep(0.1)
#             data = input('>')
#             ws.send(data)
#     except (KeyboardInterrupt, EOFError):
#         return

# thread: Thread = Thread(target=send_data, daemon=True)
# thread.start()

# try:
#     while True:
#         result =  ws.recv()
#         print(f"Received: {result}")
# except KeyboardInterrupt:
#     print('\nShutdown client')
#     ws.close()
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
#     client = WebSocketClient(UUID('f2bc9fb1-e6dd-4bd3-8fd6-9f03e1664f19'))
#     client.send('dfgfdgg')
#     try:
#         while(True):
#             print(client.ws.recv())
#             pass

#     except KeyboardInterrupt:
#         print('Shutdown radio driver')
    # websocket.enableTrace(True)
    # ws = websocket.WebSocketApp("ws://localhost:8080/websocket_api/ws/123",
    #                           on_open=on_open,
    #                           on_message=on_message,
    #                           on_error=on_error,
                            #   on_close=on_close)

#     ws.run_forever()  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    # rel.signal(2, rel.abort)  # Keyboard Interrupt
    # rel.dispatch()