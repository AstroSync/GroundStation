from apscheduler.job import Job
from fastapi import APIRouter

from ground_station.database_api import pending_collection, completed_collection, failed_collection
from ground_station.hardware.naku_device_api import device
from ground_station.models import RegisterSessionModel

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.get('/')
async def get_schedule() -> list[Job]:
    return device.scheduler.get_jobs()


@router.post('/add_task')
async def add_task(data: RegisterSessionModel):
    # Будем предполагать, что конфигурация радия задачется из пользовательского скрипта
    # TODO: добавить возможность конфигурации радио из отдельного файла конфигурации
    data = data.dict()
    sat_name = data['sat_name']
    session_list = data['session_list']
    user_script = data['user_script']
    print(sat_name, session_list, user_script)
    # pending_collection.insert_one(task_model.dict())
    for session in session_list:
        device.add_new_session('', data['sat_name'], session['start_time'], session['finish_time'])
    return {"message": "OK"}


@router.get('/get_pending_tasks')
async def get_pending_tasks(user_id: int):
    return [session for session in pending_collection.find({'user_data.userId': user_id}, {"_id": 0})]


@router.get('/get_completed_tasks')
async def get_completed_tasks(user_id: int):
    return [session for session in completed_collection.find({'user_data.userId': user_id}, {"_id": 0})]


@router.get('/get_failed_tasks')
async def get_failed_tasks(user_id: int):
    return [session for session in failed_collection.find({'user_data.userId': user_id}, {"_id": 0})]



