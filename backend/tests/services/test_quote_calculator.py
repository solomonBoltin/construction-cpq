# Placeholder for quote calculator unit tests

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.models import (
    Material,
    UnitType,
    Quote,
    QuoteConfig,
    QuoteProductEntry,
    Product,
    ProductMaterial,
    VariationOption,
    VariationOptionMaterial,
    CalculatedQuote,
    BillOfMaterialEntry,
    AppliedRateInfoEntry,
)
from app.services.quote_calculator import QuoteCalculator, quantize_decimal, final_quantize_decimal

# Helper to create Decimal with consistent precision for tests
def D(value: str) -> Decimal:
    return Decimal(value)

@pytest.fixture
def quote_calculator():
    return QuoteCalculator()

@pytest.fixture
def mock_session():
    return MagicMock()

# --- Tests for _get_material_cost_per_base_unit ---
def test_get_material_cost_per_base_unit_valid(quote_calculator):
    material = Material(
        cost_per_supplier_unit=D("10.0"),
        quantity_in_supplier_unit=D("5.0"),
        # ... other fields
    )
    expected_cost = D("2.0")
    assert quote_calculator._get_material_cost_per_base_unit(material) == expected_cost

def test_get_material_cost_per_base_unit_zero_quantity(quote_calculator):
    material = Material(
        cost_per_supplier_unit=D("10.0"),
        quantity_in_supplier_unit=D("0"),
        # ... other fields
    )
    expected_cost = D("0")
    assert quote_calculator._get_material_cost_per_base_unit(material) == expected_cost

def test_get_material_cost_per_base_unit_zero_cost(quote_calculator):
    material = Material(
        cost_per_supplier_unit=D("0"),
        quantity_in_supplier_unit=D("5.0"),
        # ... other fields
    )
    expected_cost = D("0")
    assert quote_calculator._get_material_cost_per_base_unit(material) == expected_cost


# --- Tests for calculate_and_save_quote ---

def test_calculate_and_save_quote_simple_product_no_variations_no_fees(quote_calculator, mock_session):
    # --- Mock Data Setup ---
    mock_base_unit_type = UnitType(id=1, name="kg", abbreviation="kg")
    
    mock_material_1 = Material(
        id=1, name="Steel",
        cost_per_supplier_unit=D("100"), quantity_in_supplier_unit=D("10"), # Cost per base unit = 10
        base_unit_type_id=1, base_unit_type=mock_base_unit_type,
        # ... other necessary fields
    )
    
    mock_product_1 = Product(
        id=1, name="Basic Widget",
        base_labor_cost_per_product_unit=D("50"),
        product_materials=[
            ProductMaterial(id=1, product_id=1, material_id=1, material=mock_material_1, quantity_of_material_base_units_per_product_unit=D("2")), # Needs 2 kg of Steel
        ],
        # ... other necessary fields
    )
    
    mock_quote_entry_1 = QuoteProductEntry(
        id=1, quote_id=1, product_id=1, product=mock_product_1,
        quantity_of_product_units=D("3"), # 3 Basic Widgets
        selected_variations=[],
        # ... other necessary fields
    )
    
    mock_quote_config = QuoteConfig(
        id=1, name="Standard Config No Fees",
        sales_commission_rate=D("0"),
        franchise_fee_rate=D("0"),
        margin_rate=D("0"),
        additional_fixed_fees=D("0"),
        tax_rate=D("0"),
        # ... other necessary fields
    )
    
    mock_quote = Quote(
        id=1, name="Test Quote Simple",
        quote_config_id=1, quote_config=mock_quote_config,
        product_entries=[mock_quote_entry_1],
        # ... other necessary fields
    )

    # Mock session.get to return our mock objects
    def get_side_effect(model, pk):
        if model == Quote and pk == 1:
            return mock_quote
        # Add other models if QuoteCalculator fetches them directly by ID (e.g., CalculatedQuote if updating)
        return None 
    mock_session.get.side_effect = get_side_effect
    
    # Mock session.exec(select(...)).first() for existing CalculatedQuote check
    mock_existing_calculated_quote_query = MagicMock()
    mock_existing_calculated_quote_query.first.return_value = None # No existing CalculatedQuote
    mock_session.exec.return_value = mock_existing_calculated_quote_query


    # --- Call the method ---
    calculated_quote_result = quote_calculator.calculate_and_save_quote(quote_id=1, session=mock_session)

    # --- Assertions ---
    # Material cost: 3 widgets * (2 kg/widget * 10 cost/kg) = 3 * 20 = 60
    # Labor cost: 3 widgets * 50 cost/widget = 150
    # COGS = 60 + 150 = 210
    # No fees, no margin, no tax.
    
    assert calculated_quote_result is not None
    assert calculated_quote_result.quote_id == 1
    assert final_quantize_decimal(calculated_quote_result.total_material_cost) == final_quantize_decimal(D("60"))
    assert final_quantize_decimal(calculated_quote_result.total_labor_cost) == final_quantize_decimal(D("150"))
    assert final_quantize_decimal(calculated_quote_result.cost_of_goods_sold) == final_quantize_decimal(D("210"))
    assert final_quantize_decimal(calculated_quote_result.subtotal_before_tax) == final_quantize_decimal(D("210"))
    assert final_quantize_decimal(calculated_quote_result.tax_amount) == final_quantize_decimal(D("0"))
    assert final_quantize_decimal(calculated_quote_result.final_price) == final_quantize_decimal(D("210"))
    
    assert len(calculated_quote_result.bill_of_materials_json) == 1
    bom_entry = calculated_quote_result.bill_of_materials_json[0]
    assert bom_entry.material_name == "Steel"
    assert quantize_decimal(bom_entry.quantity) == quantize_decimal(D("6")) # 3 widgets * 2 kg/widget
    assert quantize_decimal(bom_entry.unit_cost) == quantize_decimal(D("10"))
    assert final_quantize_decimal(bom_entry.total_cost) == final_quantize_decimal(D("60"))
    assert bom_entry.unit_name == "kg"
    
    assert len(calculated_quote_result.applied_rates_info_json) == 0 # No rates applied

    # Verify session.add and session.commit were called (or session.refresh if updating)
    mock_session.add.assert_any_call(calculated_quote_result) # Check that our object was added
    mock_session.commit.assert_called_once()
    # Check if refresh was called with calculated_quote_result
    refreshed_objects = [call_args[0][0] for call_args in mock_session.refresh.call_args_list]
    assert calculated_quote_result in refreshed_objects


