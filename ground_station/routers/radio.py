<<<<<<< HEAD
from typing import Union

from fastapi import APIRouter

from ground_station.hardware.naku_device_api import gs_device
from ground_station.models import LoRaConfig, FSK_Config

router = APIRouter(prefix="/radio", tags=["Radio"])


@router.post("/set_config")
async def radio_config(radio_config: Union[LoRaConfig, FSK_Config]):
    gs_device.radio.set_config(radio_config)
    return {"message": "OK"}


@router.post("/send_msg")
async def send_msg(msg: Union[list[int], bytes]):
    gs_device.radio.send(msg)
    return {"message": "OK"}


@router.get("/dump_registers")
async def dump_registers():
    return gs_device.radio.dump_memory()
=======
from typing import Union

from fastapi import APIRouter

from ground_station.hardware.naku_device_api import gs_device
from ground_station.models import LoRaConfig, FSK_Config

router = APIRouter(prefix="/radio", tags=["Radio"])


@router.post("/set_config")
async def radio_config(radio_config: Union[LoRaConfig, FSK_Config]):
    gs_device.radio.set_config(radio_config)
    return {"message": "OK"}


@router.post("/send_msg")
async def send_msg(msg: Union[list[int], bytes]):
    gs_device.radio.send(msg)
    return {"message": "OK"}


@router.get("/dump_registers")
async def dump_registers():
    return gs_device.radio.dump_memory()
