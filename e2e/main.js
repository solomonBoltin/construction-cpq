// main.js
const fs = require('fs');

const ApiClient = require('./generated/generated-client');


// Configure the client
const client = new ApiClient.ApiClient();
// Use the NOCODB_BASE_URL environment variable or default to localhost
client.basePath = process.env.NOCODB_BASE_URL || 'http://localhost:8082';

// If authentication is needed
// set xc-token to YkwakgPOIY1gF4pFTavpCyqtqQL_xcZ_qBYSR7WA

// get token from ./generated/token.txt 

const tokenPath = './generated/token.txt';
let token = '';
if (fs.existsSync(tokenPath)) {
  token = fs.readFileSync(tokenPath, 'utf8').trim();
    console.log('Token loaded successfully:', token);
} else {
  console.error('Token file not found:', tokenPath);
  process.exit(1);
}



client.defaultHeaders = {
  'xc-token': token,
};

// Use the API
const api = new ApiClient.ProductApi(client);

async function main() {
  try {
    const result = await api.productCount();

    console.log('API Response:', result);
  } catch (error) {
    console.error('API Error:', error);
  }
}

main();