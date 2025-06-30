import { useState, useCallback } from 'react';
import { apiClient } from '../services/api';
import { CalculatedQuote } from '../types';

// Custom hook for quote calculation logic
export const useQuoteCalculation = () => {
    const [calculatedQuote, setCalculatedQuote] = useState<CalculatedQuote | null>(null);
    const [isCalculating, setIsCalculating] = useState(false);
    const [calculationError, setCalculationError] = useState<string | null>(null);

    const calculateQuote = useCallback(async (quoteId: number) => {
        setIsCalculating(true);
        setCalculationError(null);
        
        try {
            const result = await apiClient.calculateQuote(quoteId);
            setCalculatedQuote(result);
            return { success: true as const, data: result };
        } catch (error) {
            const errorMessage = (error as Error).message;
            setCalculationError(errorMessage);
            return { success: false as const, error: errorMessage };
        } finally {
            setIsCalculating(false);
        }
    }, []);

    const clearCalculation = useCallback(() => {
        setCalculatedQuote(null);
        setCalculationError(null);
    }, []);

    return {
        calculatedQuote,
        isCalculating,
        calculationError,
        calculateQuote,
        clearCalculation,
    };
};
