FROM python:3.11.2-slim
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY src src
EXPOSE 5000

ENV PYTHONPATH "${PYTHONPATH}:/src"