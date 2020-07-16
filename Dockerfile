
FROM python:3.7.8-alpine3.12

COPY . /

RUN pip install -r requirements.txt

ENTRYPOINT ["/entrypoint.sh"]
