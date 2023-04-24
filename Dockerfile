FROM python:3.11.2-slim
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY src src

ENV PYTHONPATH "${PYTHONPATH}:/src"