import fs from 'fs/promises'; // Added for file system operations
import dotenv from 'dotenv';



// Load environment variables
dotenv.config();

/**
 * NocoDB PostgreSQL Integration Automation Script
 * 
 * This script automates the process of:
 * 1. Authenticating with NocoDB
 * 2. Creating a new base
 * 3. Adding a PostgreSQL data source
 * 4. Configuring the base to use the PostgreSQL source
 */

// ========================================
// Configuration
// ========================================

const CONFIG = {
    // NocoDB Configuration
    nocodb: {
        baseUrl: process.env.NOCODB_BASE_URL,
        credentials: {
            email: process.env.NOCODB_EMAIL,
            password: process.env.NOCODB_PASSWORD, 
        }
    },

    // PostgreSQL Configuration
    postgres: {
        host: process.env.POSTGRES_HOST,
        port: process.env.POSTGRES_PORT,
        user: process.env.POSTGRES_USER,
        password: process.env.POSTGRES_PASSWORD,
        database: process.env.POSTGRES_DB,
        ssl: process.env.POSTGRES_SSL === 'true'
    },    // Base Configuration
    base: {
        title: process.env.BASE_TITLE || 'Automated App Base (Postgres)',
        sourceAlias: process.env.SOURCE_TITLE || 'AutomatedProductionPostgres'
    },
    
    // File paths
    generated: {
        swaggerJsonPath: process.env.SWAGGER_JSON_PATH || './gen/swagger.json',
        tokenPath: process.env.TOKEN_PATH || './gen/token.txt',
        apiClientOutputDir: process.env.API_CLIENT_OUTPUT_DIR || './gen/generated-client',
        projectName: process.env.PROJECT_NAME || 'nocodb-cpq-client'
    }
};

// ========================================
// Utility Functions
// ========================================

/**
 * Makes authenticated HTTP requests to NocoDB API
 * @param {string} apiPath - The API endpoint path
 * @param {string} method - HTTP method (GET, POST, PATCH, DELETE)
 * @param {object|null} body - Request body for POST/PATCH requests
 * @param {string|null} authToken - Authentication token
 * @returns {Promise<object|null>} API response data or null for empty responses
 */
async function makeNocoDBRequest(apiPath, method = 'GET', body = null, authToken = null) {
    const url = `${CONFIG.nocodb.baseUrl}${apiPath}`;
    console.log(`Making request to: ${url}`);
    const headers = {
        'Content-Type': 'application/json'
    };

    // Add authentication header
    if (authToken) {
        if (authToken.startsWith('eyJ')) {
            headers['xc-auth'] = authToken; // JWT token
        } else {
            headers['xc-token'] = authToken; // API token
        }
    }

    const options = { method, headers };
    if (body) {
        options.body = JSON.stringify(body);
    }

    console.log(`→ ${method} ${apiPath}`);

    try {
        const response = await fetch(url, options);
        const responseText = await response.text();

        if (!response.ok) {
            let errorData;
            try {
                errorData = JSON.parse(responseText);
            } catch (e) {
                errorData = { message: response.statusText, details: responseText };
            }

            const errorMessage = `API Error ${response.status}: ${errorData.message || response.statusText}`;
            console.error(`✗ ${errorMessage}`);
            throw new Error(errorMessage);
        }

        // Handle empty responses
        if (response.status === 204 || !responseText) {
            console.log(`✓ ${method} ${apiPath} - Success (no content)`);
            return null;
        }

        const jsonData = JSON.parse(responseText);
        console.log(`✓ ${method} ${apiPath} - Success`);
        return jsonData;

    } catch (error) {
        if (!error.message.startsWith('API Error')) {
            console.error(`✗ Network error: ${error.message}`);
        }
        throw error;
    }
}

/**
 * Logs sensitive data safely by masking passwords
 * @param {object} data - Data to log
 * @returns {object} Data with sensitive fields masked
 */
