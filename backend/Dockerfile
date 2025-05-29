# Dockerfile for backend
FROM python:3.9-slim

# Install netcat (nc) for the wait script in docker-compose
# Also install curl for the backend healthcheck
RUN apt-get update && apt-get install -y netcat-openbsd curl postgresql-client dos2unix && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
