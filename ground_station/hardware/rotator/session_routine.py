import time
from datetime import datetime
from pytz import utc
from ground_station.hardware.rotator.rotator_driver import RotatorDriver
from ground_station.propagator.propagate import SatellitePath


def session_routine(path_points: SatellitePath, rotator: RotatorDriver) -> None:
    print(f'Start rotator session routine:\n{path_points.__repr__}')
    normal_speed: int = 4
    fast_speed: int = 6
    az_step: float = 0.15
    az_trim_angle: float = az_step * path_points.az_rotation_direction
    rotator.set_speed(fast_speed, fast_speed)
    # prepare rotator position
    rotator.set_angle(path_points.azimuth[0], path_points.altitude[0])
    if path_points.azimuth[-1] > 360:
        rotator.set_boundary_maximum_angle('1', path_points.azimuth[-1] + 1)
    elif path_points.azimuth[-1] < 0:
        rotator.set_boundary_minimum_angle('1', path_points.azimuth[-1] - 1)

    if path_points.t_points[0].tzinfo is None:
        path_points.t_points = [t.astimezone(utc) for t in path_points.t_points]

    while datetime.now().astimezone(utc) < path_points.t_points[0]:  # waiting for start session
        time.sleep(1)
        print(f'start time wating: {(path_points.t_points[0] - datetime.now().astimezone(utc)).seconds}')
    while rotator.rotator_model.azimuth.speed is None:
        rotator.set_speed(normal_speed, normal_speed)
        time.sleep(0.2)
    print('start rotator session routine')
    point_count: int = len(path_points.t_points)
    for i, (altitude, azimuth, time_point) in enumerate(path_points):
        print(f'next point: ({azimuth:.2f}, {altitude:.2f})\tstep {i}/{point_count}')
        i+=1
        # if NAKU().rotator.rotator_model.azimuth.speed > normal_speed:
        #     NAKU().rotator.set_speed(normal_speed, normal_speed)
            # Unsupported operand types for > ("datetime" and "timedelta")
        if abs(datetime.now().astimezone(utc) - time_point.astimezone(utc)).seconds > 1.5:
            print(f'skip point: {datetime.now().astimezone(utc), time_point}')
            continue
        if datetime.now().astimezone(utc) < time_point:
            while datetime.now().astimezone(utc) < time_point:  # waiting for next point
                time.sleep(0.01)
        rotator.set_angle(azimuth + az_trim_angle, altitude)

        current_pos = rotator.current_position
        if current_pos is not None:
            az_diff: float = current_pos[0] - azimuth
            el_diff: float = current_pos[1] - altitude
            # if abs(az_diff) > 3:
            #     NAKU().rotator.set_speed(fast_speed, fast_speed)
            # elif abs(az_diff) < 2:
            #     NAKU().rotator.set_speed(normal_speed, normal_speed)
            if 0 < az_diff < 1:
                az_step = 0.15
            elif 0 < az_diff < 2:
                az_step = 1
            elif 0 < az_diff < 3:
                az_step = 2
            elif 0 > az_diff > -1:
                az_step = 0.15
            elif 0 > az_diff > -2:
                az_step = 0.05
            elif 0 > az_diff > -3:
                az_step = 0.02
            # print(f'current pos: {device.rotator.current_position} target pos: {azimuth:.2f}, {altitude:.2f}')
            print(f'Az,El diff: ({az_diff:.2f}, {el_diff:.2f}) '  # type: ignore
                  f'current pos: ({current_pos[0]:.2f}, {current_pos[1]:.2f})')  # type: ignore