function maskSensitiveData(data) {
    const masked = JSON.parse(JSON.stringify(data));

    if (masked.config?.connection?.password) {
        masked.config.connection.password = '********';
    }
    if (masked.password) {
        masked.password = '********';
    }

    return masked;
}

// ========================================
// Authentication Functions
// ========================================

/**
 * Authenticates with NocoDB and returns a JWT token
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<string>} JWT authentication token
 */
async function signIn(email, password) {
    console.log(`\n🔐 Signing in as: ${email}`);

    const payload = { email, password };
    console.log('Signing in with payload:', payload);
    const response = await makeNocoDBRequest('/api/v1/auth/user/signin', 'POST', payload);

    if (!response?.token) {
        throw new Error('Sign-in failed: No token returned');
    }

    console.log('✓ Sign-in successful');
    return response.token;
}

/**
 * Creates an API token using the JWT token
 * @param {string} jwtToken - JWT token from sign-in
 * @returns {Promise<string>} API token for subsequent requests
 */
async function createApiToken(jwtToken) {
    console.log('\n🔑 Creating API token...');

    const payload = { description: `Auto-generated token ${new Date().toISOString()}` };
    const response = await makeNocoDBRequest('/api/v1/tokens', 'POST', payload, jwtToken);

    if (!response?.token) {
        throw new Error('API token creation failed: No token returned');
    }

    console.log('✓ API token created successfully');
    return response.token;
}

/**
 * Saves the API token to a file
 * @param {string} token - API token to save
 * @returns {Promise<void>}
 */
async function saveTokenToFile(token) {
    console.log(`\n💾 Saving API token to file...`);
    const filePath = CONFIG.generated.tokenPath;
    
    try {
        // Make sure the directory exists
        const directory = filePath.substring(0, filePath.lastIndexOf('/'));
        try {
            await fs.mkdir(directory, { recursive: true });
        } catch (error) {
            // Ignore if directory already exists
            if (error.code !== 'EEXIST') {
                throw error;
            }
        }
        
        await fs.writeFile(filePath, token);
        console.log(`✓ API token saved successfully to ${filePath}`);
    } catch (error) {
        console.error(`✗ Error saving API token: ${error.message}`);
        // We don't want to fail the whole automation if just the token save fails
        // Just log the error and continue
    }
}

// ========================================
// Base Management Functions
// ========================================

/**
 * Finds an existing base by title
 * @param {string} title - Base title to search for
 * @param {string} apiToken - API token for authentication
 * @returns {Promise<object|null>} Existing base object or null if not found
 */
async function findExistingBase(title, apiToken) {
    console.log(`\\n🔎 Searching for existing base: \"${title}\"`);
    try {
        const response = await makeNocoDBRequest('/api/v2/meta/bases', 'GET', null, apiToken);
        if (response && response.list) {
            const existingBase = response.list.find(base => base.title === title);
            if (existingBase) {
                console.log(`✓ Found existing base (ID: ${existingBase.id}, Title: ${existingBase.title})`);
                return existingBase;
            }
        }
        console.log(`✓ No base found with title: \"${title}\"`);
        return null;
    } catch (error) {
        console.error(`✗ Error searching for base: ${error.message}`);
        throw error;
    }
}

/**
 * Creates a new base in NocoDB
 * @param {string} title - Base title
 * @param {string} apiToken - API token for authentication
 * @returns {Promise<object>} Created base object
 */
async function createBase(title, apiToken) {
    console.log(`\n📊 Creating base: "${title}"`);

    const payload = { title };
    const response = await makeNocoDBRequest('/api/v2/meta/bases', 'POST', payload, apiToken);

    if (!response?.id) {
        throw new Error('Base creation failed: No ID returned');
    }

    console.log(`✓ Base created successfully (ID: ${response.id})`);
    return response;
}

