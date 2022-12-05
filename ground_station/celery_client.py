# from datetime import datetime
from datetime import datetime, timedelta
from celery import group, signature
from ground_station.celery_worker import celery_app
from ground_station.sessions_store.session import Session
# from ground_station.celery_tasks import radio_task, rotator_task_emulation


def celery_register_session(model: Session):
    soft_time_limit: float = model.duration_sec + 3.0
    time_limit: float = soft_time_limit + 8.0

    radio = signature('ground_station.celery_tasks.radio_task', args=(),
                                                   kwargs=model.__dict__,
                                                   eta=model.start,
                                                   soft_time_limit=soft_time_limit,
                                                   time_limit=time_limit)
    rotator = signature('ground_station.celery_tasks.rotator_task_emulation', args=(),
                                                   kwargs=model.__dict__,
                                                   eta=model.start,
                                                   soft_time_limit=soft_time_limit,
                                                   time_limit=time_limit)

    group_task: group = group(radio, rotator)
    return group_task.apply_async()

def connect():
    return celery_app.send_task('ground_station.celery_tasks.connect')

def get_position():
    return celery_app.send_task('ground_station.celery_tasks.get_angle',
                                kwargs={'var1':1, 'var2': 2},
                                soft_time_limit=5,
                                eta=datetime.now().astimezone() + timedelta(seconds=6))

def shutdown_worker():
    celery_app.control.broadcast('shutdown', destination=['NSU'])



if __name__ == '__main__':
    # data = Session(start=datetime.now(), username='Test User', result='0xAB 0x21 0xCD 0x78 0x01')
    # print(data.__dict__)
    # print(register_session(data).get())
    # print(connect())
    # print(Model.parse_obj(get_position().get()))
    get_position()
    # print(celery_app.control.purge())
    # print(celery_app.control.broadcast('purge', destination=['NSU']))
    # while True:

    # celery_app.control.revoke('3343b68e-eae1-408a-a890-5183fb56140d')
# az67 el:49

#az 120api = 127rot; el 51api = 90rot