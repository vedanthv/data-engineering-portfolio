FROM python:3.10-slim

WORKDIR /app

COPY producer.py .

RUN pip install --no-cache-dir kafka-python requests

CMD ["python3", "producer.py"]