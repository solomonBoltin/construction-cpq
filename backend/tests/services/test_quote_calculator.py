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


@pytest.mark.parametrize(
    "cost_per_supplier_unit_str, quantity_in_supplier_unit_str, expected_cost_str",
    [
        ("10.0", "5.0", "2.0"),
        ("10.0", "0", "0"),
        ("0", "5.0", "0"),
    ],
)
def test_get_material_cost_per_base_unit(
    quote_calculator_service: QuoteCalculator, 
    D_fixture,
    cost_per_supplier_unit_str: str,
    quantity_in_supplier_unit_str: str,
    expected_cost_str: str,
):
    material = Material(
        cost_per_supplier_unit=D_fixture(cost_per_supplier_unit_str),
        quantity_in_supplier_unit=D_fixture(quantity_in_supplier_unit_str),
    )
    expected_cost = D_fixture(expected_cost_str)
    assert quote_calculator_service._get_material_cost_per_base_unit(material) == expected_cost


def test_calculate_and_save_quote_simple_product_no_variations_no_fees(
    quote_calculator_service: QuoteCalculator, mock_session: MagicMock, D_fixture
):
    D = D_fixture
    mock_unit_type = UnitType(id=1, name="kg", category="weight")
    
    mock_material_1 = Material(
        id=1, name="Steel",
        cost_per_supplier_unit=D("100"), quantity_in_supplier_unit=D("10"), 
        unit_type=mock_unit_type,
    )
    
    mock_product_1 = Product(
        id=1, name="Basic Widget",
        unit_labor_cost=D("50"),
        product_materials=[
            ProductMaterial(id=1, product_id=1, material_id=1, material=mock_material_1, material_amount=D("2")),
        ],
    )
    
    mock_quote_entry_1 = QuoteProductEntry(
        id=1, quote_id=1, product_id=1, product=mock_product_1,
        quantity_of_product_units=D("3"), 
        selected_variations=[],
    )
    
    mock_quote_config = QuoteConfig(
        id=1, name="Standard Config No Fees",
        sales_commission_rate=D("0"),
        franchise_fee_rate=D("0"),
        margin_rate=D("0"),
        additional_fixed_fees=D("0"),
        tax_rate=D("0"),
    )
    
    mock_quote = Quote(
        id=1, name="Test Quote Simple",
        quote_config_id=1, quote_config=mock_quote_config,
        product_entries=[mock_quote_entry_1],
    )

    
    mock_session.get.return_value = mock_quote
    
    calculated_quote_result = quote_calculator_service.calculate_and_save_quote(quote_id=1, session=mock_session)
    
    assert calculated_quote_result is not None
    assert calculated_quote_result.quote_id == 1
    assert final_quantize_decimal(calculated_quote_result.total_material_cost) == final_quantize_decimal(D("60"))
    assert final_quantize_decimal(calculated_quote_result.total_labor_cost) == final_quantize_decimal(D("150"))
    assert final_quantize_decimal(calculated_quote_result.cost_of_goods_sold) == final_quantize_decimal(D("210"))
    assert final_quantize_decimal(calculated_quote_result.subtotal_before_tax) == final_quantize_decimal(D("210"))
    assert final_quantize_decimal(calculated_quote_result.tax_amount) == final_quantize_decimal(D("0"))
    assert final_quantize_decimal(calculated_quote_result.final_price) == final_quantize_decimal(D("210"))
    
    assert len(calculated_quote_result.bill_of_materials_json) == 1
    bom_entry_data = calculated_quote_result.bill_of_materials_json[0]
    if isinstance(bom_entry_data, dict): # Handle Pydantic v2
        bom_entry = BillOfMaterialEntry.model_validate(bom_entry_data)
    else: # Handle Pydantic v1 or direct object
        bom_entry = bom_entry_data
        
    assert bom_entry.material_name == "Steel"
    assert quantize_decimal(bom_entry.quantity) == quantize_decimal(D("6")) 
    assert quantize_decimal(bom_entry.unit_cost) == quantize_decimal(D("10"))
    assert final_quantize_decimal(bom_entry.total_cost) == final_quantize_decimal(D("60"))
    assert bom_entry.unit_name == "kg"
    
    assert len(calculated_quote_result.applied_rates_info_json) == 0

    mock_session.add.assert_any_call(calculated_quote_result) 
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_any_call(calculated_quote_result)


