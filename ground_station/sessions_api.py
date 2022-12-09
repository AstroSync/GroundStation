from __future__ import annotations
from datetime import datetime, timedelta
from uuid import UUID  #, uuid4
from ground_station.celery_worker import celery_app
from ground_station.celery_client import celery_register_session
from ground_station.models.api import RegisterSessionModel
from ground_station.sessions_store.session import Session
from ground_station.sessions_store.mongodb_controller import MongoStore

store = MongoStore('10.6.1.74', 'root', 'rootpassword', Session)

def register_sessions(new_sessions: list[RegisterSessionModel]):
    sessions: list[Session] = [Session(**session.dict()) for session in new_sessions]
    store.append(*sessions)
    async_result = celery_register_session(sessions[0])
    return async_result

def cancel_sessions(sessions_id_list: list[UUID]) -> None:
    i = celery_app.control.inspect()
    tasks: list[dict[str, list[dict]]] = i.scheduled()
    # find id in tasks and mark as revoked


def set_session_priority(priority: int) -> None:
    pass

def set_session_script(session_id: UUID, script_id: UUID | None):
    pass

def remove_script(script_id: UUID) -> None:
    pass

def get_user_scripts(user_id: UUID) -> list:
    return []

def get_user_sessions(user_id: UUID) -> list:
    return []

def get_my_satellites(user_id: UUID) -> list:
    return []


if __name__ == '__main__':
    start_time = datetime.now() + timedelta(seconds=6)
    input_data: RegisterSessionModel = RegisterSessionModel(user_id=UUID('388c01db-52a2-4192-9d6e-131958ea9e3a'),
                                                            script_id=UUID('6e867ffa-264f-49a7-a58b-71de451f1c49'),
                                                            username='kek',
                                                            sat_name='NORBI',
                                                            priority=1,
                                                            start=start_time,
                                                            duration_sec=10)
    print(register_sessions([input_data])[0].get())