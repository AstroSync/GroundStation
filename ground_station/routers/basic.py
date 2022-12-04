from __future__ import annotations
import hashlib

import os
from datetime import date, datetime
from tempfile import NamedTemporaryFile
from typing import Any, Union
from io import BytesIO, StringIO
from uuid import UUID  #, uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile  # , UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse  #, RedirectResponse,
from fastapi_keycloak import OIDCUser  #, UsernamePassword
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from ground_station.models.api import RegisterSessionModel
#from ground_station.database_api import db_add_user_script, db_register_new_session, get_all_sessions
# from ground_station.hardware.naku_device_api import device
from ground_station.models.db import UserScriptModel
from ground_station.propagator.celestrak_api import get_sat_name_and_num
from ground_station.propagator.propagate import OBSERVERS, get_sessions_for_sat
from ground_station.sessions_store.scripts_store import script_store
from ground_station.keycloak import idp

router = APIRouter(tags=["Main"])
sat_names = get_sat_name_and_num(os.path.join(os.path.dirname(__file__), "../propagator/active.json"))


@router.get("/user")
async def root_user(user: OIDCUser = Depends(idp.get_current_user())):
    return {"message": user.dict()}


@router.get("/app")
async def root():
    return {"message": "OK"}


@router.get("/satellites")
async def satellites():
    print('return satellite list')
    return JSONResponse(content=sat_names)


@router.post("/register_new_session")
async def register_new_session(request_body: RegisterSessionModel):
    #db_register_new_session(request_body.dict())
    print(request_body)
    return 'OK'


def pylint_check(path: str) -> tuple[int, int, str]:
    pylint_output: StringIO = StringIO()  # Custom open stream
    reporter: TextReporter = TextReporter(pylint_output)
    results: Run = Run(['--disable=missing-module-docstring', f'{path}'],
                  reporter=reporter, exit=False)
    errors: int = results.linter.stats.error
    fatal: int = results.linter.stats.fatal
    return errors, fatal, pylint_output.getvalue()


@router.post("/save_script")
async def save_script(user_id: UUID, user_script: UploadFile, script_name: str, description: str = ''):
    contents: bytes = await user_script.read()

    file_copy = NamedTemporaryFile(delete=False)
    file_copy.write(contents)  # copy the received file data into a new temp file.
    file_copy.seek(0)  # move to the beginning of the file

    errors, fatal, details = pylint_check(f'{file_copy.name}')
    if not errors:
        print('SCRIPT OK')
        now: datetime = datetime.now().astimezone()
        sha256: str = hashlib.sha256(contents).hexdigest()
        scriptModel=UserScriptModel(user_id=user_id, username='username', script_name=script_name, description=description,
                        content=contents, upload_date=now, last_edited_date=now, size=len(contents), sha256=sha256)
        script_store.save_script(scriptModel)
    else:
        print(f'{errors=}')
    # os.remove(f'{prefix}_{user_script.filename}')
    file_copy.close()  # Remember to close any file instances before removing the temp file
    os.unlink(file_copy.name)  # unlink (remove) the file
    #db_add_user_script(UserScriptModel(user_id=user_id, script_name=script_name, content=contents))
    return {"result": details, "errors": errors, "fatal": fatal}


@router.get("/download_script")
async def download_script(script_id: UUID) -> StreamingResponse:
    model: UserScriptModel | None = script_store.download_script(script_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return StreamingResponse(BytesIO(model.content))


@router.get("/sessions")
async def sessions(sat_name: str, start_date: Union[date, str] = date.today(),
                   end_date: Union[date, str] = date.today()):
    print(f'sat_name: {sat_name}, start_date: {start_date}, end_date: {end_date}')
    session_list: list[dict[str, Any]] = get_sessions_for_sat(sat_name=sat_name, observers=OBSERVERS,
                                                              t_1=start_date, t_2=end_date)
    if session_list == ValueError:
        raise HTTPException(status_code=404, detail="Satellite name was not found.")
    return JSONResponse(content=session_list)


@router.get("/{path:path}")
async def root_path(path: str):
    print(f'basic router catch path:{path}')
    return {"message": path}


SCRIPT = """
import time
print('Running user script')
for i in range(50):
    time.sleep(0.1
    print(f'some processing {i}')
print('User script completed')
"""
if __name__ == "__main__":
    f = lambda: exec(compile(SCRIPT, "<string>", "exec"))
    f()
# frontend_server = True
#
#
# @router.get("/", response_class=HTMLResponse)
# @router.get("/{path:path}")
# async def catch_all(request: Request, path: str):
#     print(f'path_name: {path}')
#     if frontend_server:
#         if path == '':
#             return HTMLResponse(requests.get(f'http://localhost:8000/{path}').content)
#         else:
#             return HTMLResponse(requests.get(f'http://localhost:8000/{path}').content)
# return FileResponse(f'{dist_path}/{path.lstrip("/")}')
