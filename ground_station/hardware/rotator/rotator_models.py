from typing import Optional


class RotatorAxisModel:
    def __init__(self, **kwargs):
        self.position: float = kwargs.get('position', None)
        self.speed: float = kwargs.get('speed', None)
        self.acceleration: float = kwargs.get('acceleration', None)
        self.min_angle: float = kwargs.get('min_angle', None)
        self.max_angle: float = kwargs.get('max_angle', None)
        self.boundary_start: float = kwargs.get('boundary_start', None)
        self.boundary_end: float = kwargs.get('boundary_end', None)
        self.limits: bool = kwargs.get('limits', None)

    def update(self, pos: Optional[float], speed: Optional[float], accel: float, boundary_start: float,
               boundary_end: float, limits: bool):
        if pos is not None:
            self.position: float = pos
        if speed is not None:
            self.speed: float = speed
        self.acceleration: float = accel
        self.boundary_start: float = boundary_start
        self.boundary_end: float = boundary_end
        self.limits: bool = limits

    def __str__(self):
        return f'Pos: {self.position}\nSpeed: {self.speed}\nAccel: {self.acceleration}\nMin angle: {self.min_angle}\n' \
               f'Max angle: {self.max_angle}\nBoundary start angle: {self.boundary_start}\n' \
               f'Boundary end angle: {self.boundary_end}\nLimits: {self.limits}'


class RotatorModel:
    def __init__(self):
        self.azimuth: RotatorAxisModel = RotatorAxisModel()
        self.elevation: RotatorAxisModel = RotatorAxisModel()

    def __str__(self):
        return f'Azimuth:\n{self.azimuth}\n\nElevation:\n{self.elevation}\n'