def test_calculate_and_save_quote_with_sales_commission_and_margin(quote_calculator, mock_session):
    # --- Mock Data Setup ---
    mock_base_unit_type = UnitType(id=1, name="item", abbreviation="item")
    
    mock_material_1 = Material(
        id=1, name="Component A",
        cost_per_supplier_unit=D("20"), quantity_in_supplier_unit=D("1"), # Cost per base unit = 20
        base_unit_type_id=1, base_unit_type=mock_base_unit_type,
    )
    
    mock_product_1 = Product(
        id=1, name="Advanced Gizmo",
        base_labor_cost_per_product_unit=D("100"),
        product_materials=[
            ProductMaterial(id=1, product_id=1, material_id=1, material=mock_material_1, quantity_of_material_base_units_per_product_unit=D("1")),
        ],
    )
    
    mock_quote_entry_1 = QuoteProductEntry(
        id=1, quote_id=1, product_id=1, product=mock_product_1,
        quantity_of_product_units=D("1"), # 1 Advanced Gizmo
        selected_variations=[],
    )
    
    mock_quote_config = QuoteConfig(
        id=1, name="Config with Commission and Margin",
        sales_commission_rate=D("0.10"), # 10%
        franchise_fee_rate=D("0"),
        margin_rate=D("0.20"), # 20%
        additional_fixed_fees=D("0"),
        tax_rate=D("0"),
    )
    
    mock_quote = Quote(
        id=1, name="Test Quote Commission Margin",
        quote_config_id=1, quote_config=mock_quote_config,
        product_entries=[mock_quote_entry_1],
    )

    mock_session.get.return_value = mock_quote
    mock_existing_calculated_quote_query = MagicMock()
    mock_existing_calculated_quote_query.first.return_value = None
    mock_session.exec.return_value = mock_existing_calculated_quote_query

    # --- Call the method ---
    calculated_quote_result = quote_calculator.calculate_and_save_quote(quote_id=1, session=mock_session)

    # --- Assertions ---
    # Material cost: 1 widget * (1 item/widget * 20 cost/item) = 20
    # Labor cost: 1 widget * 100 cost/widget = 100
    # COGS = 20 + 100 = 120
    
    # Sales Commission (on COGS): 120 * 0.10 = 12
    # Subtotal after COGS-based fees = 120 + 12 = 132
    
    # Margin (on subtotal after COGS-based fees):
    # Cost base for margin = 132
    # Margin Amount = (132 * 0.20) / (1 - 0.20) = (132 * 0.20) / 0.80 = 26.4 / 0.80 = 33
    
    # Subtotal before tax = 132 (cost_base_for_margin) + 33 (margin_amount) = 165
    # No tax.
    # Final Price = 165
    
    assert final_quantize_decimal(calculated_quote_result.total_material_cost) == final_quantize_decimal(D("20"))
    assert final_quantize_decimal(calculated_quote_result.total_labor_cost) == final_quantize_decimal(D("100"))
    assert final_quantize_decimal(calculated_quote_result.cost_of_goods_sold) == final_quantize_decimal(D("120"))
    
    assert len(calculated_quote_result.applied_rates_info_json) == 2
    
    commission_info = next(r for r in calculated_quote_result.applied_rates_info_json if r.name == "Sales Commission")
    assert commission_info.type == "fee_on_cogs"
    assert quantize_decimal(commission_info.rate_value) == quantize_decimal(D("0.10"))
    assert final_quantize_decimal(commission_info.applied_amount) == final_quantize_decimal(D("12"))
    
    margin_info = next(r for r in calculated_quote_result.applied_rates_info_json if r.name == "Margin")
    assert margin_info.type == "margin"
    assert quantize_decimal(margin_info.rate_value) == quantize_decimal(D("0.20"))
    assert final_quantize_decimal(margin_info.applied_amount) == final_quantize_decimal(D("33"))

    assert final_quantize_decimal(calculated_quote_result.subtotal_before_tax) == final_quantize_decimal(D("165"))
    assert final_quantize_decimal(calculated_quote_result.tax_amount) == final_quantize_decimal(D("0"))
    assert final_quantize_decimal(calculated_quote_result.final_price) == final_quantize_decimal(D("165"))

    mock_session.add.assert_any_call(calculated_quote_result) # Check that our object was added
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_any_call(calculated_quote_result) # Allow multiple refreshes for now


