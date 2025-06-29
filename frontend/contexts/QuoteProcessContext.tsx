import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { 
    CatalogStepKey, 
    CatalogContextState, 
    FullQuote, 
    ProductRole,
    MaterializedProductEntry,
    QuotePreview,
    QuoteType, // Added import
    CalculatedQuote
} from '../types';
import { apiClient } from '../services/api'; 
import { useNavigate } from 'react-router-dom';

interface QuoteProcessState {
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
    | { type: 'START_LOADING' }
    | { type: 'END_LOADING' }
    | { type: 'SET_ERROR'; payload: string | null }
    | { type: 'SET_QUOTES'; payload: QuotePreview[] }
    | { type: 'SET_ACTIVE_QUOTE_ID'; payload: number | null }
    | { type: 'SET_ACTIVE_STEP'; payload: CatalogStepKey }
    | { type: 'SET_SELECTED_CATEGORY'; payload: string | null }
    | { type: 'SET_ACTIVE_QUOTE_FULL'; payload: FullQuote | null }
    | { type: 'UPDATE_ACTIVE_QUOTE_ENTRY'; payload: MaterializedProductEntry }
    | { type: 'REMOVE_ACTIVE_QUOTE_ENTRY'; payload: number } // entryId
    | { type: 'ADD_ACTIVE_QUOTE_ENTRY'; payload: MaterializedProductEntry }
    | { type: 'TOGGLE_MODAL'; payload: boolean }
    | { type: 'SET_CALCULATED_QUOTE'; payload: CalculatedQuote | null};


const reducer = (state: QuoteProcessState, action: Action): QuoteProcessState => {
    switch (action.type) {
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
    createNewQuote: (name: string, description: string, type: QuoteType) => Promise<number | undefined>;
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
    const navigate = useNavigate();
    const [state, dispatch] = useReducer(reducer, initialState);
    const [showMainProductModal, setShowMainProductModal] = React.useState(false);
    const [pendingStep, setPendingStep] = React.useState<CatalogStepKey | null>(null);
    // Track which modal to show: 'main' | 'secondary' | null
    const [productModalType, setProductModalType] = React.useState<'main' | 'secondary' | null>(null);

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
                dispatch({ type: 'SET_ACTIVE_QUOTE_FULL', payload: activeQuoteData as FullQuote });
                // No need to dispatch SET_VIEW here, navigation will be handled by the router
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
            await fetchQuotes();
            dispatch({ type: 'TOGGLE_MODAL', payload: false });
            navigate(`/quote/${newQuote.id}`);
            return newQuote.id;
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, [fetchQuotes, navigate]);

    const selectCategory = useCallback((categoryName: string) => {
        dispatch({ type: 'SET_SELECTED_CATEGORY', payload: categoryName });
        dispatch({ type: 'SET_ACTIVE_STEP', payload: 'choose_main_product' });
    }, []);

    const selectProduct = useCallback(async (productId: number, role: ProductRole) => {
        if (!state.activeQuoteId) return;
        console.log("Selecting product:", productId, "for role:", role);
        // Enforce only one MAIN product on frontend
        if (role === ProductRole.MAIN && state.catalogContext.activeQuoteFull) {
            const hasMain = state.catalogContext.activeQuoteFull.product_entries.some(e => e.role === ProductRole.MAIN);
            if (hasMain) {
                dispatch({ type: 'SET_ERROR', payload: 'A main product already exists for this quote. Please remove it before adding a new one.' });
                return;
            }
        }
        dispatch({ type: 'START_LOADING' });
        try {
            // @ts-ignore - Mock client takes quantity and returns MaterializedProductEntry
            const newEntry = await apiClient.addQuoteProductEntry(state.activeQuoteId, productId, 1, role); // Default quantity 1
            dispatch({ type: 'ADD_ACTIVE_QUOTE_ENTRY', payload: newEntry as MaterializedProductEntry});
            const nextStep = role === ProductRole.MAIN ? 'configure_main' : 'configure_secondary';
            dispatch({ type: 'SET_ACTIVE_STEP', payload: nextStep });
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, [state.activeQuoteId, state.catalogContext.activeQuoteFull]);

    const updateProductQuantity = useCallback(async (entryId: number, quantity: number) => {
        if (!state.activeQuoteId) return;
        // No loading state for faster UI
        try {
            // @ts-ignore - Mock client
            const updatedEntry = await apiClient.updateQuoteProductEntry(entryId, { quantity });
            dispatch({ type: 'UPDATE_ACTIVE_QUOTE_ENTRY', payload: updatedEntry as MaterializedProductEntry });
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
            console.log("Updating variation for entryId:", entryId, "groupId:", groupId, "optionId:", optionId);
            const updatedEntry = await apiClient.setQuoteProductVariationOption(entryId, optionId);
            dispatch({ type: 'UPDATE_ACTIVE_QUOTE_ENTRY', payload: updatedEntry as MaterializedProductEntry });
            // reload display data if needed
            
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
                dispatch({type: 'ADD_ACTIVE_QUOTE_ENTRY', payload: newEntry as MaterializedProductEntry});
            }
        } catch (err) {
            dispatch({ type: 'SET_ERROR', payload: (err as Error).message });
        } finally {
            dispatch({ type: 'END_LOADING' });
        }
    }, [state.activeQuoteId, state.catalogContext.activeQuoteFull]);
    
    // Helper to check if main product is selected
    const isMainProductSelected = !!state.catalogContext.activeQuoteFull?.product_entries?.some(e => e.role === ProductRole.MAIN);
    // Helper to check if secondary product is selected
    const isSecondaryProductSelected = !!state.catalogContext.activeQuoteFull?.product_entries?.some(e => e.role === ProductRole.SECONDARY);

    // Handler for modal response
    const handleMainProductModalResponse = (deleteProduct: boolean) => {
        setShowMainProductModal(false);
        if (deleteProduct && state.catalogContext.activeQuoteFull) {
            let entryToRemove = null;
            if (productModalType === 'main') {
                entryToRemove = state.catalogContext.activeQuoteFull.product_entries.find(e => e.role === ProductRole.MAIN);
            } else if (productModalType === 'secondary') {
                entryToRemove = state.catalogContext.activeQuoteFull.product_entries.find(e => e.role === ProductRole.SECONDARY);
            }
            if (entryToRemove) {
                dispatch({ type: 'REMOVE_ACTIVE_QUOTE_ENTRY', payload: entryToRemove.id });
            }
            if (pendingStep) {
                dispatch({ type: 'SET_ACTIVE_STEP', payload: pendingStep });
                setPendingStep(null);
            }
        } else {
            setPendingStep(null);
        }
        setProductModalType(null);
    };

    // Enhanced goToStep
    const goToStep = useCallback((step: CatalogStepKey) => {
        // If clicking on first two steps and main product is selected, show modal
        if ((step === 'choose_category' || step === 'choose_main_product') && isMainProductSelected) {
            setPendingStep(step);
            setProductModalType('main');
            setShowMainProductModal(true);
            return;
        }
        if ((step === 'choose_secondary_product') && isSecondaryProductSelected) {
            setPendingStep(step);
            setProductModalType('secondary');
            setShowMainProductModal(true);
            return;
        }
        dispatch({ type: 'SET_ACTIVE_STEP', payload: step });
    }, [isMainProductSelected, isSecondaryProductSelected]);

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
            {/* Modal for main/secondary product already selected */}
            {showMainProductModal && (
                <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
                    <div className="bg-white p-6 rounded-lg shadow-lg max-w-sm w-full">
                        <h3 className="text-lg font-bold mb-2 text-slate-800">
                            {productModalType === 'main' ? 'Main product already selected' : 'Secondary product already selected'}
                        </h3>
                        <p className="mb-4 text-slate-700">Would you like to delete it?</p>
                        <div className="flex justify-end gap-2">
                            <button onClick={() => handleMainProductModalResponse(true)} className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">Yes</button>
                            <button onClick={() => handleMainProductModalResponse(false)} className="bg-slate-300 text-slate-800 px-4 py-2 rounded hover:bg-slate-400">No</button>
                        </div>
                    </div>
                </div>
            )}
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