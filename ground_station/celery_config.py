enable_utc = True
result_extended = True
result_expires = 3600  # sec
# mongodb_backend_settings = {
#     'database': 'celery_db',
#     'taskmeta_collection': 'tasks_collection',
# }
# task_serializer = 'pickle'
# result_serializer = 'pickle'
accept_content = ['application/json', 'application/x-json']
task_serializer = 'json'
# accept_content = ['json']
result_serializer = 'json'
task_track_started = True
# result_extended = True
# task_ignore_result = True
broker_transport_option = {'visibility_timeout': 3600000}
# timezone = 'Asia/Novosibirsk'