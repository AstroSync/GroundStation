from fastapi import APIRouter
from starlette.websockets import WebSocket

router = APIRouter(prefix="/websocket_api", tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    print(f'{client_id=}')
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
