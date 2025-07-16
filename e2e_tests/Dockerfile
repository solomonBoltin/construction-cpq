# Dockerfile for e2e_tests service
FROM python:3.9-slim

# Install netcat for potential wait scripts (though Python-based polling is preferred)
# Install postgresql-client if direct DB interaction is ever needed for complex cleanup,
# otherwise, it can be removed if all interactions are via API.
RUN apt-get update && apt-get install -y netcat-openbsd postgresql-client && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libgbm-dev \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy all python files from the e2e_tests directory
COPY ./*.py ./

# Create screenshots directory
RUN mkdir -p /app/screenshots

# The command to run tests will be specified in docker-compose.yml
