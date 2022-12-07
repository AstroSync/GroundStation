
#!/usr/bin/python

from websocket import create_connection
ws = create_connection("ws://localhost:8080/websocket_api/ws")
print("Sending 'Hello, World'...")
ws.send("Hello, World")
print("Sent")
print("Receiving...")
result =  ws.recv()
print(f"Received {result}")
ws.close()