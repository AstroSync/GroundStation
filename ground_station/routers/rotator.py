import random
import time

from fastapi import APIRouter

from ground_station.hardware.naku_device_api import NAKU
from ground_station.models.api import RotatorModel
# from ground_station.models.api import RotatorModel


router = APIRouter(prefix="/rotator", tags=["Rotator"])


@router.post("/set_config")
async def rotator_config(rotator_model: RotatorModel):
    NAKU().rotator.set_config(rotator_model.dict())
    return {"message": "OK"}


@router.post("/set_angle")
async def set_angle(az: float, el: float):
    NAKU().rotator.set_angle(az, el)
    return {"message": 'OK'}


@router.post("/set_random_angle")
async def set_random_angle():
    az, el = random.uniform(0, 180), random.uniform(-90, 90)
    NAKU().rotator.set_angle(az, el)
    return {"az": f'{az:.2f}', 'el': f'{el:.2f}'}


@router.post("/set_speed")
async def set_speed(az_speed: float, el_speed: float):
    NAKU().rotator.set_speed(az_speed, el_speed)
    return {"message": 'OK'}


@router.get("/")
async def get_position():
    position: tuple[float, float] = NAKU().rotator.current_position  # type: ignore
    print(position)
    return {"az": position[0], "el": position[1]}


@router.get("/condition")
async def get_condition():
    return NAKU().rotator.rotator_model.__dict__


@router.get("/update_condition")
async def update_condition():
    NAKU().rotator.queue_request_condition()
    time.sleep(1.5)
    return NAKU().rotator.rotator_model.__dict__

