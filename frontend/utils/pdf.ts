/**
 * Utility functions for handling PDF downloads and operations
 */

export const downloadPDF = (blob: Blob, filename: string): void => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
};

export const openPDFInNewTab = (blob: Blob): void => {
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank');
    // Note: URL will be cleaned up when the tab is closed
};

export const generateQuotePDFFilename = (quoteId: number, quoteName?: string): string => {
    const name = quoteName ? quoteName.replace(/[^a-zA-Z0-9]/g, '_') : 'quote';
    return `${name}_${quoteId}.pdf`;
};