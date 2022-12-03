FROM python:3.10-slim-buster

WORKDIR /app

COPY manager/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY manager/* .

CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]
