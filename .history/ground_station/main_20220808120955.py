from __future__ import annotations
import ast
import asyncio
import os
import uvicorn
import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ground_station.hardware.naku_device_api import device
from ground_station.routers import basic, websocket_api, schedule, radio, rotator

device.connect(tx_port_or_serial_id=f'{os.environ.get("TX_PORT", "6")}',
               rx_port_or_serial_id=f'{os.environ.get("RX_PORT", "A50285BIA")}',
               radio_port_or_serial_id=f'{os.environ.get("RADIO_PORT", "AH06T3YJA")}')
device.start()

device.rotator.print_flag = True

app = FastAPI(title="Ground station API")
app.include_router(rotator.router)
app.include_router(radio.router)
app.include_router(schedule.router)
app.include_router(websocket_api.router)
app.include_router(basic.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://astrosync.ru", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def request_sessions() -> str:
    """Request all pending sessions from the server .

    Returns:
        str: [description]
    """
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.astrosync.ru/pending_sessions') as resp:  # FIXME: use .env
            result = await resp.text()
    return result


async def init_loop():
    """
    Waiting while main server start
    """
    result = None
    while result is None:
        result = await request_sessions()
        if result:
            break
        await asyncio.sleep(5)
    print(f'There is {len(ast.literal_eval(result))} pending sessions')

# asyncio.run(init_loop())

# uvicorn GS_backend.__main__:app --proxy-headers --host 0.0.0.0 --port 8080

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=80)  # 192.168.31.30
