from __future__ import annotations
from fastapi import APIRouter
from ground_station.hardware.naku_device_api import NAKU
from ground_station.models.db import LoRaConfig, FSK_Config

router = APIRouter(prefix="/radio", tags=["Radio"])


@router.post("/set_config")
async def radio_config(config: LoRaConfig | FSK_Config):
    #gs_device.radio.set_config(radio_config)
    return {"message": "OK"}


@router.post("/send_msg")
async def send_msg(msg: list[int] | bytes):
    NAKU().radio.send_single(msg)
    return {"message": "OK"}


# @router.get("/dump_registers")
# async def dump_registers():
#     return gs_device.radio.dump_memory()
