FROM python:3.7-alpine

RUN apk add libffi-dev gcc musl-dev libressl-dev

RUN pip3 install pefile

COPY 1768.py /

RUN chmod u+x /1768.py

VOLUME ["/data"]

WORKDIR /data

ENTRYPOINT ["/1768.py"]
