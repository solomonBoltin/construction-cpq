FROM node:24-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy main application file
COPY main.js ./

# Set the command to run the API client
# CMD ["npm install ./generated/generated-client && node main.js"]

# cmd to sleep for ever
CMD ["sh", "-c", "while true; do sleep 1000; done"]
