FROM python:3.9

# 
WORKDIR /GS_backend
COPY ./GS_backend /GS_backend
RUN pip install --no-cache-dir --upgrade -r /GS_backend/requirements.txt
RUN pip install 'uvicorn[standard]'
WORKDIR /
CMD ["uvicorn", "GS_backend.__main__:app", "--proxy-headers", "--host", "0.0.0.0", "--port" "8080"]
#CMD ["python", "-m", "GS_backend"]
