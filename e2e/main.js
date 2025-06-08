// main.js
const fs = require('fs');
const path = require('path'); // Added path module
const ApiClient = require('nocodb-cpq-client');
const { runAllTests } = require('./test-runner'); // Import the test runner


// Configure the client
const client = new ApiClient.ApiClient();
// Use the NOCODB_BASE_URL environment variable or default to localhost
client.basePath = process.env.NOCODB_BASE_URL || 'http://localhost:8082';

// get token from ./generated/token.txt
// Corrected token path to be relative to the e2e directory
const tokenPath = path.join(__dirname, 'generated', 'token.txt');
let token = '';
if (fs.existsSync(tokenPath)) {
  token = fs.readFileSync(tokenPath, 'utf8').trim();
  console.log('Token loaded successfully.'); // Token value removed from log for security
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
    console.log('Running main application logic...');
    const result = await api.productCount();
    console.log('API Response from productCount:', result);
    console.log('Main application logic finished.\n');

    // Run E2E tests after main logic
    await runAllTests();

  } catch (error) {
    console.error('API Error in main logic:', error.message);
    if (error.response && error.response.body) {
        console.error('API Error Response Body:', JSON.stringify(error.response.body, null, 2));
    }
    // Decide if the main process should exit if main logic fails, or still run tests
    // For now, we'll let it proceed to tests unless it's a critical setup error handled by process.exit(1) elsewhere
  }
}

main().catch(error => {
    console.error("Unhandled error in main execution:", error);
    process.exit(1); // Exit if main itself has an unhandled error
});