/**
 * Adds a PostgreSQL data source to a base
 * @param {string} baseId - Base ID
 * @param {string} alias - Source alias/name
 * @param {object} pgConfig - PostgreSQL connection configuration
 * @param {string} apiToken - API token for authentication
 * @returns {Promise<object>} Created source object
 */
async function addPostgreSQLSource(baseId, alias, pgConfig, apiToken) {
    console.log(`\n🔗 Adding PostgreSQL source: "${alias}"`);

    const payload = {
        alias,
        type: 'pg',
        config: {
            client: 'pg',
            connection: {
                host: pgConfig.host,
                port: pgConfig.port,
                user: pgConfig.user,
                password: pgConfig.password,
                database: pgConfig.database,
                ...(pgConfig.ssl && { ssl: pgConfig.ssl })
            }
        },
        enabled: true
    };

    console.log('Connection details:', maskSensitiveData(payload));

    const response = await makeNocoDBRequest(
        `/api/v2/meta/bases/${baseId}/sources`,
        'POST',
        payload,
        apiToken
    );

    if (!response?.id) {
        throw new Error('PostgreSQL source creation failed: No ID returned');
    }

    console.log(`✓ PostgreSQL source added successfully (ID: ${response.id})`);
    return response;
}

/**
 * Configures a base to use a specific data source
 * @param {string} baseId - Base ID
 * @param {object} sourceDetails - Source details (id, alias, type)
 * @param {string} apiToken - API token for authentication
 * @returns {Promise<object>} Updated base object
 */
async function configureBaseSource(baseId, sourceDetails, apiToken) {
    console.log(`\\n⚙️  Configuring base to use source: "${sourceDetails.alias}"`);

    const payload = {
        sources: [{
            id: sourceDetails.id,
            alias: sourceDetails.alias,
            type: sourceDetails.type,
            enabled: true,
            is_meta: true
        }]
    };

    const response = await makeNocoDBRequest(
        `/api/v2/meta/bases/${baseId}`,
        'PATCH',
        payload,
        apiToken
    );

    console.log('✓ Base configuration updated successfully');
    return response;
}

/**
 * Saves the Swagger JSON for a given base to a file
 * @param {string} baseId - Base ID
 * @param {string} apiToken - API token for authentication
 * @returns {Promise<void>}
 */
async function saveSwaggerJson(baseId, apiToken) {
    console.log(`\\n📄 Saving Swagger JSON for base: ${baseId}`);
    const swaggerUrl = `${CONFIG.nocodb.baseUrl}/api/v2/meta/bases/${baseId}/swagger.json`;
    const headers = {
        'xc-token': apiToken // Using the API token obtained earlier
    };

    try {
        console.log(`Making request to: ${swaggerUrl}`);
        const response = await fetch(swaggerUrl, { headers });

        if (!response.ok) {
            const errorText = await response.text();
            let errorData;
            try {
                errorData = JSON.parse(errorText);
            } catch (e) {
                errorData = { message: response.statusText, details: errorText };
            }
            const errorMessage = `Swagger API Error ${response.status}: ${errorData.message || response.statusText}`;
            console.error(`✗ ${errorMessage}`);
            throw new Error(errorMessage);
        }        const swaggerJson = await response.json();
        const filePath = CONFIG.generated.swaggerJsonPath;
        await fs.writeFile(filePath, JSON.stringify(swaggerJson, null, 2));
        console.log(`✓ Swagger JSON saved successfully to ${filePath}`);

    } catch (error) {
        console.error(`✗ Error saving Swagger JSON: ${error.message}`);
        // We might not want to throw here if swagger saving is optional
        // For now, let's rethrow to indicate failure in this step
        throw error;
    }
}

/**
 * Generates an API client from the Swagger JSON file using openapi-generator-cli
 * @param {string} swaggerFilePath - Path to the Swagger JSON file
 * @returns {Promise<void>}
 */
