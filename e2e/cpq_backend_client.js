const fetchPromise = import('node-fetch').then(mod => mod.default);

const BASE_URL = process.env.CPQ_BACKEND_URL || 'http://localhost:8000/api/v1'; // Adjusted to likely Docker service name

async function request(method, path, body = null, token = null) {
    const fetch = await fetchPromise;
    const url = `${BASE_URL}${path}`;
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    };
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    if (body) {
        options.body = JSON.stringify(body);
    }

    console.debug(`CPQ Client Request: ${method} ${url} Body: ${JSON.stringify(body)}`);

    const response = await fetch(url, options);

    if (!response.ok) {
        const errorText = await response.text();
        console.error(`CPQ Client Error: ${response.status} ${response.statusText} - ${errorText} for ${method} ${url}`);
        throw new Error(`API request to ${method} ${url} failed with status ${response.status}: ${errorText}`);
    }

    if (response.status === 204 || response.headers.get("content-length") === "0") {
        return null; // No content
    }
    
    const responseData = await response.json();
    console.debug(`CPQ Client Response: ${method} ${url} Status: ${response.status} Data: ${JSON.stringify(responseData)}`);
    return responseData;
}

const cpqClient = {
    unitType: {
        create: (data, token = null) => request('POST', '/unit_types/', data, token),
        list: (offset = 0, limit = 100, token = null) => request('GET', `/unit_types/?offset=${offset}&limit=${limit}`, null, token),
        getById: (id, token = null) => request('GET', `/unit_types/${id}`, null, token),
        delete: (id, token = null) => request('DELETE', `/unit_types/${id}`, null, token),
        // update: (id, data, token = null) => request('PUT', `/unit_types/${id}`, data, token), // Assuming PUT for update
    },
    material: {
        create: (data, token = null) => request('POST', '/materials/', data, token),
        list: (offset = 0, limit = 100, token = null) => request('GET', `/materials/?offset=${offset}&limit=${limit}`, null, token),
        getById: (id, token = null) => request('GET', `/materials/${id}`, null, token),
        delete: (id, token = null) => request('DELETE', `/materials/${id}`, null, token),
        // update: (id, data, token = null) => request('PUT', `/materials/${id}`, data, token),
    },
    product: {
        create: (data, token = null) => request('POST', '/products/', data, token),
        list: (offset = 0, limit = 100, token = null) => request('GET', `/products/?offset=${offset}&limit=${limit}`, null, token),
        getById: (id, token = null) => request('GET', `/products/${id}`, null, token),
        delete: (id, token = null) => request('DELETE', `/products/${id}`, null, token),
        // update: (id, data, token = null) => request('PUT', `/products/${id}`, data, token),
        getMaterials: (productId, token = null) => request('GET', `/products/${productId}/materials/`, null, token),
        getVariationGroups: (productId, token = null) => request('GET', `/products/${productId}/variation_groups/`, null, token),
    },
    productMaterial: {
        create: (data, token = null) => request('POST', '/product_materials/', data, token),
        getById: (id, token = null) => request('GET', `/product_materials/${id}`, null, token),
        update: (id, data, token = null) => request('PUT', `/product_materials/${id}`, data, token),
        delete: (id, token = null) => request('DELETE', `/product_materials/${id}`, null, token),
    },
    variationGroup: {
        create: (data, token = null) => request('POST', '/variation_groups/', data, token),
        getById: (id, token = null) => request('GET', `/variation_groups/${id}`, null, token),
        update: (id, data, token = null) => request('PUT', `/variation_groups/${id}`, data, token),
        delete: (id, token = null) => request('DELETE', `/variation_groups/${id}`, null, token),
        getOptions: (groupId, token = null) => request('GET', `/variation_groups/${groupId}/options/`, null, token),
    },
    variationOption: {
        create: (data, token = null) => request('POST', '/variation_options/', data, token),
        getById: (id, token = null) => request('GET', `/variation_options/${id}`, null, token),
        update: (id, data, token = null) => request('PUT', `/variation_options/${id}`, data, token),
        delete: (id, token = null) => request('DELETE', `/variation_options/${id}`, null, token),
        getMaterials: (optionId, token = null) => request('GET', `/variation_options/${optionId}/materials/`, null, token),
    },
    variationOptionMaterial: {
        create: (data, token = null) => request('POST', '/variation_option_materials/', data, token),
        getById: (id, token = null) => request('GET', `/variation_option_materials/${id}`, null, token),
        update: (id, data, token = null) => request('PUT', `/variation_option_materials/${id}`, data, token),
        delete: (id, token = null) => request('DELETE', `/variation_option_materials/${id}`, null, token),
    },
    quoteConfig: {
        create: (data, token = null) => request('POST', '/quote_configs/', data, token),
        list: (offset = 0, limit = 100, token = null) => request('GET', `/quote_configs/?offset=${offset}&limit=${limit}`, null, token),
        getById: (id, token = null) => request('GET', `/quote_configs/${id}`, null, token),
        delete: (id, token = null) => request('DELETE', `/quote_configs/${id}`, null, token),
        // update: (id, data, token = null) => request('PUT', `/quote_configs/${id}`, data, token),
    },
    quote: {
        create: (data, token = null) => request('POST', '/quotes/', data, token),
        list: (offset = 0, limit = 100, token = null) => request('GET', `/quotes/?offset=${offset}&limit=${limit}`, null, token),
        getById: (id, token = null) => request('GET', `/quotes/${id}`, null, token),
        update: (id, data, token = null) => request('PUT', `/quotes/${id}`, data, token),
        delete: (id, token = null) => request('DELETE', `/quotes/${id}`, null, token),
        calculate: (id, token = null) => request('POST', `/quotes/${id}/calculate`, null, token),
        getProductEntries: (quoteId, token = null) => request('GET', `/quotes/${quoteId}/product_entries/`, null, token),
    },
    quoteProductEntry: {
        create: (data, token = null) => request('POST', '/quote_product_entries/', data, token),
        getById: (id, token = null) => request('GET', `/quote_product_entries/${id}`, null, token),
        update: (id, data, token = null) => request('PUT', `/quote_product_entries/${id}`, data, token),
        delete: (id, token = null) => request('DELETE', `/quote_product_entries/${id}`, null, token),
        getVariations: (entryId, token = null) => request('GET', `/quote_product_entries/${entryId}/variations/`, null, token),
    },
    quoteProductEntryVariation: {
        create: (data, token = null) => request('POST', '/quote_product_entry_variations/', data, token),
        getById: (id, token = null) => request('GET', `/quote_product_entry_variations/${id}`, null, token),
        delete: (id, token = null) => request('DELETE', `/quote_product_entry_variations/${id}`, null, token),
        // update: (id, data, token = null) => request('PUT', `/quote_product_entry_variations/${id}`, data, token), // Link table, update might not be common
    },
    // TODO: Add other models (QuoteConfig, Quote, QuoteProductEntry, QuoteProductEntryVariation) following the same pattern
};

module.exports = cpqClient;
