FROM python:3.11.0-slim-buster
LABEL authors="Sparkgeo UK"

RUN apt-get update && apt-get install -y \
    build-essential

ADD app/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN pip install botocore

ADD app/*.py /usr/bin/
RUN chmod +x /usr/bin/*.py
