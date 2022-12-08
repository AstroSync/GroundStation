from __future__ import annotations
# import sys
import uvicorn
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from ground_station.routers import basic, websocket_api, schedule, radio, rotator

app: FastAPI = FastAPI(title="Ground station API")
app.include_router(rotator.router)
app.include_router(radio.router)
app.include_router(schedule.router)
app.include_router(websocket_api.router)
app.include_router(basic.router)

# idp.add_swagger_config(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# uvicorn GS_backend.__main__:app --proxy-headers --host 0.0.0.0 --port 8080

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)  # 192.168.31.30
# JobEvent (code=1024)>, code: 1024, type: <class 'int'>
# JobSubmissionEvent (code=32768)>, code: 32768, type: <class 'int'
# <JobExecutionEvent (code=4096)>, code: 4096, type: <class 'int'
