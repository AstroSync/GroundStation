FROM python:3.10

#
WORKDIR /ground_station

COPY ./ground_station /ground_station/ground_station

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false
COPY ./pyproject.toml /ground_station
COPY ./poetry.lock /ground_station
RUN poetry install --no-root
# RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
# COPY ./requirements.txt /ground_station
# RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD uvicorn ground_station.main:app --proxy-headers --host 0.0.0.0 --port 80
