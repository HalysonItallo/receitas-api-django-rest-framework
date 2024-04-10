FROM python:3.12-alpine3.19
LABEL matainer="halyssonpimentell@gmail.com"

# Evita delay na saída das menssagens no console
ENV PYTHONNUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements-dev.txt /tmp/requirements-dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

# TODO: Tentar entender por que só funciona com /py
ARG DEV=false
RUN python -m venv /py && \
  /py/bin/pip install --upgrade pip && \
  /py/bin/pip install -r  /tmp/requirements.txt && \
  if [${DEV} == "true"]; \
  then  /py/bin/pip install -r  /tmp/requirements-dev.txt; \
  fi && \
  rm -rf /tmp && \
  adduser --disabled-password --no-create-home django-user

ENV PATH="/py/bin:$PATH"

USER django-user