import React from 'react';
import { PDFGenerationButtons } from './PDFGenerationButtons';

/**
 * Example integration showing how to use PDF generation in a quote view
 */

interface ExampleQuoteViewProps {
  quoteId: number;
  quoteName: string;
  quoteData?: {
    description: string;
    status: string;
    totalAmount: number;
  };
}

export const ExampleQuoteView: React.FC<ExampleQuoteViewProps> = ({
  quoteId,
  quoteName,
  quoteData
}) => {
  return (
    <div className="quote-view-page">
      <div className="quote-header">
        <h1>{quoteName}</h1>
        {quoteData && (
          <div className="quote-meta">
            <p><strong>Description:</strong> {quoteData.description}</p>
            <p><strong>Status:</strong> {quoteData.status}</p>
            <p><strong>Total:</strong> ${quoteData.totalAmount.toFixed(2)}</p>
          </div>
        )}
      </div>

      <div className="quote-content">
        {/* Quote content would go here */}
        <p>Quote details, products, materials, etc.</p>
      </div>

      <div className="quote-actions">
        <h3>Actions</h3>
        <PDFGenerationButtons 
          quoteId={quoteId}
          quoteName={quoteName}
          className="pdf-actions"
        />
      </div>
    </div>
  );
};

/**
 * Example usage:
 * 
 * <ExampleQuoteView 
 *   quoteId={123}
 *   quoteName="Construction Quote - Main Building"
 *   quoteData={{
 *     description: "Foundation and framing work",
 *     status: "Draft",
 *     totalAmount: 25000.00
 *   }}
 * />
 */