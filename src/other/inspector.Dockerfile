FROM python:3.10.5-slim-buster

ENV PYTHONUNBUFFERED 1

COPY reqs/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "-u", "inspector.py"]
