from ground_station.main import celery_app
argv = [
    'worker',
    '--loglevel=INFO',
    '--hostname=NSU'
]
celery_app.worker_main(argv)
