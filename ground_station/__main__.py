import uvicorn
from ground_station.main import app

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)  # 192.168.31.30
