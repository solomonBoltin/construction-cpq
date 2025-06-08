FROM node:24-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all test files and helpers
COPY main.js ./
COPY test-runner.js ./
COPY test-helpers.js ./
COPY tests/ ./tests/

# Set the command to run the API client
# CMD ["npm install ./generated/generated-client && node main.js"]

# Default command (can be overridden in docker-compose)
CMD ["sh", "-c", "while true; do sleep 1000; done"]