async function generateApiClient(swaggerFilePath) {
    console.log(`\\n🔧 Generating API client from Swagger JSON`);
    
    try {
        // Set up the path for the generated client
        const outputDir = CONFIG.generated.apiClientOutputDir;
        
        // Import the openapi generator dynamically
        const { exec } = await import('child_process');
        const util = await import('util');
        const execPromise = util.promisify(exec);
        
        console.log(`Generating API client at: ${outputDir}`);
        
        // Delete directory if it exists
        try {
            await fs.rm(outputDir, { recursive: true, force: true });
            console.log(`✓ Removed existing output directory: ${outputDir}`);
        } catch (err) {
            if (err.code !== 'ENOENT') {
                throw err;
            }
        }

        // Execute the openapi-generator-cli command
        const command = `npx openapi-generator-cli generate -i ${swaggerFilePath} -g javascript -o ${outputDir} --additional-properties=usePromises=true,projectName=${CONFIG.generated.projectName}`;
        
        console.log(`Executing command: ${command}`);
        const { stdout, stderr } = await execPromise(command);
        
        if (stderr && !stderr.includes('WARNING')) {
            console.error(`⚠️ OpenAPI Generator CLI warnings/errors: ${stderr}`);
        }
        
        // check if the output directory was created and has files
        const files = await fs.readdir(outputDir);
        if (files.length === 0) {
            throw new Error(`No files generated in output directory: ${outputDir}`);
        }

        console.log(`✓ API client generated successfully at ${outputDir}`);
        
    } catch (error) {
        console.error(`✗ Error generating API client: ${error.message}`);
        console.error(error.stack);
        // We don't want to fail the whole automation if just the client generation fails
        // Just log the error and continue
    }
}

// ========================================
// Main Execution Function
// ========================================

/**
 * Main automation workflow
 */
async function runAutomation() {
    console.log('🚀 Starting NocoDB PostgreSQL Integration Automation\n');
    console.log('Configuration:');
    console.log(`  NocoDB URL: ${CONFIG.nocodb.baseUrl}`);
    console.log(`  PostgreSQL Host: ${CONFIG.postgres.host}:${CONFIG.postgres.port}`);
    console.log(`  Database: ${CONFIG.postgres.database}`);
    console.log(`  Base Title: ${CONFIG.base.title}\n`);    try {
        // Step 1: Authentication
        const jwtToken = await signIn(
            CONFIG.nocodb.credentials.email,
            CONFIG.nocodb.credentials.password
        );

        const apiToken = await createApiToken(jwtToken);
        
        // Save the token to file for other services to use
        await saveTokenToFile(apiToken);

        // Step 2: Check for existing Base
        let base = await findExistingBase(CONFIG.base.title, apiToken);
        let pgSource;

        if (base) {
            console.log(`\\n✅ Base \"${CONFIG.base.title}\" already exists. Skipping creation.`);
            // Optionally, you could try to find the source if the base exists
            // For now, we assume if the base exists, setup was likely completed.
            // To make it more robust, you could list sources for this base and check.
            // For this example, we'll just report success.
            // Try to find the source associated with this base to report it
            const sources = await makeNocoDBRequest(`/api/v2/meta/bases/${base.id}/sources`, 'GET', null, apiToken);
            if (sources && sources.list && sources.list.length > 0) {
                // Assuming the first source is the one we're interested in, or match by alias if needed
                pgSource = sources.list.find(s => s.alias === CONFIG.base.sourceAlias);
                if (!pgSource && sources.list.length > 0) { // if not found by alias, take the first one
                    pgSource = sources.list[0];
                    console.log(`✓ Found existing source (ID: ${pgSource.id}, Alias: ${pgSource.alias}) for base \"${base.title}\"`);
                } else if (pgSource) {
                    console.log(`✓ Found existing source (ID: ${pgSource.id}, Alias: ${CONFIG.base.sourceAlias}) for base \"${base.title}\"`);
                } else {
                    console.log(`ℹ️ No source named \"${CONFIG.base.sourceAlias}\" found for existing base \"${base.title}\". Manual check might be needed.`);
                }
            } else {
                console.log(`ℹ️ No sources found for existing base \"${base.title}\". Manual check might be needed.`);
            }

        } else {
            console.log(`\\n✨ Base \"${CONFIG.base.title}\" does not exist. Proceeding with creation.`);
            // Step 2a: Create Base
            base = await createBase(CONFIG.base.title, apiToken);

            // Step 3: Add PostgreSQL Source
            pgSource = await addPostgreSQLSource(
                base.id,
                CONFIG.base.sourceAlias,
                CONFIG.postgres,
                apiToken
            );

            // Step 4: Configure Base to Use PostgreSQL Source
            await configureBaseSource(base.id, pgSource, apiToken);
            console.log(`\\n🎉 New base and source configured successfully!`);
        }        // Step 5: Save Swagger JSON
        // Ensure base.id and apiToken are available
        if (base && base.id && apiToken) {
            await saveSwaggerJson(base.id, apiToken);
            
            // Step 6: Generate API client from the Swagger JSON
            try {
                await generateApiClient(CONFIG.generated.swaggerJsonPath);
            } catch (error) {
                console.error(`Failed to generate API client: ${error.message}`);
                // Continue with the rest of the automation even if client generation fails
            }
        } else {
            console.warn('Skipping Swagger JSON save and API client generation due to missing base ID or API token.');
        }

        // Success Summary
        console.log('\n🌟 Automation completed!');
        console.log('\nSummary:');
        console.log(`  Base ID: ${base.id}`);
        console.log(`  Base Title: ${base.title}`); // Use base.title in case it was pre-existing
        if (pgSource) {
            console.log(`  Source ID: ${pgSource.id}`);
            console.log(`  Source Alias: ${pgSource.alias}`); // Use pgSource.alias
        } else {
            console.log(`  Source: Not created or found in this run (as base existed).`);
        }
        console.log(`  NocoDB URL: ${CONFIG.nocodb.baseUrl}/dashboard/#/base/${base.id}`);
        console.log(`  API Client: Generated in ./generated-client directory`);


        return {
            success: true,
            base,
            source: pgSource
        };

    } catch (error) {
        console.error('\n❌ Automation failed!');
        console.error(`Error: ${error.message}`);

        return {
            success: false,
            error: error.message
        };
    }
}

