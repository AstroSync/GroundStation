import datetime
# from hashlib import _Hash, sha1
from typing import Any, Union
from uuid import UUID, uuid4
from pydantic import BaseModel


class UserDataModel(BaseModel):
    _id: UUID
    satellites: list[str]
    scripts: list[UUID]
    waiting_sessions: list[UUID]
    passed_sessions: list[UUID]
    priority: int


class UserScriptModel(BaseModel):
    _id: UUID = uuid4()
    user_id: UUID
    username: str
    script_name: str
    description: str = ''
    content: bytes
    upload_date: datetime.datetime
    last_edited_date: datetime.datetime
    size: int
    sha256: Any


class DbTaskModel(BaseModel):
    _id: UUID
    user_id: UUID
    username: str
    script_id: UUID | None
    priority: int
    sat_name: str
    registration_time: datetime.datetime
    start: datetime.datetime
    duration_sec: int
    initial_start: datetime.datetime
    initial_duration_sec: int
    parts: int
    station: str
    status: str
    result: str
    traceback: str


class SessionModel(BaseModel):
    start_time: datetime.datetime
    finish_time: datetime.datetime
    available_sec: int  # duration
    busy_sec: int
    station: str
    script_id: UUID
    priority: int


class RegisterSessionModel(BaseModel):
    user_id: UUID
    username: str
    sat_name: str
    session_list: list[SessionModel]


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
    boundary_start: float = -175
    boundary_end: float = 515
    limits: bool = True
    # calibration: float


class RotatorModel(BaseModel):
    az: RotatorAxis
    el: RotatorAxis = {'position': 0, 'speed': 2, 'acceleration': 1,
                       'boundary_start': -90, 'boundary_end': 270, 'limits': True}  # type: ignore


# if __name__ == '__main__':
#     m = TaskModel()
#     print(m)