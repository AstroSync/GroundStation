import sys
from celery import Celery
# from ground_station import celery_tasks
from ground_station import celery_config


print('Created celery app')

if sys.platform.startswith('win'):
    celery_app = Celery('ground_station', broker='amqp://guest:guest@localhost:5672//',
                                # backend="redis://localhost:6379/0",
                                # backend='mongodb://root:rootpassword@astrosync.ru:27017/?authMechanism=DEFAULT',
                                backend='mongodb://root:rootpassword@localhost:27017/?authMechanism=DEFAULT',
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