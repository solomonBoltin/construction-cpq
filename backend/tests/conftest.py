import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from sqlmodel import Session
from typing import Dict, Callable

from app.services.quote_calculator import final_quantize_decimal
from app.models import CalculatedQuote, QuoteConfig


def D(value: str) -> Decimal:
    return Decimal(value)

@pytest.fixture
def mock_session() -> MagicMock:
    session = MagicMock(spec=Session)
    session.get.return_value = MagicMock()

    def exec_side_effect(*args, **kwargs):
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None
        mock_exec_result.all.return_value = []
        mock_exec_result.one.return_value = MagicMock()
        return mock_exec_result
        
    session.exec.side_effect = exec_side_effect
    session.refresh.return_value = None
    session.commit.return_value = None
    session.add.return_value = None
    session.delete.return_value = None

    return session

@pytest.fixture
def quote_calculator_service():
    from app.services.quote_calculator import QuoteCalculator
    return QuoteCalculator()

@pytest.fixture
def D_fixture():
    return D

# Helper for consistent decimal quantization in assertions
def _conftest_final_quantize_decimal(value: Decimal) -> Decimal:
    return final_quantize_decimal(value)

def assert_decimal_equal_conftest(
    actual: Decimal, 
    expected: Decimal, 
    D_fixture: Callable[[str], Decimal], 
    msg: str = ""
):
    """Asserts two decimals are equal after final quantization."""
    quantized_actual = _conftest_final_quantize_decimal(actual)
    quantized_expected = _conftest_final_quantize_decimal(expected)
    assert quantized_actual == quantized_expected, \
        f"{msg} Expected: {quantized_expected}, Got: {quantized_actual}. Original expected: {expected}, original actual: {actual}."

def assert_calculated_quote_financial_details(
    calculated_quote: CalculatedQuote,
    expected_total_material_cost: Decimal,
    expected_total_labor_cost: Decimal,
    expected_cogs: Decimal,
    quote_config: QuoteConfig, # Pass QuoteConfig for fee calculation
    D_fixture: Callable[[str], Decimal]
):
    """Asserts the core financial details and calculated fees of a CalculatedQuote object."""
    assert calculated_quote is not None, "CalculatedQuote should not be None"

    assert_decimal_equal_conftest(calculated_quote.total_material_cost, expected_total_material_cost, D_fixture, "Total Material Cost")
    assert_decimal_equal_conftest(calculated_quote.total_labor_cost, expected_total_labor_cost, D_fixture, "Total Labor Cost")
    assert_decimal_equal_conftest(calculated_quote.cost_of_goods_sold, expected_cogs, D_fixture, "COGS")

    # Calculate expected fees based on COGS and QuoteConfig
    expected_commission = expected_cogs * quote_config.sales_commission_rate
    expected_franchise_fee = expected_cogs * quote_config.franchise_fee_rate
    
    cost_base = expected_cogs + expected_commission + expected_franchise_fee
    # Ensure "1" is also a Decimal for precision with D_fixture
    # Use D_fixture directly for "1" to ensure it's a Decimal of the correct context if necessary,
    # or rely on D() from conftest if D_fixture is just a pass-through for that.
    one_decimal = D_fixture("1") if D_fixture else D("1") 
    expected_margin = (cost_base * quote_config.margin_rate) / (one_decimal - quote_config.margin_rate)
    expected_subtotal = cost_base + expected_margin
    expected_tax = expected_subtotal * quote_config.tax_rate
    expected_final_price = expected_subtotal + expected_tax

    assert_decimal_equal_conftest(calculated_quote.subtotal_before_tax, expected_subtotal, D_fixture, "Subtotal Before Tax")
    assert_decimal_equal_conftest(calculated_quote.tax_amount, expected_tax, D_fixture, "Tax Amount")
    assert_decimal_equal_conftest(calculated_quote.final_price, expected_final_price, D_fixture, "Final Price")

    # Validate applied rates info
    assert calculated_quote.applied_rates_info_json is not None, "applied_rates_info_json should not be None"
    
    expected_applied_rates_details = {
        "Sales Commission": expected_commission,
        "Franchise Fee": expected_franchise_fee,
        "Margin": expected_margin
    }
    assert len(calculated_quote.applied_rates_info_json) == len(expected_applied_rates_details), \
        f"Number of applied rates mismatch. Expected: {len(expected_applied_rates_details)}, Got: {len(calculated_quote.applied_rates_info_json)}"
    
    actual_applied_rates = {rate.name: rate.applied_amount for rate in calculated_quote.applied_rates_info_json}
    
    for name, expected_amount in expected_applied_rates_details.items():
        assert name in actual_applied_rates, f"Expected rate '{name}' not found in applied rates. Available: {list(actual_applied_rates.keys())}"
        assert_decimal_equal_conftest(actual_applied_rates[name], expected_amount, D_fixture, f"Applied Rate Amount for '{name}'")
