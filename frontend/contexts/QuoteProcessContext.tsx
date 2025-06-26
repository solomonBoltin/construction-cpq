import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { 
    AppView, 
    CatalogStepKey, 
    CatalogContextState, 
    MockFullQuote, 
    ProductRole,
    MockQuoteProductEntry,
    // MaterializedProductEntry, // Not directly used in this file for action payloads/state shaping
    QuotePreview,
    QuoteType, // Added import
    // Quote, // Not directly used in this file for action payloads/state shaping
    CalculatedQuote
} from '../types';
import { apiClient } from '../services/api'; 
// import { Steps, AddonCategoryType, GateCategoryType, MainProductCategoryType } from '../constants'; // Not used in this file

interface QuoteProcessState {
    currentView: AppView;
    activeQuoteId: number | null;
    activeStep: CatalogStepKey;
    catalogContext: Omit<CatalogContextState, 'activeProductEntryId'>;
    quotes: QuotePreview[];
    isLoading: boolean;
    error: string | null;
    isModalOpen: boolean;
    calculatedQuoteResult: CalculatedQuote | null;
}

const initialState: QuoteProcessState = {
    currentView: 'quote_list',
    activeQuoteId: null,
    activeStep: 'choose_category',
    catalogContext: {
        selectedCategoryName: null,
        activeQuoteFull: null,
    },
    quotes: [],
    isLoading: false,
    error: null,
    isModalOpen: false,
    calculatedQuoteResult: null,
};

type Action =
    | { type: 'SET_VIEW'; payload: AppView }
    | { type: 'START_LOADING' }
    | { type: 'END_LOADING' }
    | { type: 'SET_ERROR'; payload: string | null }
    | { type: 'SET_QUOTES'; payload: QuotePreview[] }
    | { type: 'SET_ACTIVE_QUOTE_ID'; payload: number | null }
    | { type: 'SET_ACTIVE_STEP'; payload: CatalogStepKey }
    | { type: 'SET_SELECTED_CATEGORY'; payload: string | null }
    | { type: 'SET_ACTIVE_QUOTE_FULL'; payload: MockFullQuote | null }
    | { type: 'UPDATE_ACTIVE_QUOTE_ENTRY'; payload: MockQuoteProductEntry }
    | { type: 'REMOVE_ACTIVE_QUOTE_ENTRY'; payload: number } // entryId
    | { type: 'ADD_ACTIVE_QUOTE_ENTRY'; payload: MockQuoteProductEntry }
    | { type: 'TOGGLE_MODAL'; payload: boolean }
    | { type: 'SET_CALCULATED_QUOTE'; payload: CalculatedQuote | null};


const reducer = (state: QuoteProcessState, action: Action): QuoteProcessState => {
    switch (action.type) {
        case 'SET_VIEW':
            return { ...state, currentView: action.payload, error: null };
        case 'START_LOADING':
            return { ...state, isLoading: true, error: null };
        case 'END_LOADING':
            return { ...state, isLoading: false };
        case 'SET_ERROR':
            return { ...state, error: action.payload, isLoading: false };
        case 'SET_QUOTES':
            return { ...state, quotes: action.payload };
        case 'SET_ACTIVE_QUOTE_ID':
            return { ...state, activeQuoteId: action.payload, calculatedQuoteResult: null };
        case 'SET_ACTIVE_STEP':
            return { ...state, activeStep: action.payload };
        case 'SET_SELECTED_CATEGORY':
            return { ...state, catalogContext: { ...state.catalogContext, selectedCategoryName: action.payload } };
        case 'SET_ACTIVE_QUOTE_FULL': {
            const incomingQuote = action.payload;
            if (!incomingQuote) {
                return { ...state, catalogContext: { ...state.catalogContext, activeQuoteFull: null } };
            }
            // Ensure product_entries is always an array
            const sanitizedQuote = {
                ...incomingQuote,
                product_entries: incomingQuote.product_entries || [],
            };
            return { ...state, catalogContext: { ...state.catalogContext, activeQuoteFull: sanitizedQuote } };
        }
        case 'UPDATE_ACTIVE_QUOTE_ENTRY':
            if (!state.catalogContext.activeQuoteFull) return state;
            return {
                ...state,
                catalogContext: {
                    ...state.catalogContext,
                    activeQuoteFull: {
                        ...state.catalogContext.activeQuoteFull,
                        product_entries: state.catalogContext.activeQuoteFull.product_entries.map(e =>
                            e.id === action.payload.id ? action.payload : e
                        ),
                    },
                },
            };
        case 'REMOVE_ACTIVE_QUOTE_ENTRY':
            if (!state.catalogContext.activeQuoteFull) return state;
            return {
                ...state,
                catalogContext: {
                    ...state.catalogContext,
                    activeQuoteFull: {
                        ...state.catalogContext.activeQuoteFull,
                        product_entries: state.catalogContext.activeQuoteFull.product_entries.filter(e => e.id !== action.payload),
                    },
                },
            };
        case 'ADD_ACTIVE_QUOTE_ENTRY':
             if (!state.catalogContext.activeQuoteFull) return state;
            return {
                ...state,
                catalogContext: {
                    ...state.catalogContext,
                    activeQuoteFull: {
                        ...state.catalogContext.activeQuoteFull,
                        product_entries: [...state.catalogContext.activeQuoteFull.product_entries, action.payload],
                    },
                },
            };
        case 'TOGGLE_MODAL':
            return { ...state, isModalOpen: action.payload };
        case 'SET_CALCULATED_QUOTE':
            return { ...state, calculatedQuoteResult: action.payload, isLoading: false};
        default:
            return state;
    }
};

