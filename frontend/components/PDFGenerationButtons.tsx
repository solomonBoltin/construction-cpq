import React from 'react';
import { usePDFGeneration } from '../hooks/usePDFGeneration';

interface PDFGenerationButtonsProps {
    quoteId: number;
    quoteName?: string;
    className?: string;
}

export const PDFGenerationButtons: React.FC<PDFGenerationButtonsProps> = ({ 
    quoteId, 
    quoteName, 
    className = '' 
}) => {
    const { 
        generateAndDownloadPDF, 
        generateAndOpenPDF, 
        isGenerating, 
        error, 
        clearError 
    } = usePDFGeneration({ quoteId, quoteName });

    return (
        <div className={`pdf-generation-buttons ${className}`}>
            <div className="button-group">
                <button 
                    onClick={generateAndDownloadPDF}
                    disabled={isGenerating}
                    className="btn btn-primary"
                    style={{
                        marginRight: '8px',
                        padding: '8px 16px',
                        backgroundColor: isGenerating ? '#cccccc' : '#007bff',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: isGenerating ? 'not-allowed' : 'pointer',
                    }}
                >
                    {isGenerating ? 'Generating...' : 'Download PDF'}
                </button>
                
                <button 
                    onClick={generateAndOpenPDF}
                    disabled={isGenerating}
                    className="btn btn-secondary"
                    style={{
                        padding: '8px 16px',
                        backgroundColor: isGenerating ? '#cccccc' : '#6c757d',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: isGenerating ? 'not-allowed' : 'pointer',
                    }}
                >
                    {isGenerating ? 'Generating...' : 'View PDF'}
                </button>
            </div>
            
            {error && (
                <div 
                    className="error-message"
                    style={{
                        marginTop: '8px',
                        padding: '8px',
                        backgroundColor: '#f8d7da',
                        color: '#721c24',
                        borderRadius: '4px',
                        border: '1px solid #f5c6cb',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                    }}
                >
                    <span>{error}</span>
                    <button 
                        onClick={clearError}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: '#721c24',
                            cursor: 'pointer',
                            fontSize: '16px',
                            marginLeft: '8px',
                        }}
                    >
                        ×
                    </button>
                </div>
            )}
        </div>
    );
};