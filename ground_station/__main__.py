from ground_station.main import app
argv = [
    'worker',
    '--loglevel=INFO',
    '--hostname=NSU'
]
app.worker_main(argv)
