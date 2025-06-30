import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { FullQuote, MaterializedProductEntry, CalculatedQuote, QuoteBuilderStepKey, ProductRole, QuoteStatus } from '../types';
import { apiClient } from '../services/api';
import { handleApiError } from '../utils/errors';

interface QuoteBuilderStore {
  // State
  quote: FullQuote | null;
  activeStep: QuoteBuilderStepKey;
  selectedCategoryName: string | null;
  calculatedQuote: CalculatedQuote | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setQuote: (quote: FullQuote) => void;
  setStep: (step: QuoteBuilderStepKey) => void;
  selectCategory: (name: string) => void;
  updateEntry: (entryId: number, updates: Partial<MaterializedProductEntry>) => void;
  addEntry: (entry: MaterializedProductEntry) => void;
  removeEntry: (entryId: number) => void;
  setCalculatedQuote: (calculatedQuote: CalculatedQuote | null) => void;
  reset: () => void;
  initializeStep: () => void;

  // Async actions
  loadQuote: (quoteId: number) => Promise<void>;
  selectProduct: (productId: number, role: string) => Promise<MaterializedProductEntry>;
  updateProductQuantity: (entryId: number, quantity: number) => Promise<void>;
  updateProductVariation: (entryId: number, groupId: number, optionId: number) => Promise<void>;
  calculateQuote: () => Promise<void>;
}

const initialState = {
  quote: null,
  activeStep: 'choose_category' as QuoteBuilderStepKey,
  selectedCategoryName: null,
  calculatedQuote: null,
  isLoading: false,
  error: null,
};

export const useQuoteBuilderStore = create<QuoteBuilderStore>()(
  immer((set, get) => ({
    ...initialState,

    // Sync actions
    setLoading: (loading) => set((state) => {
      state.isLoading = loading;
    }),

    setError: (error) => set((state) => {
      state.error = error;
    }),

    setQuote: (quote) => set((state) => {
      state.quote = quote;
    }),

    setStep: (step) => set((state) => {
      state.activeStep = step;
    }),

    selectCategory: (name) => set((state) => {
      state.selectedCategoryName = name;
      // Remove automatic navigation - let useStepNavigation handle it
    }),

    updateEntry: (entryId, updates) => set((state) => {
      if (state.quote?.product_entries) {
        const entryIndex = state.quote.product_entries.findIndex(e => e.id === entryId);
        if (entryIndex !== -1) {
          Object.assign(state.quote.product_entries[entryIndex], updates);
        }
      }
    }),

    addEntry: (entry) => set((state) => {
      if (state.quote) {
        if (!state.quote.product_entries) {
          state.quote.product_entries = [];
        }
        state.quote.product_entries.push(entry);
      }
    }),

    removeEntry: (entryId) => set((state) => {
      if (state.quote?.product_entries) {
        state.quote.product_entries = state.quote.product_entries.filter(e => e.id !== entryId);
      }
    }),

    setCalculatedQuote: (calculatedQuote) => set((state) => {
      state.calculatedQuote = calculatedQuote;
    }),

    reset: () => set(() => ({ ...initialState })),

    // Initialize step based on quote data
    initializeStep: () => {
      const { quote, setStep } = get();
      if (!quote) {
        setStep('choose_category');
        return;
      }

      const mainEntry = quote.product_entries?.find(e => e.role === ProductRole.MAIN);
      const secondaryEntry = quote.product_entries?.find(e => e.role === ProductRole.SECONDARY);
      const hasAdditional = quote.product_entries?.some(e => e.role === ProductRole.ADDITIONAL);

      // If quote is finalized, go to review
      if (quote.status === QuoteStatus.FINAL || quote.status === QuoteStatus.FINALIZED) {
        setStep('review');
        return;
      }

      // Work backwards to find the appropriate step
      if (secondaryEntry && secondaryEntry.quantity_of_product_units > 0) {
        // Secondary is configured
        if (hasAdditional) {
          setStep('review');
        } else {
          setStep('select_additional');
        }
      } else if (secondaryEntry) {
        // Secondary exists but not configured
        setStep('configure_secondary');
      } else if (mainEntry && mainEntry.quantity_of_product_units > 0) {
        // Main is configured
        setStep('choose_secondary_product');
      } else if (mainEntry) {
        // Main exists but not configured
        setStep('configure_main');
      } else {
        // No products selected
        setStep('choose_category');
      }
    },

    // Async actions
    loadQuote: async (quoteId) => {
      const { setLoading, setError, setQuote, initializeStep } = get();
      setLoading(true);
      setError(null);
      
      try {
        const quote = await apiClient.getQuoteFull(quoteId);
        setQuote(quote);

        // Try to load calculated quote if it exists
        try {
          const calculatedQuote = await apiClient.getCalculatedQuote(quoteId);
          if (calculatedQuote) {
            set((state) => {
              state.calculatedQuote = calculatedQuote;
            });
          }
        } catch (calcError) {
          console.warn('No calculated quote found:', calcError);
        }

        // Initialize the step based on quote data
        initializeStep();
      } catch (error) {
        setError(handleApiError(error));
      } finally {
        setLoading(false);
      }
    },

    selectProduct: async (productId, role) => {
      const { quote, setLoading, setError, addEntry } = get();
      if (!quote) throw new Error('No quote loaded');

      setLoading(true);
      setError(null);

      try {
        const productEntry = await apiClient.addQuoteProductEntry(quote.id, productId, 1, role as any);
        addEntry(productEntry);
        // Return the entry so the caller can decide what to do next
        return productEntry;
      } catch (error) {
        setError(handleApiError(error));
        throw error;
      } finally {
        setLoading(false);
      }
    },

    updateProductQuantity: async (entryId, quantity) => {
      const { setError, updateEntry } = get();
      
      try {
        await apiClient.updateQuoteProductEntry(entryId, { quantity });
        updateEntry(entryId, { quantity_of_product_units: quantity });
      } catch (error) {
        setError(handleApiError(error));
      }
    },

    updateProductVariation: async (entryId, _groupId, optionId) => {
      const { setError, loadQuote, quote } = get();
      if (!quote) return;
      
      try {
        await apiClient.setQuoteProductVariationOption(entryId, optionId);
        // Reload the quote to get updated variation state
        await loadQuote(quote.id);
      } catch (error) {
        setError(handleApiError(error));
      }
    },

    calculateQuote: async () => {
      const { quote, setLoading, setError, setCalculatedQuote } = get();
      if (!quote) return;

      setLoading(true);
      setError(null);

      try {
        const calculatedQuote = await apiClient.calculateQuote(quote.id);
        setCalculatedQuote(calculatedQuote);
      } catch (error) {
        setError(handleApiError(error));
      } finally {
        setLoading(false);
      }
    },
  }))
);
