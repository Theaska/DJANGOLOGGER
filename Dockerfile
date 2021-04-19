FROM python:3.8-alpine

WORKDIR /app
COPY . /app/

ENV DJANGO_SETTINGS_MODULE=django_logger.settings

RUN apk update && \
    apk add --virtual build-deps gcc musl-dev bash && \
    apk add postgresql-dev postgresql

RUN pip install --upgrade -r requirements.txt

CMD ["python"]
