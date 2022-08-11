from __future__ import annotations

import os
from datetime import date
# from tempfile import NamedTemporaryFile
from typing import Union
from anyio import Any

from fastapi import APIRouter, HTTPException  # , UploadFile, File
from fastapi.responses import JSONResponse
# from pylint.lint import Run
# from pylint.reporters.text import TextReporter
# from io import StringIO
from ground_station.database_api import db_register_new_session, get_all_sessions
# from ground_station.hardware.naku_device_api import device
from ground_station.models import RegisterSessionModel
from ground_station.propagator.celestrak_api import get_sat_name_and_num
from ground_station.propagator.propagate import OBSERVERS, get_sessions_for_sat

router = APIRouter(tags=["Main"])
sat_names = get_sat_name_and_num(os.path.join(os.path.dirname(__file__), "../propagator/active.json"))


# @router.get('/favicon.ico', include_in_schema=False)
# async def favicon():
#     return FileResponse(os.path.join(os.path.dirname(__file__), '../../BRK_Controller/assets/satellite.ico'))


# @router.get("/", response_class=HTMLResponse)
# async def root(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


@router.get("/app")
async def root():
    return {"message": "OK"}


@router.get("/satellites")
async def satellites():
    print('return satellite list')
    return JSONResponse(content=sat_names)


@router.post("/register_new_session")
async def register_new_session(request_body: RegisterSessionModel):
    db_register_new_session(request_body.dict())
    print(request_body)
    return 'OK'


@router.get("/pending_sessions")
async def get_pending_sessions():
    sat_sessions = get_all_sessions()
    print(sat_sessions)
    return JSONResponse(content=sat_sessions)


# def pylint_check(path: str):
#     pylint_output = StringIO()  # Custom open stream
#     reporter = TextReporter(pylint_output)
#     results = Run(['--disable=missing-module-docstring', f'{path}'],
#                   reporter=reporter, exit=False)
#     errors = results.linter.stats.error
#     fatal = results.linter.stats.fatal
#     return errors, fatal, pylint_output.getvalue()


# @router.post("/save_script")
# async def create_upload_file(user_script: UploadFile):
#     contents = await user_script.read()
#
#     file_copy = NamedTemporaryFile(delete=False)
#     file_copy.write(contents)  # copy the received file data into a new temp file.
#     file_copy.seek(0)  # move to the beginning of the file
#
#     errors, fatal, details = pylint_check(f'{file_copy.name}')
#     if not errors:
#         print('SCRIPT OK')
#         # TODO: save script in db
#     # os.remove(f'{prefix}_{user_script.filename}')
#     file_copy.close()  # Remember to close any file instances before removing the temp file
#     os.unlink(file_copy.name)  # unlink (remove) the file
#     return {"result": details, "errors": errors, "fatal": fatal}


# @router.post("/register_new_session")
# async def register_new_session(request: Request):
#     form_data = await request.form()
#     if form_data['file'] != 'null':
#         content = await form_data['file'].read()
#         print(content)
#     print(form_data['sat_name'])
#     print(form_data['session_list'])
#     return 'OK'


@router.get("/sessions")
async def sessions(sat_name: str, start_date: Union[date, str] = date.today(),
                   end_date: Union[date, str] = date.today()):
    """_summary_

    Args:
        sat_name (str): _description_
        start_date (Union[date, str], optional): _description_. Defaults to date.today().
        end_date (Union[date, str], optional): _description_. Defaults to date.today().

    Raises:
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    print(f'sat_name: {sat_name}, start_date: {start_date}, end_date: {end_date}')
    session_list: list[dict[str, Any]] = get_sessions_for_sat(sat_name=sat_name, observers=OBSERVERS,
                                                              t_1=start_date, t_2=end_date)
    if session_list == ValueError:
        raise HTTPException(status_code=404, detail="Satellite name was not found.")
    return JSONResponse(content=session_list)


# @router.get("/device")
# async def device_state():
#     device


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
