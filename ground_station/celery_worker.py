from __future__ import annotations
from datetime import datetime
import json
import sys
from celery import Celery
from kombu import serialization
# from ground_station import celery_tasks
from ground_station import celery_config
from ground_station.hardware.rotator.rotator_models import RotatorModel


def encoder(obj) -> str | dict:
    if isinstance(obj, datetime):
        return obj.isoformat()
    print(type(obj), obj)
    return obj.__dict__

def decoder(obj):
    if isinstance(obj, dict):
        if 'azimuth' in obj:
            return RotatorModel(**obj)
    return obj

def my_dumps(obj):
    return json.dumps(obj, default=encoder)

def my_loads(obj) -> dict:
    return json.loads(str(obj).replace('\'', '\"'), object_hook=decoder)

print('Created celery app')

serialization.register(
    'custom_json',
    my_dumps,
    my_loads,
    content_type='application/x-json',
    content_encoding='utf-8',
)
host = '10.6.1.74' # 'localhost'
if sys.platform.startswith('win'):
    celery_app: Celery = Celery('ground_station', broker=f'amqp://guest:guest@{host}:5672//',
                                # backend="redis://localhost:6379/0",
                                # backend='mongodb://root:rootpassword@astrosync.ru:27017/?authMechanism=DEFAULT',
                                backend=f'mongodb://root:rootpassword@{host}:27017/?authMechanism=DEFAULT',
                                # backend = 'db+postgresql+psycopg2://testkeycloakuser:testkeycloakpassword@postgres/testkeycloakdb',
                                include=['ground_station.celery_tasks'])
else:  # docker
    celery_app = Celery('celery_worker', broker='amqp://guest:guest@rabbitmq:5672//',
                                # backend="redis://redis:6379/0",
                                # backend='mongodb://root:rootpassword@astrosync.ru:27017/?authMechanism=DEFAULT',
                                backend='mongodb://root:rootpassword@mongodb:27017/?authMechanism=DEFAULT',
                                # backend = 'db+postgresql+psycopg2://testkeycloakuser:testkeycloakpassword@postgres/testkeycloakdb',
                                include=['ground_station.celery_tasks'])
celery_app.config_from_object(celery_config)


# celery -A ground_station.celery_worker worker --loglevel=INFO --hostname=NSU@%h
# celery -A ground_station.celery_worker flower --persistent=True --broker_api=http://guest:guest@rabbitmq:15672/api --basic_auth=user:pass
# celery -A ground_station.celery_worker flower --persistent=True --broker_api=http://guest:guest@rabbitmq:15672/api/ --basic_auth=user:pass --tasks_columns=name,uuid,state,result,received,eta,started,runtime,worker
if __name__ == '__main__':
    celery_app.start()