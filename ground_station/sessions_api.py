from datetime import datetime
from uuid import UUID
from ground_station.models import DbTaskModel, RegisterSessionModel
from ground_station.sessions_store.sessions_store import TimeRanges_store

def register_sessions(new_sessions: RegisterSessionModel):
    """
    Данные приходят от фронта.
    *подразумевается, что пользователь авторизирован, а скрипты проверены линтером и находятся в БД
    1) сконвертировать RegisterSessionModel в лист DbTaskModel
    2) обновить расписание, сделав merge сессий
    3) зарегистрировать сессии в БД и отправить исполняться в celery
    """
    tasks: list[DbTaskModel] = [DbTaskModel(user_id=new_sessions.user_id,
                                            username=new_sessions.username,
                                            script_id=session.script_id,
                                            priority=session.priority,
                                            sat_name=new_sessions.sat_name,
                                            registration_time=datetime.now(),
                                            start_time=session.start_time,
                                            duration_sec=session.available_sec,
                                            station=session.station,
                                            status='WAITING')
                                for session in new_sessions.session_list]
    TimeRanges_store.append()

def cancel_sessions(sessions_id_list: list[UUID]):
    pass

def set_session_priority(priority: int):
    pass

def set_session_script(script_id: UUID):
    pass

def remove_script(script_id: UUID):
    pass

def get_user_scripts(user_id: UUID) -> list:
    return []

def get_user_sessions(user_id: UUID) -> list:
    return []

def get_my_satellites(user_id: UUID) -> list:
    return []
