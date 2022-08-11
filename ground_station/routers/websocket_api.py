from fastapi import APIRouter
from starlette.websockets import WebSocket

router = APIRouter(prefix="/websocket_api", tags=["WebSocket"])


@router.websocket("/ws/{client_id}", name='ws')
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
