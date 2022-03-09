# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

#FROM python:3-windowsservercore

WORKDIR /app

COPY requirements.txt requirements.txt
COPY . .
RUN pip3 install -r requirements.txt

ENV port 8080
EXPOSE ${PORT}

ENTRYPOINT ["python3", "-m" , "src", "run", "--host=0.0.0.0"]

#CMD [ "python3", "-m" , "src", "run", "--host=0.0.0.0"]
