from __future__ import annotations
import sys
from celery import Celery
from ground_station import celery_config

print('Created celery app')


host = '10.6.1.74' # 'localhost'
if sys.platform.startswith('win'):
    celery_app: Celery = Celery('ground_station', broker=f'amqp://guest:guest@{host}:5672//',
                                # backend="redis://localhost:6379/0",
                                # backend='mongodb://root:rootpassword@astrosync.ru:27017/?authMechanism=DEFAULT',
                                backend=f'mongodb://root:rootpassword@{host}:27017/?authMechanism=DEFAULT',
                                # backend = 'db+postgresql+psycopg2://testkeycloakuser:testkeycloakpassword@postgres/testkeycloakdb',
                                include=['ground_station.celery_tasks'])
else:  # docker
    celery_app = Celery('celery_worker', broker='amqp://guest:guest@localhost:5672//',
                                # backend="redis://redis:6379/0",
                                # backend='mongodb://root:rootpassword@astrosync.ru:27017/?authMechanism=DEFAULT',
                                backend='mongodb://root:rootpassword@localhost:27017/?authMechanism=DEFAULT',
                                # backend = 'db+postgresql+psycopg2://testkeycloakuser:testkeycloakpassword@postgres/testkeycloakdb',
                                include=['ground_station.celery_tasks'])
celery_app.config_from_object(celery_config)
celery_app.send_task('ground_station.celery_tasks.init_devices', ignore_result=True).get()

# celery -A ground_station.celery_worker worker --loglevel=INFO --hostname=NSU@%h
# celery -A ground_station.celery_worker flower --persistent=True --broker_api=http://guest:guest@rabbitmq:15672/api --basic_auth=user:pass
# celery -A ground_station.celery_worker flower --persistent=True --broker_api=http://guest:guest@rabbitmq:15672/api/ --basic_auth=user:pass --tasks_columns=name,uuid,state,result,received,eta,started,runtime,worker
if __name__ == '__main__':
    celery_app.start()