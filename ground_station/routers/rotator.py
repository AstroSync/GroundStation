import random
import time

from fastapi import APIRouter

from ground_station.hardware.naku_device_api import device
from ground_station.models import RotatorModel

router = APIRouter(prefix="/rotator", tags=["Rotator"])


@router.post("/set_config")
async def rotator_config(rotator_model: RotatorModel):
    device.rotator.set_config(rotator_model.dict())
    return {"message": "OK"}


@router.post("/set_angle")
async def set_angle(az: float, el: float):
    device.rotator.set_angle(az, el)
    return {"message": 'OK'}


@router.post("/set_random_angle")
async def set_random_angle():
    az, el = random.uniform(0, 180), random.uniform(-90, 90)
    device.rotator.set_angle(az, el)
    return {"az": f'{az:.2f}', 'el': f'{el:.2f}'}


@router.post("/set_speed")
async def set_speed(az_speed: float, el_speed: float):
    device.rotator.set_speed(az_speed, el_speed)
    return {"message": 'OK'}


@router.get("/")
async def get_position():
    position = device.rotator.current_position
    print(position)
    return {"az": position[0], "el": position[1]}


@router.get("/condition")
async def get_condition():
    return device.rotator.rotator_model.__dict__


@router.get("/update_condition")
async def update_condition():
    device.rotator.queue_request_condition()
    time.sleep(1.5)
    return device.rotator.rotator_model.__dict__