interface QuoteProcessContextType extends QuoteProcessState {
    dispatch: React.Dispatch<Action>;
    fetchQuotes: () => Promise<void>;
    createNewQuote: (name: string, description: string, type: QuoteType) => Promise<void>;
    selectQuoteForEditing: (quoteId: number) => Promise<void>;
    selectCategory: (categoryName: string) => void;
    selectProduct: (productId: number, role: ProductRole) => Promise<void>;
    updateProductQuantity: (entryId: number, quantity: number) => Promise<void>;
    updateProductVariation: (entryId: number, groupId: number, optionId: number) => Promise<void>;
    toggleAdditionalProduct: (productId: number) => Promise<void>;
    goToStep: (step: CatalogStepKey) => void;
    calculateActiveQuote: () => Promise<void>;
    fetchCalculatedQuote: (quoteId: number) => Promise<void>;
}

const QuoteProcessContext = createContext<QuoteProcessContextType | undefined>(undefined);

export const QuoteProcessProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [state, dispatch] = useReducer(reducer, initialState);

    const fetchQuotes = useCallback(async () => {
        dispatch({ type: 'START_LOADING' });
        try {
            const quotesData = await apiClient.listQuotes(QuoteType.FENCE_PROJECT);
            dispatch({ type: 'SET_QUOTES', payload: quotesData });
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, []);

    const selectQuoteForEditing = useCallback(async (quoteId: number) => {
        dispatch({ type: 'START_LOADING' });
        try {
            const activeQuoteData = await apiClient.getQuoteForEditing(quoteId);
            if (activeQuoteData) {
                dispatch({ type: 'SET_ACTIVE_QUOTE_ID', payload: quoteId });
                dispatch({ type: 'SET_ACTIVE_QUOTE_FULL', payload: activeQuoteData as MockFullQuote });
                dispatch({ type: 'SET_VIEW', payload: 'catalog' });
                dispatch({ type: 'SET_ACTIVE_STEP', payload: 'choose_category' });
                dispatch({ type: 'SET_SELECTED_CATEGORY', payload: null }); // Reset category selection
            } else {
                dispatch({type: 'SET_ERROR', payload: 'Failed to load quote for editing.'});
            }
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, []);
    
    const createNewQuote = useCallback(async (name: string, description: string, type: QuoteType = QuoteType.FENCE_PROJECT) => {
        dispatch({ type: 'START_LOADING' });
        try {
            const newQuote = await apiClient.createQuote(name, type, description);
            // Fetch fresh list or add to existing
            await fetchQuotes(); 
            dispatch({ type: 'TOGGLE_MODAL', payload: false });
            // Now select the quote for editing to transition views
            await selectQuoteForEditing(newQuote.id);

        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, [fetchQuotes, selectQuoteForEditing]);

    const selectCategory = useCallback((categoryName: string) => {
        dispatch({ type: 'SET_SELECTED_CATEGORY', payload: categoryName });
        dispatch({ type: 'SET_ACTIVE_STEP', payload: 'choose_main_product' });
    }, []);

    const selectProduct = useCallback(async (productId: number, role: ProductRole) => {
        if (!state.activeQuoteId) return;
        dispatch({ type: 'START_LOADING' });
        try {
            // @ts-ignore - Mock client takes quantity and returns MockQuoteProductEntry
            const newEntry = await apiClient.addQuoteProductEntry(state.activeQuoteId, productId, 1, role); // Default quantity 1
            dispatch({ type: 'ADD_ACTIVE_QUOTE_ENTRY', payload: newEntry as MockQuoteProductEntry});
            const nextStep = role === ProductRole.MAIN ? 'configure_main' : 'configure_secondary';
            dispatch({ type: 'SET_ACTIVE_STEP', payload: nextStep });
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, [state.activeQuoteId]);

    const updateProductQuantity = useCallback(async (entryId: number, quantity: number) => {
        if (!state.activeQuoteId) return;
        // No loading state for faster UI
        try {
            // @ts-ignore - Mock client
            const updatedEntry = await apiClient.updateQuoteProductEntry(entryId, { quantity });
            dispatch({ type: 'UPDATE_ACTIVE_QUOTE_ENTRY', payload: updatedEntry as MockQuoteProductEntry });
        } catch (err) {
            console.error("Failed to update quantity:", err);
            // Optionally dispatch SET_ERROR
        }
    }, [state.activeQuoteId]);

    const updateProductVariation = useCallback(async (entryId: number, groupId: number, optionId: number) => {
        if (!state.activeQuoteId) return;
        dispatch({ type: 'START_LOADING' });
        try {
            // @ts-ignore - Mock client
            const updatedEntry = await apiClient.setQuoteProductVariationOption(state.activeQuoteId, entryId, groupId, optionId);
            dispatch({ type: 'UPDATE_ACTIVE_QUOTE_ENTRY', payload: updatedEntry as MockQuoteProductEntry });
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, [state.activeQuoteId]);

    const toggleAdditionalProduct = useCallback(async (productId: number) => {
        if (!state.activeQuoteId || !state.catalogContext.activeQuoteFull) return;
        dispatch({ type: 'START_LOADING' });
        try {
            const existingEntry = state.catalogContext.activeQuoteFull.product_entries.find(e => e.product_id === productId && e.role === ProductRole.ADDITIONAL);
            if (existingEntry) {
                 // @ts-ignore - Mock client
                await apiClient.deleteQuoteProductEntry(state.activeQuoteId, existingEntry.id);
                dispatch({type: 'REMOVE_ACTIVE_QUOTE_ENTRY', payload: existingEntry.id});
            } else {
                 // @ts-ignore - Mock client
                const newEntry = await apiClient.addQuoteProductEntry(state.activeQuoteId, productId, 1, ProductRole.ADDITIONAL);
                dispatch({type: 'ADD_ACTIVE_QUOTE_ENTRY', payload: newEntry as MockQuoteProductEntry});
            }
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, [state.activeQuoteId, state.catalogContext.activeQuoteFull]);
    
    const goToStep = useCallback((step: CatalogStepKey) => {
        dispatch({ type: 'SET_ACTIVE_STEP', payload: step });
    }, []);

    const calculateActiveQuote = useCallback(async () => {
        if (!state.activeQuoteId) return;
        dispatch({ type: 'START_LOADING' });
        try {
            const result = await apiClient.calculateQuote(state.activeQuoteId);
            dispatch({ type: 'SET_CALCULATED_QUOTE', payload: result });
            // Also update the quote list if status changed
            await fetchQuotes();
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' }); // This might be set by SET_CALCULATED_QUOTE too
        }
    }, [state.activeQuoteId, fetchQuotes]);

    const fetchCalculatedQuote = useCallback(async (quoteId: number) => {
        if (!quoteId) return;
        dispatch({ type: 'START_LOADING' });
        try {
            const result = await apiClient.getCalculatedQuote(quoteId);
            dispatch({ type: 'SET_CALCULATED_QUOTE', payload: result });
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, []);


    return (
        <QuoteProcessContext.Provider value={{ 
            ...state, 
            dispatch,
            fetchQuotes,
            createNewQuote,
            selectQuoteForEditing,
            selectCategory,
            selectProduct,
            updateProductQuantity,
            updateProductVariation,
            toggleAdditionalProduct,
            goToStep,
            calculateActiveQuote,
            fetchCalculatedQuote
        }}>
            {children}
        </QuoteProcessContext.Provider>
    );
};

export const useQuoteProcess = (): QuoteProcessContextType => {
    const context = useContext(QuoteProcessContext);
    if (context === undefined) {
        throw new Error('useQuoteProcess must be used within a QuoteProcessProvider');
    }
    return context;
};