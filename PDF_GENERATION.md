# PDF Generation Feature

This document describes the PDF generation functionality added to the Construction CPQ system.

## Overview

The PDF generation feature allows users to generate professional PDF documents from construction quotes. The feature includes:

- Backend PDF generation service using ReportLab
- API endpoints for generating PDFs
- Frontend components for easy PDF generation
- Support for both download and inline viewing

## Backend Implementation

### Dependencies
- `reportlab` - Python library for PDF generation

### Components

#### 1. PDF Generation Service (`app/services/pdf_generator.py`)
- **Class**: `PDFGenerator`
- **Purpose**: Creates PDF documents from quote data
- **Key Features**:
  - Professional layout with headers, tables, and formatting
  - Includes quote information, bill of materials, applied rates, and totals
  - Handles missing data gracefully
  - Uses ReportLab for PDF generation

#### 2. API Endpoints (`app/api/pdf_generation.py`)
- **Base URL**: `/api/v1/pdf`
- **Endpoints**:
  - `GET /quotes/{quote_id}` - Generate PDF for download
  - `GET /quotes/{quote_id}/inline` - Generate PDF for inline viewing

### API Usage

```bash
# Download PDF
curl -X GET "http://localhost:8000/api/v1/pdf/quotes/1" \
  -H "Accept: application/pdf" \
  -o quote_1.pdf

# View PDF inline
curl -X GET "http://localhost:8000/api/v1/pdf/quotes/1/inline" \
  -H "Accept: application/pdf"
```

## Frontend Implementation

### Components

#### 1. PDF Generation Buttons (`components/PDFGenerationButtons.tsx`)
- **Purpose**: Provides UI buttons for PDF generation
- **Features**:
  - Download PDF button
  - View PDF button (opens in new tab)
  - Loading states
  - Error handling

#### 2. PDF Generation Hook (`hooks/usePDFGeneration.ts`)
- **Purpose**: Manages PDF generation logic and state
- **Features**:
  - `generateAndDownloadPDF()` - Downloads PDF file
  - `generateAndOpenPDF()` - Opens PDF in new tab
  - Loading and error state management

#### 3. PDF Utilities (`utils/pdf.ts`)
- **Purpose**: Utility functions for PDF handling
- **Features**:
  - `downloadPDF()` - Downloads blob as file
  - `openPDFInNewTab()` - Opens PDF in new tab
  - `generateQuotePDFFilename()` - Creates standardized filename

### API Client Integration

The PDF generation functions are integrated into the existing `quoteProcessClient`:

```typescript
// Generate PDF for download
const blob = await apiClient.generateQuotePDF(quoteId);

// Generate PDF for inline viewing
const blob = await apiClient.generateQuotePDFInline(quoteId);
```

## Usage Example

```tsx
import React from 'react';
import { PDFGenerationButtons } from '../components/PDFGenerationButtons';

const QuoteViewPage: React.FC = () => {
  const quoteId = 1;
  const quoteName = "My Construction Quote";

  return (
    <div>
      <h1>{quoteName}</h1>
      {/* Quote content */}
      
      <PDFGenerationButtons 
        quoteId={quoteId} 
        quoteName={quoteName}
        className="my-custom-class"
      />
    </div>
  );
};
```

## PDF Content Structure

The generated PDF includes:

1. **Header**: "Construction Quote" title
2. **Quote Information**:
   - Quote ID
   - Quote Name
   - Description
   - Quote Type
   - Status
   - Created Date
   - Calculated Date

3. **Bill of Materials** (if available):
   - Material name
   - Quantity
   - Unit cost
   - Total cost
   - Unit type

4. **Applied Rates & Fees** (if available):
   - Rate type
   - Rate percentage/amount
   - Applied to amount
   - Calculated amount

5. **Quote Summary**:
   - Total material cost
   - Total labor cost
   - Cost of goods sold
   - Subtotal before tax
   - Tax amount
   - **Final price** (highlighted)

## Error Handling

The system handles various error conditions:

- Quote not found (404 error)
- PDF generation failures (500 error)
- Network errors
- Malformed data

## Testing

Tests are included in `backend/tests/test_pdf_generation.py`:
- PDF generator initialization
- Quote not found handling
- Successful PDF generation
- PDF content validation

## Security Considerations

- PDF generation requires valid quote access
- No sensitive data is logged during PDF generation
- PDF files are generated in memory and not stored on disk
- All PDF generation uses secure ReportLab functions

## Performance

- PDFs are generated on-demand
- No caching is implemented (consider adding for high-traffic scenarios)
- Memory usage is minimal as PDFs are generated in memory buffers
- Large quotes may require longer generation times

## Future Enhancements

Potential improvements for the PDF generation feature:

1. **Customization**: Allow users to customize PDF layout and branding
2. **Templates**: Support for multiple PDF templates
3. **Batch Generation**: Generate PDFs for multiple quotes
4. **Caching**: Cache generated PDFs to improve performance
5. **Email Integration**: Send PDFs via email
6. **Watermarks**: Add watermarks for draft quotes
7. **Digital Signatures**: Support for digital signatures
8. **Internationalization**: Support for multiple languages