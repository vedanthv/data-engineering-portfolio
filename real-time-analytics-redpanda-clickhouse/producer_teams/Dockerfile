FROM python:3.10-slim

WORKDIR /app

COPY producer_teams.py .

RUN pip install --no-cache-dir kafka-python requests

CMD ["python3", "producer_teams.py"]
