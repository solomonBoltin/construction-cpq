from decimal import Decimal
from typing import Optional, BinaryIO
from datetime import datetime
import io
import logging

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from sqlmodel import Session

from app.models import Quote, CalculatedQuote, BillOfMaterialEntry, AppliedRateInfoEntry
from app.services.quote_calculator import QuoteCalculator

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Service for generating PDF documents from quotes."""
    
    def __init__(self, session: Session):
        self.session = session
        self.quote_calculator = QuoteCalculator()
        
    def generate_quote_pdf(self, quote_id: int) -> bytes:
        """Generate a PDF for a quote and return the bytes."""
        # Get the quote
        quote = self.session.get(Quote, quote_id)
        if not quote:
            raise ValueError(f"Quote with ID {quote_id} not found")
            
        # Get or calculate the quote totals
        calculated_quote = self.quote_calculator.calculate_and_save_quote(quote_id, self.session)
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build the PDF content
        story = []
        styles = getSampleStyleSheet()
        
        # Add custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#2E3A59')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=HexColor('#2E3A59')
        )
        
        # Title
        story.append(Paragraph("Construction Quote", title_style))
        story.append(Spacer(1, 20))
        
        # Quote information
        self._add_quote_info(story, quote, calculated_quote, styles)
        story.append(Spacer(1, 20))
        
        # Bill of materials
        if calculated_quote.bill_of_materials_json:
            story.append(Paragraph("Bill of Materials", heading_style))
            story.append(Spacer(1, 10))
            self._add_bill_of_materials(story, calculated_quote.bill_of_materials_json, styles)
            story.append(Spacer(1, 20))
        
        # Applied rates
        if calculated_quote.applied_rates_info_json:
            story.append(Paragraph("Applied Rates & Fees", heading_style))
            story.append(Spacer(1, 10))
            self._add_applied_rates(story, calculated_quote.applied_rates_info_json, styles)
            story.append(Spacer(1, 20))
        
        # Totals
        story.append(Paragraph("Quote Summary", heading_style))
        story.append(Spacer(1, 10))
        self._add_quote_totals(story, calculated_quote, styles)
        
        # Build PDF
        doc.build(story)
        
        # Get the PDF bytes
        buffer.seek(0)
        return buffer.read()
    
    def _add_quote_info(self, story, quote: Quote, calculated_quote: CalculatedQuote, styles):
        """Add quote information section."""
        data = [
            ['Quote ID:', str(quote.id)],
            ['Quote Name:', quote.name or 'Unnamed Quote'],
            ['Description:', quote.description or 'No description'],
            ['Quote Type:', quote.quote_type.value],
            ['Status:', quote.status.value],
            ['Created:', quote.created_at.strftime('%Y-%m-%d %H:%M')],
            ['Calculated:', calculated_quote.calculated_at.strftime('%Y-%m-%d %H:%M')],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    
    def _add_bill_of_materials(self, story, bill_of_materials: list[BillOfMaterialEntry], styles):
        """Add bill of materials table."""
        # Header
        data = [['Material', 'Quantity', 'Unit Cost', 'Total Cost', 'Unit']]
        
        # Data rows
        for item in bill_of_materials:
            data.append([
                item.material_name,
                str(item.quantity),
                f"${item.unit_cost:.2f}",
                f"${item.total_cost:.2f}",
                item.unit_name or 'unit'
            ])
        
        table = Table(data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    
    def _add_applied_rates(self, story, applied_rates: list[AppliedRateInfoEntry], styles):
        """Add applied rates table."""
        # Header
        data = [['Rate Type', 'Rate', 'Applied To', 'Amount']]
        
        # Data rows
        for rate in applied_rates:
            data.append([
                rate.rate_type,
                f"{rate.rate:.2%}" if rate.rate < 1 else f"{rate.rate:.2f}",
                f"${rate.applied_to:.2f}",
                f"${rate.amount:.2f}"
            ])
        
        table = Table(data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    
    def _add_quote_totals(self, story, calculated_quote: CalculatedQuote, styles):
        """Add quote totals section."""
        data = [
            ['Total Material Cost:', f"${calculated_quote.total_material_cost:.2f}"],
            ['Total Labor Cost:', f"${calculated_quote.total_labor_cost:.2f}"],
            ['Cost of Goods Sold:', f"${calculated_quote.cost_of_goods_sold:.2f}"],
            ['Subtotal (before tax):', f"${calculated_quote.subtotal_before_tax:.2f}"],
            ['Tax Amount:', f"${calculated_quote.tax_amount:.2f}"],
            ['', ''],  # Empty row for spacing
            ['FINAL PRICE:', f"${calculated_quote.final_price:.2f}"],
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
        ]))
        
        story.append(table)