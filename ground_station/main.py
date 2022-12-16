from __future__ import annotations
from celery import Celery
from ground_station import celery_config

print('Created celery app')


host = '10.6.1.74' # 'localhost'
app: Celery = Celery('ground_station',
                     broker=f'redis://{host}:6379/0',
                    #  broker=f'amqp://guest:guest@{host}:5672//',

                     backend=f"redis://{host}:6379/0",
                            # backend='mongodb://root:rootpassword@astrosync.ru:27017/?authMechanism=DEFAULT',
                            # backend = 'db+postgresql+psycopg2://testkeycloakuser:testkeycloakpassword@postgres/testkeycloakdb',
                            include=['ground_station.celery_tasks'])
app.config_from_object(celery_config)
# app.send_task('ground_station.celery_tasks.init_devices', ignore_result=True, countdown=2).get()
if __name__ == "__main__":
    argv = [
        'worker',
        '--loglevel=INFO',
        '--hostname=NSU',
        '--concurrency=1'
    ]
    app.worker_main(argv)
# celery -A ground_station.celery_worker worker --loglevel=INFO --hostname=NSU@%h
# celery -A ground_station.celery_worker flower --persistent=True --broker_api=http://guest:guest@rabbitmq:15672/api --basic_auth=user:pass
# celery -A ground_station.main flower --persistent=True --broker_api=http://guest:guest@rabbitmq:15672/api/ --tasks_columns=name,uuid,state,result,received,eta,started,runtime,worker

# <bound method SatellitePath.__repr__ of Altitude deg from 3.00 to 2.94
# Azimuth deg from 252.67 to 308.60
# Distance km from 2147.83 to 2392.31
# Altitude rate deg/s from -0.03 to 0.03
# Azimuth rate deg/s from 0.17 to 0.21
# Distance rate km/s from -2.99 to 3.09
# Time points: from 2022-12-15 09:36:01.726000+00:00 to 2022-12-15 09:40:53.726000+00:00.
# Duration: 292 sec
# >