def test_calculate_and_save_quote_with_variation_material_change(quote_calculator, mock_session):
    # --- Mock Data Setup ---
    mock_base_unit_type = UnitType(id=1, name="unit", abbreviation="u")
    
    mock_material_base = Material(id=1, name="Base Material", cost_per_supplier_unit=D("10"), quantity_in_supplier_unit=D("1"), base_unit_type=mock_base_unit_type)
    mock_material_added = Material(id=2, name="Added Material", cost_per_supplier_unit=D("5"), quantity_in_supplier_unit=D("1"), base_unit_type=mock_base_unit_type)

    mock_variation_option = VariationOption(
        id=1, name="Upgrade Option", additional_labor_cost_per_product_unit=D("5"),
        variation_option_materials=[
            VariationOptionMaterial(material_id=1, material=mock_material_base, quantity_of_material_base_units_added=D("-0.5")), # Reduces Base Material
            VariationOptionMaterial(material_id=2, material=mock_material_added, quantity_of_material_base_units_added=D("1.0")), # Adds new Material
        ]
    )

    mock_product = Product(
        id=1, name="Customizable Product", base_labor_cost_per_product_unit=D("20"),
        product_materials=[
            ProductMaterial(material_id=1, material=mock_material_base, quantity_of_material_base_units_per_product_unit=D("2.0"))
        ]
    )

    mock_quote_entry = QuoteProductEntry(
        id=1, product=mock_product, quantity_of_product_units=D("1"),
        selected_variations=[MagicMock(variation_option=mock_variation_option)] # Using MagicMock for QuoteProductEntryVariation
    )
    
    mock_quote_config = QuoteConfig(sales_commission_rate=D("0"), franchise_fee_rate=D("0"), margin_rate=D("0"), additional_fixed_fees=D("0"), tax_rate=D("0"))
    mock_quote = Quote(id=1, quote_config=mock_quote_config, product_entries=[mock_quote_entry])

    mock_session.get.return_value = mock_quote
    mock_existing_calculated_quote_query = MagicMock()
    mock_existing_calculated_quote_query.first.return_value = None
    mock_session.exec.return_value = mock_existing_calculated_quote_query
    
    # --- Call ---
    result = quote_calculator.calculate_and_save_quote(1, mock_session)

    # --- Assertions ---
    # Base Material: (2.0 base - 0.5 variation) * 10 cost = 1.5 * 10 = 15
    # Added Material: 1.0 variation * 5 cost = 5
    # Total Material Cost = 15 + 5 = 20

    # Base Labor: 20
    # Variation Labor: 5
    # Total Labor Cost = 20 + 5 = 25
    
    # COGS = 20 (material) + 25 (labor) = 45

    assert final_quantize_decimal(result.total_material_cost) == final_quantize_decimal(D("20"))
    assert final_quantize_decimal(result.total_labor_cost) == final_quantize_decimal(D("25"))
    assert final_quantize_decimal(result.cost_of_goods_sold) == final_quantize_decimal(D("45"))
    assert final_quantize_decimal(result.final_price) == final_quantize_decimal(D("45"))

    assert len(result.bill_of_materials_json) == 2
    
    base_material_bom = next(b for b in result.bill_of_materials_json if b.material_name == "Base Material")
    added_material_bom = next(b for b in result.bill_of_materials_json if b.material_name == "Added Material")

    assert quantize_decimal(base_material_bom.quantity) == quantize_decimal(D("1.5"))
    assert final_quantize_decimal(base_material_bom.total_cost) == final_quantize_decimal(D("15"))
    
    assert quantize_decimal(added_material_bom.quantity) == quantize_decimal(D("1.0"))
    assert final_quantize_decimal(added_material_bom.total_cost) == final_quantize_decimal(D("5"))

    mock_session.add.assert_any_call(result) # Check that our object was added
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_any_call(result) # Allow multiple refreshes for now


