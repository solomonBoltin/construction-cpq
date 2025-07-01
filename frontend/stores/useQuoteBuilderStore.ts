import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { FullQuote, MaterializedProductEntry, CalculatedQuote, QuoteBuilderStepKey, ProductRole, QuoteStatus } from '../types';
import { apiClient } from '../services/api';

interface QuoteBuilderStore {
  // State
  quote: FullQuote | null;
  activeStep: QuoteBuilderStepKey;
  selectedCategoryName: string | null;
  calculatedQuote: CalculatedQuote | null;
  isLoading: boolean;

  // Actions
  setLoading: (loading: boolean) => void;
  setQuote: (quote: FullQuote) => void;
  setStep: (step: QuoteBuilderStepKey) => void;
  selectCategory: (name: string) => void;
  updateEntry: (entryId: number, updates: Partial<MaterializedProductEntry>) => void;
  addEntry: (entry: MaterializedProductEntry) => void;
  setCalculatedQuote: (calculatedQuote: CalculatedQuote | null) => void;
  reset: () => void;
  initializeStep: () => void;

  // Async actions
  loadQuote: (quoteId: number, shouldInitializeStep?: boolean) => Promise<void>;
  selectProduct: (productId: number, role: string) => Promise<MaterializedProductEntry>;
  removeEntry: (entryId: number) => Promise<void>;
  updateProductQuantity: (entryId: number, quantity: number) => Promise<void>;
  updateProductVariation: (entryId: number, groupId: number, optionId: number) => Promise<void>;
  calculateQuote: () => Promise<void>;
  finalizeQuote: () => Promise<void>;
}

const initialState = {
  quote: null,
  activeStep: 'choose_category' as QuoteBuilderStepKey,
  selectedCategoryName: null,
  calculatedQuote: null,
  isLoading: false,
};

export const useQuoteBuilderStore = create<QuoteBuilderStore>()(
  immer((set, get) => ({
    ...initialState,

    // Sync actions
    setLoading: (loading) => set((state) => {
      state.isLoading = loading;
    }),

    setQuote: (quote) => set((state) => {
      state.quote = quote;
    }),

    setStep: (step) => set((state) => {
      state.activeStep = step;
    }),

    selectCategory: (name) => set((state) => {
      state.selectedCategoryName = name;
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
      if (quote.status === QuoteStatus.FINAL) {
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
    loadQuote: async (quoteId, shouldInitializeStep=false) => {
      const { setLoading, setQuote, initializeStep } = get();
      setLoading(true);
      
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
        if (shouldInitializeStep) 
          initializeStep();
      } catch (error) {
        console.error('Error loading quote:', error);
        throw error; // Re-throw for component to handle with toast
      } finally {
        setLoading(false);
      }
    },

    selectProduct: async (productId, role) => {
      const { quote, setLoading, addEntry } = get();
      if (!quote) throw new Error('No quote loaded');

      setLoading(true);

      try {
        const productEntry = await apiClient.addQuoteProductEntry(quote.id, productId, 1, role as any);
        addEntry(productEntry);
        // Return the entry so the caller can decide what to do next
        return productEntry;
      } catch (error) {
        console.error('Error selecting product:', error);
        throw error; // Re-throw for component to handle with toast
      } finally {
        setLoading(false);
      }
    },

    updateProductQuantity: async (entryId, quantity) => {
      const { updateEntry } = get();
      
      try {
        await apiClient.updateQuoteProductEntry(entryId, { quantity });
        updateEntry(entryId, { quantity_of_product_units: quantity });
      } catch (error) {
        console.error('Error updating product quantity:', error);
        throw error; // Re-throw for component to handle with toast
      }
    },

    updateProductVariation: async (entryId, _groupId, optionId) => {
      const { loadQuote, quote } = get();
      if (!quote) return;
      
      try {
        await apiClient.setQuoteProductVariationOption(entryId, optionId);
        // Reload the quote to get updated variation state
        await loadQuote(quote.id);
      } catch (error) {
        console.error('Error updating product variation:', error);
        throw error; // Re-throw for component to handle with toast
      }
    },

    calculateQuote: async () => {
      const { quote, setLoading, setCalculatedQuote } = get();
      if (!quote) return;

      setLoading(true);

      try {
        const calculatedQuote = await apiClient.calculateQuote(quote.id);
        setCalculatedQuote(calculatedQuote);
      } catch (error) {
        console.error('Error calculating quote:', error);
        throw error; // Re-throw for component to handle with toast
      } finally {
        setLoading(false);
      }
    },

    removeEntry: async (entryId) => {
      const { quote } = get();
      if (!quote) return;

      try {
        await apiClient.deleteQuoteProductEntry(quote.id, entryId);
        
        // Remove from local state
        set((state) => {
          if (state.quote?.product_entries) {
            state.quote.product_entries = state.quote.product_entries.filter(e => e.id !== entryId);
          }
        });
      } catch (error) {
        console.error('Error removing entry:', error);
        throw error; // Re-throw for component to handle with toast
      }
    },

    finalizeQuote: async () => {
      const { quote, setLoading } = get();
      if (!quote) throw new Error('No quote loaded');

      setLoading(true);

      try {
        const updatedQuote = await apiClient.setQuoteStatus(quote.id, QuoteStatus.FINAL);
        
        // Update the quote in the store
        set((state) => {
          if (state.quote) {
            state.quote.status = updatedQuote.status;
          }
        });
      } catch (error) {
        console.error('Error finalizing quote:', error);
        throw error; // Re-throw for component to handle with toast
      } finally {
        setLoading(false);
      }
    },
  }))
);
