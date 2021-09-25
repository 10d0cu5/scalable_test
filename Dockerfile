FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

COPY requirements.txt /requirements.txt

RUN apt-get update
RUN pip install --no-cache-dir -r /requirements.txt

COPY ./app /app/app