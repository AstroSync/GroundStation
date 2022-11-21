from uuid import uuid4
from datetime import datetime
from celery import group
from ground_station.celery_worker import celery_app
from ground_station.models import DbTaskModel
# from ground_station.celery_tasks import infinite_task


def register_session(model: DbTaskModel):
    soft_time_limit = model.duration_sec + 1
    time_limit = soft_time_limit + 5
    return group(celery_app.send_task('ground_station.celery_tasks.radio_task',
                                       kwargs={"data": model},
                                       eta=model.start_time,
                                       soft_time_limit=soft_time_limit,
                                       time_limit=time_limit),
                 celery_app.send_task('ground_station.celery_tasks.rotator_task',
                                       kwargs={"data": model},
                                       eta=model.start_time,
                                       soft_time_limit=soft_time_limit,
                                       time_limit=time_limit))()


def shutdown_worker():
    celery_app.control.broadcast('shutdown', destination=['NSU@edf1dbccb956'])



if __name__ == '__main__':
    data = DbTaskModel(user_id=uuid4(), script_id=uuid4(), priority=1, sat_name='NORBI',
                       registration_time=datetime.now(), start_time=datetime.now(), duration_sec=10, username='Test User',
                       station='NSU', status='SUCCESS', result='0xAB 0x21 0xCD 0x78 0x01', traceback='')
    # print(data.__dict__)
    print(register_session(data).get())
