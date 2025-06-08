const ApiClient = require('./generated/generated-client');
const fs = require('fs');
const path = require('path');

function createApiClient() {
    const client = new ApiClient.ApiClient();
    client.basePath = process.env.NOCODB_BASE_URL || 'http://localhost:8082';

    const tokenPath = path.join(__dirname, 'generated', 'token.txt');
    let token = '';
    if (fs.existsSync(tokenPath)) {
        token = fs.readFileSync(tokenPath, 'utf8').trim();
    } else {
        console.error('Token file not found for tests:', tokenPath);
        // Potentially throw an error or handle as needed if token is critical for all tests
    }

    client.defaultHeaders = {
        'xc-token': token,
    };
    return client;
}

module.exports = {
    createApiClient,
};
