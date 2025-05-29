# Dockerfile for e2e_tests service
FROM python:3.9-slim

# Install netcat for potential wait scripts (though Python-based polling is preferred)
# Install postgresql-client if direct DB interaction is ever needed for complex cleanup,
# otherwise, it can be removed if all interactions are via API.
RUN apt-get update && apt-get install -y netcat-openbsd postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all python files from the e2e_tests directory
COPY ./*.py ./

# The command to run tests will be specified in docker-compose.yml
