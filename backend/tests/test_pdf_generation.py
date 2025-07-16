import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime, timezone

from app.services.pdf_generator import PDFGenerator
from app.models import Quote, CalculatedQuote, QuoteType, QuoteStatus, BillOfMaterialEntry


class TestPDFGenerator:
    """Test the PDF generation service."""
    
    def test_pdf_generator_initialization(self):
        """Test that PDF generator can be initialized."""
        session = Mock()
        pdf_generator = PDFGenerator(session)
        assert pdf_generator.session == session
        assert pdf_generator.quote_calculator is not None
    
    @patch('app.services.pdf_generator.QuoteCalculator')
    def test_generate_quote_pdf_quote_not_found(self, mock_calculator):
        """Test PDF generation when quote is not found."""
        session = Mock()
        session.get.return_value = None
        
        pdf_generator = PDFGenerator(session)
        
        with pytest.raises(ValueError, match="Quote with ID 1 not found"):
            pdf_generator.generate_quote_pdf(1)
    
    @patch('app.services.pdf_generator.QuoteCalculator')
    def test_generate_quote_pdf_success(self, mock_calculator):
        """Test successful PDF generation."""
        session = Mock()
        
        # Mock quote
        quote = Mock(spec=Quote)
        quote.id = 1
        quote.name = "Test Quote"
        quote.description = "Test description"
        quote.quote_type = QuoteType.GENERAL
        quote.status = QuoteStatus.DRAFT
        quote.created_at = datetime.now(timezone.utc)
        
        # Mock calculated quote
        calculated_quote = Mock(spec=CalculatedQuote)
        calculated_quote.bill_of_materials_json = [
            BillOfMaterialEntry(
                material_name="Test Material",
                quantity=Decimal("10.00"),
                unit_cost=Decimal("5.00"),
                total_cost=Decimal("50.00"),
                unit_name="units"
            )
        ]
        calculated_quote.total_material_cost = Decimal("50.00")
        calculated_quote.total_labor_cost = Decimal("100.00")
        calculated_quote.cost_of_goods_sold = Decimal("150.00")
        calculated_quote.subtotal_before_tax = Decimal("195.00")
        calculated_quote.tax_amount = Decimal("19.50")
        calculated_quote.final_price = Decimal("214.50")
        calculated_quote.calculated_at = datetime.now(timezone.utc)
        calculated_quote.applied_rates_info_json = []
        
        session.get.return_value = quote
        mock_calculator.return_value.calculate_and_save_quote.return_value = calculated_quote
        
        pdf_generator = PDFGenerator(session)
        pdf_bytes = pdf_generator.generate_quote_pdf(1)
        
        # Verify PDF was generated
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # Verify it starts with PDF header
        assert pdf_bytes.startswith(b'%PDF-')
        
        # Verify session was called correctly
        session.get.assert_called_once_with(Quote, 1)
        
        # Verify calculator was called correctly
        mock_calculator.return_value.calculate_and_save_quote.assert_called_once_with(1, session)