def test_calculate_and_save_quote_with_sales_commission_and_margin(
    quote_calculator_service: QuoteCalculator, mock_session: MagicMock, D_fixture
):
    D = D_fixture
    mock_unit_type = UnitType(id=1, name="item", category="count")
    
    mock_material_1 = Material(
        id=1, name="Component A",
        cost_per_supplier_unit=D("20"), quantity_in_supplier_unit=D("1"), 
        unit_type_id=1, unit_type=mock_unit_type,
    )
    
    mock_product_1 = Product(
        id=1, name="Advanced Gizmo",
        unit_labor_cost=D("100"),
        product_materials=[
            ProductMaterial(id=1, product_id=1, material_id=1, material=mock_material_1, material_amount=D("1")),
        ],
    )
    
    mock_quote_entry_1 = QuoteProductEntry(
        id=1, quote_id=1, product_id=1, product=mock_product_1,
        quantity_of_product_units=D("1"), 
        selected_variations=[],
    )
    
    mock_quote_config = QuoteConfig(
        id=1, name="Config with Commission and Margin",
        sales_commission_rate=D("0.10"), 
        franchise_fee_rate=D("0"),
        margin_rate=D("0.20"), 
        additional_fixed_fees=D("0"),
        tax_rate=D("0"),
    )
    
    mock_quote = Quote(
        id=1, name="Test Quote Commission Margin",
        quote_config_id=1, quote_config=mock_quote_config,
        product_entries=[mock_quote_entry_1],
    )

    mock_session.get.return_value = mock_quote
    
    calculated_quote_result = quote_calculator_service.calculate_and_save_quote(quote_id=1, session=mock_session)
    
    assert final_quantize_decimal(calculated_quote_result.total_material_cost) == final_quantize_decimal(D("20"))
    assert final_quantize_decimal(calculated_quote_result.total_labor_cost) == final_quantize_decimal(D("100"))
    assert final_quantize_decimal(calculated_quote_result.cost_of_goods_sold) == final_quantize_decimal(D("120"))
    
    assert len(calculated_quote_result.applied_rates_info_json) == 2
    
    commission_info_data = next(r for r in calculated_quote_result.applied_rates_info_json if r.name == "Sales Commission")
    if isinstance(commission_info_data, dict):
        commission_info = AppliedRateInfoEntry.model_validate(commission_info_data)
    else:
        commission_info = commission_info_data
        
    assert commission_info.type == "fee_on_cogs"
    assert quantize_decimal(commission_info.rate_value) == quantize_decimal(D("0.10"))
    assert final_quantize_decimal(commission_info.applied_amount) == final_quantize_decimal(D("12"))
    
    margin_info_data = next(r for r in calculated_quote_result.applied_rates_info_json if r.name == "Margin")
    if isinstance(margin_info_data, dict):
        margin_info = AppliedRateInfoEntry.model_validate(margin_info_data)
    else:
        margin_info = margin_info_data
        
    assert margin_info.type == "margin"
    assert quantize_decimal(margin_info.rate_value) == quantize_decimal(D("0.20"))
    assert final_quantize_decimal(margin_info.applied_amount) == final_quantize_decimal(D("33"))

    assert final_quantize_decimal(calculated_quote_result.subtotal_before_tax) == final_quantize_decimal(D("165"))
    assert final_quantize_decimal(calculated_quote_result.tax_amount) == final_quantize_decimal(D("0"))
    assert final_quantize_decimal(calculated_quote_result.final_price) == final_quantize_decimal(D("165"))

    mock_session.add.assert_any_call(calculated_quote_result) 
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_any_call(calculated_quote_result) 


