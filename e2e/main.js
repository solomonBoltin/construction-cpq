// main.js
const fs = require('fs');
const path = require('path');
// const ApiClient = require('nocodb-cpq-client'); // Old client
const cpqClient = require('./cpq_backend_client'); // New CPQ client
const { runAllTests } = require('./test-runner');

// Configure the client - This section might be simplified or removed if
// cpq_backend_client.js handles base URL and auth internally or via env vars directly.
// const client = new ApiClient.ApiClient(); // Old client instantiation
// client.basePath = process.env.NOCODB_BASE_URL || 'http://localhost:8082'; // Old base path

// Token handling might also be managed by cpq_backend_client or passed to its methods.
// For now, we assume the new client methods can accept a token if needed, or it's handled by the request function
/*
const tokenPath = path.join(__dirname, 'generated', 'token.txt');
let token = '';
if (fs.existsSync(tokenPath)) {
  token = fs.readFileSync(tokenPath, 'utf8').trim();
  console.log('Token loaded successfully.');
} else {
  console.error('Token file not found:', tokenPath);
  process.exit(1);
}

client.defaultHeaders = {
  'xc-token': token,
};
*/

// Use the API - Example with the new client (adjust as needed)
// const api = new ApiClient.ProductApi(client); // Old API instantiation

async function main() {
  try {
    console.log('Running main application logic using new cpqClient...');
    // Example: Listing products using the new client
    // Adjust the call based on actual methods and if a token is needed for this specific call
    const products = await cpqClient.product.list(); 
    console.log('API Response from cpqClient.product.list():', products.length > 0 ? `${products.length} products found.` : 'No products found or empty list.');
    if (products.length > 0) {
        console.log('First product:', products[0]);
    }
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