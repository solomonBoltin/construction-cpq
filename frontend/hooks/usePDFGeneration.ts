import { useState } from 'react';
import { apiClient } from '../services/api';
import { downloadPDF, openPDFInNewTab, generateQuotePDFFilename } from '../utils/pdf';

interface UsePDFGenerationProps {
    quoteId: number;
    quoteName?: string;
}

export const usePDFGeneration = ({ quoteId, quoteName }: UsePDFGenerationProps) => {
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const generateAndDownloadPDF = async () => {
        setIsGenerating(true);
        setError(null);
        
        try {
            const blob = await apiClient.generateQuotePDF(quoteId);
            const filename = generateQuotePDFFilename(quoteId, quoteName);
            downloadPDF(blob, filename);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to generate PDF');
        } finally {
            setIsGenerating(false);
        }
    };

    const generateAndOpenPDF = async () => {
        setIsGenerating(true);
        setError(null);
        
        try {
            const blob = await apiClient.generateQuotePDFInline(quoteId);
            openPDFInNewTab(blob);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to generate PDF');
        } finally {
            setIsGenerating(false);
        }
    };

    const clearError = () => {
        setError(null);
    };

    return {
        generateAndDownloadPDF,
        generateAndOpenPDF,
        isGenerating,
        error,
        clearError,
    };
};