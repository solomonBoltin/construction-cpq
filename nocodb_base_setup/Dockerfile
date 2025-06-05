FROM node:24-alpine

# Install Java runtime for OpenAPI Generator CLI
RUN apk add --no-cache openjdk11-jre

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install

COPY setup_auto.js .

CMD ["node", "setup_auto.js"]