def test_calculate_and_save_quote_error_quote_not_found(quote_calculator, mock_session):
    mock_session.get.return_value = None # Quote not found
    with pytest.raises(ValueError, match="Quote with id 999 not found"):
        quote_calculator.calculate_and_save_quote(quote_id=999, session=mock_session)

def test_calculate_and_save_quote_error_quote_config_not_found(quote_calculator, mock_session):
    mock_quote_no_config = Quote(id=1, quote_config=None, product_entries=[])
    mock_session.get.return_value = mock_quote_no_config
    with pytest.raises(ValueError, match="QuoteConfig not found for Quote with id 1"):
        quote_calculator.calculate_and_save_quote(quote_id=1, session=mock_session)

def test_calculate_and_save_quote_error_margin_rate_too_high(quote_calculator, mock_session):
    mock_quote_config_high_margin = QuoteConfig(margin_rate=D("1.0")) # 100% margin
    mock_quote_high_margin = Quote(id=1, quote_config=mock_quote_config_high_margin, product_entries=[
        QuoteProductEntry(product=Product(base_labor_cost_per_product_unit=D("10")), quantity_of_product_units=D("1")) # Ensure COGS > 0
    ])
    mock_session.get.return_value = mock_quote_high_margin
    
    mock_existing_calculated_quote_query = MagicMock()
    mock_existing_calculated_quote_query.first.return_value = None
    mock_session.exec.return_value = mock_existing_calculated_quote_query

    with pytest.raises(ValueError, match="Margin rate cannot be 100% or more."):
        quote_calculator.calculate_and_save_quote(quote_id=1, session=mock_session)

# TODO: Add more tests:
# - Test with multiple product entries
# - Test with multiple variations per product entry
# - Test with franchise_fee_rate
# - Test with additional_fixed_fees
# - Test with tax_rate
# - Test updating an existing CalculatedQuote
# - Test variations that only add labor
# - Test variations that introduce a completely new material not in the base product
# - Test edge case: product_quantity = 0 for a QuoteProductEntry
# - Test edge case: material.quantity_in_supplier_unit = 0 (already covered by _get_material_cost_per_base_unit tests, but good to have in full calc)
# - Test with more complex BOM aggregation (same material from different sources)
