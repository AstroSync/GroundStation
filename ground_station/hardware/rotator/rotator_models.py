from __future__ import annotations
from pydantic import BaseModel


class RotatorAxisModel(BaseModel):
    position: float = 0
    speed: float = 0
    acceleration: float = 0
    min_angle: float = 0
    max_angle: float = 0
    boundary_start: float = 0
    boundary_end: float = 0
    limits: bool = True

    def __str__(self) -> str:
        return f'Pos: {self.position}\nSpeed: {self.speed}\nAccel: {self.acceleration}\nMin angle: {self.min_angle}\n' \
               f'Max angle: {self.max_angle}\nBoundary start angle: {self.boundary_start}\n' \
               f'Boundary end angle: {self.boundary_end}\nLimits: {self.limits}'


class RotatorModel(BaseModel):
    azimuth: RotatorAxisModel = RotatorAxisModel()
    elevation: RotatorAxisModel = RotatorAxisModel()

