<<<<<<< HEAD
import datetime
from typing import Union
from pydantic import BaseModel


class SessionModel(BaseModel):
    start_time: datetime.datetime
    finish_time: datetime.datetime
    duration_sec: int
    station: str
    status: str


class RegisterSessionModel(BaseModel):
    sat_name: str
    session_list: list[SessionModel]
    user_script: str


class LoRaConfig(BaseModel):
    coding_rate: str
    frequency: float
    bandwidth: str
    spreading_factor: int
    tx_power: int
    sync_word: int
    preamble_length: int
    auto_gain_control: bool
    payload_size: int
    lna_gain: int
    lna_boost: bool
    implicit_mode: bool
    rx_timeout: int


class FSK_Config(BaseModel):
    frequency: float


class UserSatelliteModel(BaseModel):
    userId: int
    user_script: str
    sat_name: str
    radio_config: Union[LoRaConfig, FSK_Config]


class TaskModel(BaseModel):
    # user_data: UserSatelliteModel

    start_time: datetime.datetime
    end_time: datetime.datetime
    # status: str = 'pending'


class RotatorAxis(BaseModel):
    position: float = 0
    speed: float = 2
    acceleration: float = 1
    boundary_start: float = 0
    boundary_end: float = 360
    limits: bool = True
    # calibration: float


class RotatorModel(BaseModel):
    az: RotatorAxis
    el: RotatorAxis = {'position': 0, 'speed': 2, 'acceleration': 1,
                       'boundary_start': -90, 'boundary_end': 270, 'limits': True}  # type: ignore


# if __name__ == '__main__':
#     m = TaskModel()
#     print(m)
=======
import datetime
from typing import Union
from pydantic import BaseModel


class SessionModel(BaseModel):
    start_time: datetime.datetime
    finish_time: datetime.datetime
    duration_sec: int
    station: str
    status: str


class RegisterSessionModel(BaseModel):
    sat_name: str
    session_list: list[SessionModel]
    user_script: str


class LoRaConfig(BaseModel):
    coding_rate: str
    frequency: float
    bandwidth: str
    spreading_factor: int
    tx_power: int
    sync_word: int
    preamble_length: int
    auto_gain_control: bool
    payload_size: int
    lna_gain: int
    lna_boost: bool
    implicit_mode: bool
    rx_timeout: int


class FSK_Config(BaseModel):
    frequency: float


class UserSatelliteModel(BaseModel):
    userId: int
    user_script: str
    sat_name: str
    radio_config: Union[LoRaConfig, FSK_Config]


class TaskModel(BaseModel):
    # user_data: UserSatelliteModel

    start_time: datetime.datetime
    end_time: datetime.datetime
    # status: str = 'pending'


class RotatorAxis(BaseModel):
    position: float = 0
    speed: float = 2
    acceleration: float = 1
    boundary_start: float = 0
    boundary_end: float = 360
    limits: bool = True
    # calibration: float


class RotatorModel(BaseModel):
    az: RotatorAxis
    el: RotatorAxis = {'position': 0, 'speed': 2, 'acceleration': 1,
                       'boundary_start': -90, 'boundary_end': 270, 'limits': True}  # type: ignore


# if __name__ == '__main__':
#     m = TaskModel()
#     print(m)