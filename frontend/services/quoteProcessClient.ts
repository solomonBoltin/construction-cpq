import { 
    QuotePreview, 
    CategoryPreview, 
    ProductPreview, 
    MaterializedProductEntry, 
    Quote,
    QuoteType,
    ProductRole,
    CalculatedQuote
} from '../types';
import { API_BASE_URL, DEFAULT_QUOTE_CONFIG_ID } from '../constants';

const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
};

async function handleResponse<T,>(response: Response): Promise<T> {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `API request failed with status ${response.status}`);
    }
    return response.json();
}

export const quoteProcessClient = {
    listQuotes: async (quoteType?: QuoteType, offset: number = 0, limit: number = 100): Promise<QuotePreview[]> => {
        const params = new URLSearchParams({
            offset: offset.toString(),
            limit: limit.toString(),
        });
        if (quoteType) {
            params.append('quote_type', quoteType);
        }
        const response = await fetch(`${API_BASE_URL}/quote-process/quotes?${params.toString()}`, { headers });
        return handleResponse<QuotePreview[]>(response);
    },

    createQuote: async (name: string, quote_type: QuoteType, description?: string, config_id: number = DEFAULT_QUOTE_CONFIG_ID): Promise<Quote> => {
        const params = new URLSearchParams({
            name,
            quote_type,
            config_id: config_id.toString(),
        });
        if (description) {
            params.append('description', description);
        }
        const response = await fetch(`${API_BASE_URL}/quote-process/quotes?${params.toString()}`, {
            method: 'POST',
            headers,
        });
        return handleResponse<Quote>(response);
    },
    
    getQuoteForEditing: async (quoteId: number): Promise<Quote> => {
        const response = await fetch(`${API_BASE_URL}/quote-process/quotes/${quoteId}`, { headers });
        return handleResponse<Quote>(response);
    },
    
    listCategories: async (categoryType?: string, offset: number = 0, limit: number = 100): Promise<CategoryPreview[]> => {
        const params = new URLSearchParams({
            offset: offset.toString(),
            limit: limit.toString(),
        });
        if (categoryType) {
            params.append('category_type', categoryType);
        }
        const response = await fetch(`${API_BASE_URL}/quote-process/categories?${params.toString()}`, { headers });
        return handleResponse<CategoryPreview[]>(response);
    },

    listProductsInCategory: async (categoryName: string, offset: number = 0, limit: number = 100): Promise<ProductPreview[]> => {
         const params = new URLSearchParams({
            offset: offset.toString(),
            limit: limit.toString(),
        });
        const response = await fetch(`${API_BASE_URL}/quote-process/categories/${encodeURIComponent(categoryName)}/products?${params.toString()}`, { headers });
        return handleResponse<ProductPreview[]>(response);
    },
    
    getMaterializedProductEntry: async (productEntryId: number): Promise<MaterializedProductEntry> => {
        const response = await fetch(`${API_BASE_URL}/quote-process/product-entries/${productEntryId}`, { headers });
        return handleResponse<MaterializedProductEntry>(response);
    },
    
    addQuoteProductEntry: async (quoteId: number, productId: number, quantity: number, role: ProductRole): Promise<MaterializedProductEntry> => {
        const params = new URLSearchParams({
            product_id: productId.toString(),
            quantity: quantity.toString(), // Backend expects Decimal, which can be string
            role: role,
        });
        const response = await fetch(`${API_BASE_URL}/quote-process/quotes/${quoteId}/product-entries?${params.toString()}`, {
            method: 'POST',
            headers,
        });
        return handleResponse<MaterializedProductEntry>(response);
    },

    deleteQuoteProductEntry: async (quoteId: number, productEntryId: number): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/quote-process/quotes/${quoteId}/product-entries/${productEntryId}`, {
            method: 'DELETE',
            headers,
        });
        if (!response.ok && response.status !== 204) { // 204 is success with no content
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || `API request failed with status ${response.status}`);
        }
        // No content to parse for 204
    },
    
    updateQuoteProductEntry: async (productEntryId: number, data: { quantity?: number; notes?: string }): Promise<MaterializedProductEntry> => {
        // PUT /quote-process/product-entries/{product_entry_id}
        const response = await fetch(`${API_BASE_URL}/quote-process/product-entries/${productEntryId}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(data),
        });
        return handleResponse<MaterializedProductEntry>(response);
    },

    setQuoteProductVariationOption: async (productEntryId: number, variationOptionId: number): Promise<MaterializedProductEntry> => {
        const response = await fetch(`${API_BASE_URL}/quote-process/product-entries/${productEntryId}/variations/${variationOptionId}`, {
            method: 'PUT',
            headers,
        });
        return handleResponse<MaterializedProductEntry>(response);
    },

    calculateQuote: async (quoteId: number): Promise<CalculatedQuote> => {
        const response = await fetch(`${API_BASE_URL}/quote-process/quotes/${quoteId}/calculate`, {
            method: 'POST',
            headers,
        });
        return handleResponse<CalculatedQuote>(response);
    },

    getCalculatedQuote: async (quoteId: number): Promise<CalculatedQuote | null> => {
        const response = await fetch(`${API_BASE_URL}/quote-process/quotes/${quoteId}/calculate`, { headers });
        if (response.status === 404) return null; // Or if API returns empty for not found
        return handleResponse<CalculatedQuote>(response);
    },

    listProductsByCategoryType: async (categoryType: string, offset: number = 0, limit: number = 100): Promise<ProductPreview[]> => {
        const params = new URLSearchParams({
            offset: offset.toString(),
            limit: limit.toString(),
        });
        const response = await fetch(`${API_BASE_URL}/quote-process/products/by-category-type/${encodeURIComponent(categoryType)}?${params.toString()}`, { headers });
        return handleResponse<ProductPreview[]>(response);
    },
};
