import html2pdf from 'html2pdf.js';

export interface PDFExportOptions {
  filename?: string;
  format?: 'a4' | 'letter';
  orientation?: 'portrait' | 'landscape';
  margin?: number;
}

export const generatePDFFromElement = async (
  element: HTMLElement,
  options: PDFExportOptions = {}
): Promise<void> => {
  const {
    filename = 'quote-document.pdf',
    format = 'a4',
    orientation = 'portrait',
    margin = 0.5
  } = options;

  const opt = {
    margin: margin,
    filename: filename,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { 
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#ffffff'
    },
    jsPDF: { 
      unit: 'in', 
      format: format, 
      orientation: orientation
    }
  };

  try {
    await html2pdf().set(opt).from(element).save();
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw new Error('Failed to generate PDF document');
  }
};

export const generateQuotePDF = async (
  quoteElement: HTMLElement,
  quoteName?: string
): Promise<void> => {
  const sanitizedName = quoteName 
    ? quoteName.replace(/[^a-zA-Z0-9\s\-_]/g, '').trim()
    : 'Quote';
  
  const timestamp = new Date().toISOString().split('T')[0];
  const filename = `${sanitizedName}_${timestamp}.pdf`;

  return generatePDFFromElement(quoteElement, {
    filename,
    format: 'a4',
    orientation: 'portrait',
    margin: 0.5
  });
};