// ========================================
// Validation Functions
// ========================================

/**
 * Validates configuration before running automation
 */
function validateConfiguration() {
    const errors = [];

    // Check required NocoDB configuration
    if (!CONFIG.nocodb.baseUrl || CONFIG.nocodb.baseUrl === 'https://your-nocodb-instance.com') {
        errors.push('NOCODB_BASE_URL is not properly configured');
    }
    // Ensure email and password are not the placeholder values if they are critical for your setup
    if (!CONFIG.nocodb.credentials.email || CONFIG.nocodb.credentials.email === 'your-email@example.com') {
        errors.push('NOCODB_EMAIL is not properly configured');
    }
    if (!CONFIG.nocodb.credentials.password || CONFIG.nocodb.credentials.password === 'your-password') {
        errors.push('NOCODB_PASSWORD is not properly configured');
    }

    // Check PostgreSQL configuration
    if (CONFIG.postgres.host === 'your_pg_host' || !CONFIG.postgres.password) {
        errors.push('PostgreSQL connection details are not properly configured');
    }

    if (errors.length > 0) {
        console.error('❌ Configuration errors:');
        errors.forEach(error => console.error(`  • ${error}`));
        console.error('\nPlease set the required environment variables or update the CONFIG object.');
        return false;
    }

    return true;
}

// ========================================
// Script Execution
// ========================================

console.log('🔧 Validating configuration...');
if (validateConfiguration()) {
    runAutomation()
        .then(result => {
            process.exit(result.success ? 0 : 1);
        })
        .catch(error => {
            console.error('Unexpected error:', error);
            process.exit(1);
        });
} else {
    process.exit(1);
}