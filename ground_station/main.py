from __future__ import annotations
import asyncio
import os
import uvicorn
import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ground_station.hardware.naku_device_api import device
from ground_station.routers import basic, websocket_api, schedule, radio, rotator

device.connect(tx_port=f'{os.environ.get("TX_PORT", "COM46")}',
               rx_port=f'{os.environ.get("RX_PORT", "COM36")}',
               radio_port=f'{os.environ.get("RADIO_PORT", "COM3")}')
# device.start()
device.rotator.print_flag = True

app = FastAPI(title="Ground station API")
app.include_router(rotator.router)
app.include_router(radio.router)
app.include_router(schedule.router)
app.include_router(websocket_api.router)
app.include_router(basic.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "https://hirundo.ru", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def request_sessions():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.astrosync.ru/pending_sessions') as resp:
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
    print(f'There is {len(eval(result))} pending sessions')

# asyncio.run(init_loop())
#uvicorn GS_backend.__main__:app --proxy-headers --host 0.0.0.0 --port 8080


def main():
    # Popen(['python', '-m', 'https_redirect'])
    uvicorn.run(app, host="localhost", port=8080)  # 192.168.31.30


if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8080)  # 192.168.31.30