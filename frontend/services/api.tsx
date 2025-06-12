// frontend/services/api.tsx

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface Quote {
    id: number;
    name: string | null;
    description: string | null;
    status: string;
    quote_type: string; // Assuming QuoteType is a string in the frontend
    updated_at: string; // Assuming datetime is stringified
    // Add other fields from your Quote model if needed
}

export interface QuotePreview {
    id: number;
    name: string | null;
    description: string | null;
    status: string;
    quote_type: string;
    updated_at: string;
}

export interface CreateQuotePayload {
    name: string;
    quote_type: string; // e.g., "STANDARD", "CUSTOM"
    description?: string;
    config_id?: number;
}

export async function listQuotes(quoteType?: string, offset: number = 0, limit: number = 100): Promise<QuotePreview[]> {
    const params = new URLSearchParams();
    if (quoteType) {
        params.append('quote_type', quoteType);
    }
    params.append('offset', offset.toString());
    params.append('limit', limit.toString());

    const response = await fetch(`${API_BASE_URL}/quote-process/quotes?${params.toString()}`);
    if (!response.ok) {
        throw new Error('Failed to fetch quotes');
    }
    return response.json();
}

export async function createQuote(payload: CreateQuotePayload): Promise<Quote> {
    const response = await fetch(`${API_BASE_URL}/quote-process/quotes`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create quote');
    }
    return response.json();
}

// Add other API functions based on quote_process.py as needed
// For example:
// - getQuoteDetails(quoteId: number)
// - updateQuoteUiState(quoteId: number, uiState: string)
// - setQuoteStatus(quoteId: number, status: string)
// - listCategories(categoryType?: string)
// - listProductsInCategory(categoryName: string)
// - addProductToQuote(quoteId: number, productId: number, quantity: number, role: string)
// - listQuoteProductEntries(quoteId: number, role?: string)
// - removeProductFromQuote(quoteId: number, productEntryId: number)
// - getMaterializedProductEntry(productEntryId: number)
// - setProductVariationOption(productEntryId: number, variationOptionId: number)
// - calculateQuoteTotals(quoteId: number)
// - getCalculatedQuoteDetails(quoteId: number)

