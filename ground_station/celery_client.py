from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from ground_station.celery_worker import celery_app
from ground_station.celery_tasks import infinite_task
from celery import group


def register_session(user_id: str, start_time: datetime, finish_time: datetime, script: str = ''):
    soft_time_limit = (finish_time - start_time).seconds + 1
    time_limit = soft_time_limit + 5
    # session = infinite_task.signature((), {'user_id': user_id, 'user_script_id': script}, eta=start_time,
    #                                  soft_time_limit=soft_time_limit,
    #                                  time_limit=time_limit,
    #                                  expires=start_time + timedelta(seconds=1))
    # return group(session, session)()
    # return infinite_task.apply_async(kwargs={'user_id': user_id, 'user_script_id': script},
    #                                  eta=start_time,
    #                                  soft_time_limit=soft_time_limit,
    #                                  time_limit=time_limit,
    #                                  expires=start_time + timedelta(seconds=1))
    return celery_app.send_task('ground_station.celery_tasks.infinite_task',
                                kwargs={'user_id': user_id, 'user_script_id': script},
                                eta=start_time,
                                soft_time_limit=soft_time_limit,
                                time_limit=time_limit)

def shutdown_worker():
    celery_app.control.broadcast('shutdown', destination=['NSU@edf1dbccb956'])



if __name__ == '__main__':
    # result = celery_worker.add.apply_async(kwargs={'user_id':'241841fdgh42gfdg32', 'x':5, 'y':3})

    # time.sleep(1)
    # print(result.get())
    print(type(register_session('fdhhfd4334gfd32123', datetime.now(tz=ZoneInfo('Asia/Novosibirsk')) + timedelta(seconds=2), datetime.now(tz=ZoneInfo('Asia/Novosibirsk')) + timedelta(seconds=5)).get()))

    # shutdown_worker()