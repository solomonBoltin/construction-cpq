/**
 * Makes authenticated HTTP requests to NocoDB API for column setup.
 * @param {string} baseUrl - The NocoDB base URL.
 * @param {string} apiPath - The API endpoint path.
 * @param {string} method - HTTP method (GET, POST, PATCH, DELETE).
 * @param {object|null} body - Request body for POST/PATCH requests.
 * @param {string} apiToken - NocoDB API Key (xc-token).
 * @returns {Promise<object|null>} API response data or null for empty responses.
 */
async function makeNocoDBRequestForSetup(baseUrl, apiPath, method = 'GET', body = null, apiToken) {
    const url = `${baseUrl}${apiPath}`;
    const headers = {
        'Content-Type': 'application/json',
        'xc-token': apiToken,
    };
    const options = { method, headers };
    if (body) {
        options.body = JSON.stringify(body);
    }
    console.log(`→ (ColumnSetup) ${method} ${apiPath}`);
    try {
        const response = await fetch(url, options);
        const responseText = await response.text();
        if (!response.ok) {
            console.error(`✗ (ColumnSetup) API Error ${response.status}: ${responseText} for ${method} ${url}`);
            throw new Error(`API Error ${response.status}: ${responseText}`);
        }
        if (response.status === 204 || !responseText) {
            console.log(`✓ (ColumnSetup) ${method} ${apiPath} - Success (No Content)`);
            return null;
        }
        const jsonData = JSON.parse(responseText);
        console.log(`✓ (ColumnSetup) ${method} ${apiPath} - Success`);
        return jsonData;
    } catch (error) {
        // Log the error with more context if it's not already an API error from above
        if (!error.message.startsWith('API Error')) {
            console.error(`✗ (ColumnSetup) Error in makeNocoDBRequestForSetup for ${method} ${apiPath}: ${error.message}`);
        }
        throw error;
    }
}

/**
 * Finds the internal NocoDB ID for a table given its name.
 * @param {string} baseUrl - The NocoDB base URL.
 * @param {string} apiToken - NocoDB API Key.
 * @param {string} baseId - The ID of the NocoDB base.
 * @param {string} tableName - The database table name.
 * @returns {Promise<string>} The NocoDB internal table ID.
 */
async function findTableId(baseUrl, apiToken, baseId, tableName) {
    console.log(`🔎 (ColumnSetup) Searching for table ID for "${tableName}" in base "${baseId}"`);
    const response = await makeNocoDBRequestForSetup(baseUrl, `/api/v2/meta/bases/${baseId}/tables`, 'GET', null, apiToken);
    if (response && response.list) {
        const foundTable = response.list.find(table => table.table_name === tableName || table.alias === tableName);
        if (foundTable) {
            console.log(`✓ (ColumnSetup) Found table "${tableName}" with ID: ${foundTable.id}`);
            return foundTable.id;
        }
    }
    throw new Error(`Table "${tableName}" not found in base "${baseId}". Check if NocoDB has synced with the database schema.`);
}

/**
 * Finds the internal NocoDB ID for a column given its name within a table.
 * @param {string} baseUrl - The NocoDB base URL.
 * @param {string} apiToken - NocoDB API Key.
 * @param {string} tableId - The NocoDB internal table ID.
 * @param {string} columnName - The database column name.
 * @returns {Promise<string>} The NocoDB internal column ID.
 */
async function findColumnId(baseUrl, apiToken, tableId, columnName) {
    console.log(`🔎 (ColumnSetup) Searching for column ID for "${columnName}" in table "${tableId}"`);
    // Corrected endpoint: Fetch the entire table metadata
    const response = await makeNocoDBRequestForSetup(baseUrl, `/api/v2/meta/tables/${tableId}`, 'GET', null, apiToken);
    // The columns are typically in a 'columns' array within the table object
    if (response && response.columns && Array.isArray(response.columns)) {
        const foundColumn = response.columns.find(col => col.column_name === columnName || col.alias === columnName);
        if (foundColumn) {
            console.log(`✓ (ColumnSetup) Found column "${columnName}" with ID: ${foundColumn.id}`);
            return foundColumn.id;
        }
    }
    throw new Error(`Column "${columnName}" not found in table ID "${tableId}". Response: ${JSON.stringify(response)}`);
}

/**
 * Updates a NocoDB column to be a SingleSelect type with specified options.
 * @param {string} baseUrl - The NocoDB base URL.
 * @param {string} apiToken - NocoDB API Key.
 * @param {string} columnId - The NocoDB internal column ID.
 * @param {string[]} enumValues - An array of string values for the SingleSelect options.
 * @returns {Promise<void>}
 */
async function updateColumnToSingleSelect(baseUrl, apiToken, columnId, enumValues) {
    console.log(`⚙️ (ColumnSetup) Updating column "${columnId}" to SingleSelect`);
    // Ensure enumValues are uppercased for the title
    const optionsPayload = enumValues.map(value => ({ title: value}));
    const payload = {
        uidt: "SingleSelect", // NocoDB UI type for Single Select
        colOptions: {
            options: optionsPayload
        }
    };
    await makeNocoDBRequestForSetup(baseUrl, `/api/v2/meta/columns/${columnId}`, 'PATCH', payload, apiToken);
    console.log(`✓ (ColumnSetup) Column "${columnId}" updated successfully to SingleSelect with options:`, optionsPayload.map(o => o.title));
}

/**
 * Sets up a specific column in NocoDB to be of type SingleSelect with given enum values.
 * This function orchestrates finding the table and column IDs and then updating the column type.
 * @param {string} nocodbBaseUrl - The base URL of the NocoDB API (e.g., http://localhost:8080).
 * @param {string} apiToken - The NocoDB API token (xc-token).
 * @param {string} baseId - The ID of the NocoDB base (project).
 * @param {string} tableName - The name of the database table containing the column.
 * @param {string} columnName - The name of the database column to configure.
 * @param {string[]} enumValues - An array of string values that will become the options for the SingleSelect.
 * @export
 */
export async function setupColumnTypeToSingleSelect(nocodbBaseUrl, apiToken, baseId, tableName, columnName, enumValues) {
    console.log(`
🔄 (ColumnSetup) Starting setup for column "${columnName}" in table "${tableName}" of base "${baseId}" to SingleSelect.`);
    try {
        const tableId = await findTableId(nocodbBaseUrl, apiToken, baseId, tableName);
        const columnId = await findColumnId(nocodbBaseUrl, apiToken, tableId, columnName);
        await updateColumnToSingleSelect(nocodbBaseUrl, apiToken, columnId, enumValues);
        console.log(`✓ (ColumnSetup) Successfully configured column "${columnName}" in table "${tableName}" (Base ID: ${baseId}) as SingleSelect.`);
    } catch (error) {
        console.error(`✗ (ColumnSetup) Failed to setup column "${columnName}" in table "${tableName}" (Base ID: ${baseId}): ${error.message}`);
        // Rethrow the error to allow the calling function to handle it, potentially stopping the overall script.
        throw error;
    }
}
