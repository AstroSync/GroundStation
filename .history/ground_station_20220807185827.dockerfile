FROM python:3.9

#
WORKDIR /ground_station

# COPY ./ground_station /ground_station/ground_station

# COPY ./pyproject.toml /ground_station
# COPY ./poetry.lock /ground_station
VOLUME . /ground_station

RUN pip install poetry
RUN poetry export -f requirements.txt --output requirements.txt
RUN pip install -r requirements.txt
# RUN pip install --no-cache-dir --upgrade -r /GS_backend/requirements.txt

CMD poetry run uvicorn ground_station.main:app --proxy-headers --host 0.0.0.0 --port 80
#CMD ["python", "-m", "GS_backend"]