def test_calculate_and_save_quote_with_variation_material_change(
    quote_calculator_service: QuoteCalculator, mock_session: MagicMock, D_fixture
):
    D = D_fixture
    mock_unit_type = UnitType(id=1, name="unit", category="general")
    mock_material_base = Material(id=1, name="Base Material", cost_per_supplier_unit=D("10"), quantity_in_supplier_unit=D("1"), unit_type=mock_unit_type)
    mock_material_added = Material(id=2, name="Added Material", cost_per_supplier_unit=D("5"), quantity_in_supplier_unit=D("1"), unit_type=mock_unit_type)

    mock_variation_option = VariationOption(
        id=1, name="Upgrade Option", additional_labor_cost_per_product_unit=D("5"),
        variation_option_materials=[
            VariationOptionMaterial(material_id=1, material=mock_material_base, quantity_of_material_base_units_added=D("-0.5")), 
            VariationOptionMaterial(material_id=2, material=mock_material_added, quantity_of_material_base_units_added=D("1.0")), 
        ]
    )

    mock_product = Product(
        id=1, name="Customizable Product", unit_labor_cost=D("20"),
        product_materials=[
            ProductMaterial(material_id=1, material=mock_material_base, material_amount=D("2.0"))
        ]
    )

    mock_quote_entry = QuoteProductEntry(
        id=1, product=mock_product, quantity_of_product_units=D("1"),
        selected_variations=[MagicMock(variation_option=mock_variation_option)] 
    )
    
    mock_quote_config = QuoteConfig(sales_commission_rate=D("0"), franchise_fee_rate=D("0"), margin_rate=D("0"), additional_fixed_fees=D("0"), tax_rate=D("0"))
    mock_quote = Quote(id=1, quote_config=mock_quote_config, product_entries=[mock_quote_entry])

    mock_session.get.return_value = mock_quote
    
    result = quote_calculator_service.calculate_and_save_quote(1, mock_session)

    assert final_quantize_decimal(result.total_material_cost) == final_quantize_decimal(D("25"))
    assert final_quantize_decimal(result.total_labor_cost) == final_quantize_decimal(D("25"))
    assert final_quantize_decimal(result.cost_of_goods_sold) == final_quantize_decimal(D("50"))
    assert final_quantize_decimal(result.final_price) == final_quantize_decimal(D("50"))

    assert len(result.bill_of_materials_json) == 2
    
    base_material_bom_data = next(b for b in result.bill_of_materials_json if b.material_name == "Base Material")
    if isinstance(base_material_bom_data, dict):
        base_material_bom = BillOfMaterialEntry.model_validate(base_material_bom_data)
    else:
        base_material_bom = base_material_bom_data
        
    added_material_bom_data = next(b for b in result.bill_of_materials_json if b.material_name == "Added Material")
    if isinstance(added_material_bom_data, dict):
        added_material_bom = BillOfMaterialEntry.model_validate(added_material_bom_data)
    else:
        added_material_bom = added_material_bom_data

    assert quantize_decimal(base_material_bom.quantity) == quantize_decimal(D("2")) 
    assert final_quantize_decimal(base_material_bom.total_cost) == final_quantize_decimal(D("20")) 
    
    assert quantize_decimal(added_material_bom.quantity) == quantize_decimal(D("1")) 
    assert final_quantize_decimal(added_material_bom.total_cost) == final_quantize_decimal(D("5")) 

    mock_session.add.assert_any_call(result) 
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_any_call(result)


def test_calculate_and_save_quote_error_quote_not_found(quote_calculator_service: QuoteCalculator, mock_session: MagicMock):
    mock_session.get.return_value = None 
    with pytest.raises(ValueError, match="Quote with id 999 not found"):
        quote_calculator_service.calculate_and_save_quote(quote_id=999, session=mock_session)

def test_calculate_and_save_quote_error_quote_config_not_found(quote_calculator_service: QuoteCalculator, mock_session: MagicMock):
    mock_quote_no_config = Quote(id=1, quote_config=None, product_entries=[]) # type: ignore
    mock_session.get.return_value = mock_quote_no_config
    with pytest.raises(ValueError, match="QuoteConfig not found for Quote with id 1"):
        quote_calculator_service.calculate_and_save_quote(quote_id=1, session=mock_session)

def test_calculate_and_save_quote_error_margin_rate_too_high(
    quote_calculator_service: QuoteCalculator, mock_session: MagicMock, D_fixture
):
    D = D_fixture
    mock_quote_config_high_margin = QuoteConfig(margin_rate=D("1.0")) 
    mock_product_for_cogs = Product(id=1, name="Prod", unit_labor_cost=D("10"), product_materials=[])
    mock_quote_entry_for_cogs = QuoteProductEntry(id=1, product=mock_product_for_cogs, quantity_of_product_units=D("1"), selected_variations=[])
    mock_quote_high_margin = Quote(id=1, quote_config=mock_quote_config_high_margin, product_entries=[mock_quote_entry_for_cogs])
    
    mock_session.get.return_value = mock_quote_high_margin
    
    with pytest.raises(ValueError, match="Margin rate cannot be 100% or more."):
        quote_calculator_service.calculate_and_save_quote(quote_id=1, session=mock_session)

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
