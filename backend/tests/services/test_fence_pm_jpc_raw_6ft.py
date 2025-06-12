# test_quote_calculator_postmaster_h_refactored.py

from datetime import datetime
import logging
import os
import pytest
from decimal import Decimal
from unittest.mock import MagicMock # Keep if still used, though conftest mock_session might cover it
from typing import Dict, Any

from app.models import (
    Material,
    UnitType,
    Quote,
    QuoteConfig,
    QuoteProductEntry,
    Product,
    ProductMaterial,
    VariationGroup,
    VariationOption,
    QuoteProductEntryVariation,
    VariationOptionMaterial,
    CalculatedQuote,
)
from app.services.quote_calculator import QuoteCalculator, final_quantize_decimal, quantize_decimal
from tests.model_str_format import str_format_calculated_quote, str_format_quote
from tests.conftest import assert_decimal_equal_conftest, assert_calculated_quote_financial_details

logger = logging.getLogger(__name__)


class TestQuoteCalculatorPostmasterHorizontalRawJPC6ft:
    """Test suite for QuoteCalculator with Postmaster Horizontal Fence scenarios."""

    @pytest.fixture
    def unit_types(self):
        return {
            'linear_foot': UnitType(id=2, name="linear foot", category="Length"),
            'bag': UnitType(id=3, name="bag", category="Count")
        }

    @pytest.fixture
    def materials(self, unit_types, D_fixture):
        return {
            "postmaster_8ft": Material(
                id=2,
                name="8' Postmaster",
                cost_per_supplier_unit=D_fixture("18.01"),
                quantity_in_supplier_unit=D_fixture("1"),
                base_unit_type=unit_types['linear_foot'],
            ),
            "picket_raw_1x6x8": Material(
                id=6,
                name="JPC 1x6x8 Raw Picket",
                cost_per_supplier_unit=D_fixture("5.40"),
                quantity_in_supplier_unit=D_fixture("1"),
                base_unit_type=unit_types['linear_foot'],
                cull_rate=D_fixture("0.05"),
            ),
            "rail_raw_2x4x12": Material(
                id=10,
                name="JPC 2x4x12 Raw Rail",
                cost_per_supplier_unit=D_fixture("12.50"),
                quantity_in_supplier_unit=D_fixture("1"),
                base_unit_type=unit_types['linear_foot'],
            ),
            "kickboard_2x6x16": Material(
                id=12,
                name="SYP 2x6x16 Color Treated Kickboard",
                cost_per_supplier_unit=D_fixture("12.45"),
                quantity_in_supplier_unit=D_fixture("1"),
                base_unit_type=unit_types['linear_foot'],
            ),
            "nails": Material(
                id=14,
                name='Hardware - 2.25" Galvanized Ring Shank Nails',
                cost_per_supplier_unit=D_fixture("0.01"),
                quantity_in_supplier_unit=D_fixture("1"),
                base_unit_type=unit_types['linear_foot'],
            ),
            "concrete": Material(
                id=15,
                name="Concrete",
                cost_per_supplier_unit=D_fixture("5.35"),
                quantity_in_supplier_unit=D_fixture("1"),
                base_unit_type=unit_types['bag'],
            ),
        }

    @pytest.fixture
    def variation_options(self, materials, D_fixture):
        cap_group = VariationGroup(
            id=2, name="Cap", product_id=1, selection_type="single_choice", is_required=False
        )
        cap_yes = VariationOption(id=3, name="Yes", variation_group_id=2)
        cap_no = VariationOption(id=4, name="No", variation_group_id=2)
        cap_group.options = [cap_yes, cap_no]

        trim_group = VariationGroup(
            id=3, name="Trim", product_id=1, selection_type="single_choice", is_required=False
        )
        trim_yes = VariationOption(id=5, name="Yes", variation_group_id=3)
        trim_no = VariationOption(id=6, name="No", variation_group_id=3)
        trim_group.options = [trim_yes, trim_no]

        style_group = VariationGroup(
            id=4, name="Style", product_id=1, selection_type="single_choice", is_required=True
        )
        style_sxs = VariationOption(id=7, name="SxS", variation_group_id=4)
        style_bob = VariationOption(id=8, name="B.O.B.", variation_group_id=4)
        
        style_bob.variation_option_materials = [
            VariationOptionMaterial(
                variation_option_id=8,
                material_id=6,
                material=materials["picket_raw_1x6x8"],
                quantity_of_material_base_units_added=D_fixture("0.5")
            )
        ]
        style_group.options = [style_sxs, style_bob]

        return {
            'cap': {'group': cap_group, 'yes': cap_yes, 'no': cap_no},
            'trim': {'group': trim_group, 'yes': trim_yes, 'no': trim_no},
            'style': {'group': style_group, 'sxs': style_sxs, 'bob': style_bob}
        }

    @pytest.fixture
    def base_product(self, materials, variation_options, unit_types, D_fixture):
        product = Product(
            id=1,
            name="Postmaster Horizontal Fence - 6ft H - Raw",
            unit_labor_cost=D_fixture("8.00"),
            product_unit_type_id=unit_types['linear_foot'].id,
            product_materials=[
                ProductMaterial(
                    material=materials["postmaster_8ft"],
                    material_amount=D_fixture("0.125")
                ),
                ProductMaterial(
                    material=materials["picket_raw_1x6x8"],
                    material_amount=D_fixture("1.5")
                ),
                ProductMaterial(
                    material=materials["rail_raw_2x4x12"],
                    material_amount=D_fixture("0.0625")
                ),
                ProductMaterial(
                    material=materials["kickboard_2x6x16"],
                    material_amount=D_fixture("0.0625")
                ),
                ProductMaterial(
                    material=materials["nails"],
                    material_amount=D_fixture("50")
                ),
                ProductMaterial(
                    material=materials["concrete"],
                    material_amount=D_fixture("0.125")
                ),
            ],
            variation_groups=[
                variation_options['cap']['group'],
                variation_options['trim']['group'],
                variation_options['style']['group']
            ]
        )
        return product

    @pytest.fixture
    def quote_config(self, D_fixture):
        return QuoteConfig(
            id=1,
            name="Postmaster Horizontal Config",
            sales_commission_rate=D_fixture("0.07"),
            franchise_fee_rate=D_fixture("0.04"),
            margin_rate=D_fixture("0.30"),
            additional_fixed_fees=D_fixture("0.00"),
            tax_rate=D_fixture("0.085"),
            round_up_materials=False,
        )

    def create_quote(self, product, quote_config, quantity, variation_selections, D_fixture):
        quote_entry = QuoteProductEntry(
            id=1,
            quote_id=1,
            product_id=1,
            product=product,
            quantity_of_product_units=quantity,
            selected_variations=[
                QuoteProductEntryVariation(
                    quote_product_entry_id=1,
                    variation_option=option
                ) for option in variation_selections
            ]
        )

        return Quote(
            id=1,
            name=f"Test Quote - {quantity}ft",
            quote_config_id=1,
            quote_config=quote_config,
            product_entries=[quote_entry]
        )

    def test_calculate_100ft_raw_fence_no_cap_no_trim_sxs(
        self, quote_calculator_service, mock_session, base_product, quote_config, variation_options, D_fixture
    ):
        """Test calculation for 100ft raw fence with SxS style, no cap, no trim."""
        quantity = D_fixture("100")
        variations = [
            variation_options['cap']['no'],
            variation_options['trim']['no'],
            variation_options['style']['sxs']
        ]
        
        quote = self.create_quote(base_product, quote_config, quantity, variations, D_fixture)
        mock_session.get.return_value = quote

        expected_material_cost = D_fixture("1348.45")
        expected_labor_cost = D_fixture("800.00")
        expected_cogs = expected_material_cost + expected_labor_cost

        result = quote_calculator_service.calculate_and_save_quote(quote_id=1, session=mock_session)

        self._report_test("fence_pm_jpc_6ft_raw_100ft_no_cap_no_trim_sxs", quote, result)
        
        assert result is not None, "Calculator should return a result"
        assert result.quote_id == 1
        
        assert_calculated_quote_financial_details(
            calculated_quote=result,
            expected_total_material_cost=expected_material_cost,
            expected_total_labor_cost=expected_labor_cost,
            expected_cogs=expected_cogs,
            quote_config=quote_config,
            D_fixture=D_fixture
        )
        
        mock_session.add.assert_any_call(result)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_any_call(result)

    def test_picket_cull_rate_calculation(
        self, quote_calculator_service, mock_session, base_product, quote_config, variation_options, D_fixture
    ):
        """Test that cull rates are correctly applied to pickets."""
        quantity = D_fixture("100")
        variations = [
            variation_options['cap']['no'],
            variation_options['trim']['no'],
            variation_options['style']['sxs']
        ]
        
        quote = self.create_quote(base_product, quote_config, quantity, variations, D_fixture)
        mock_session.get.return_value = quote

        result = quote_calculator_service.calculate_and_save_quote(quote_id=1, session=mock_session)

        picket_bom = self._find_bom_entry(result, "JPC 1x6x8 Raw Picket")
        assert picket_bom is not None, "Picket entry should exist in BOM"
        
        expected_cull_units = D_fixture("7.5")
        expected_total_quantity = D_fixture("157.5")

        # Use conftest helper for decimal comparison if applicable, or keep specific quantize
        assert_decimal_equal_conftest(picket_bom.cull_units, quantize_decimal(expected_cull_units), D_fixture, "Picket Cull Units")
        assert_decimal_equal_conftest(picket_bom.quantity, expected_total_quantity, D_fixture, "Picket Total Quantity")

    @pytest.mark.parametrize("round_up_materials,expected_picket_qty_str", [
        (False, "157.5"),
        (True, "158"),
    ])
    def test_material_rounding_behavior(
        self, quote_calculator_service, mock_session, base_product, quote_config, variation_options, D_fixture,
        round_up_materials, expected_picket_qty_str
    ):
        """Test material quantity rounding based on configuration."""
        expected_picket_qty = D_fixture(expected_picket_qty_str)
        quote_config.round_up_materials = round_up_materials
        quantity = D_fixture("100")
        variations = [
            variation_options['cap']['no'],
            variation_options['trim']['no'],
            variation_options['style']['sxs']
        ]
        
        quote = self.create_quote(base_product, quote_config, quantity, variations, D_fixture)
        mock_session.get.return_value = quote

        result = quote_calculator_service.calculate_and_save_quote(quote_id=1, session=mock_session)

        picket_bom = self._find_bom_entry(result, "JPC 1x6x8 Raw Picket")
        assert_decimal_equal_conftest(picket_bom.quantity, expected_picket_qty, D_fixture, "Picket Quantity with Rounding")

   
    def test_variation_selection_impacts_calculation(
        self, quote_calculator_service, mock_session, base_product, quote_config, variation_options, D_fixture
    ):
        """Test that different variation selections affect the calculation appropriately."""
        quantity = D_fixture("100")
        
        variations_bob = [
            variation_options['cap']['no'],
            variation_options['trim']['no'],
            variation_options['style']['bob']
        ]
        
        quote = self.create_quote(base_product, quote_config, quantity, variations_bob, D_fixture)
        mock_session.get.return_value = quote

        result = quote_calculator_service.calculate_and_save_quote(quote_id=1, session=mock_session)
        
        self._report_test("fence_pm_jpc_6ft_raw_100ft_no_cap_no_trim_bob", quote, result)
        
        expected_material_cost_bob = D_fixture("1631.95")
        expected_labor_cost = D_fixture("800.00")
        expected_cogs_bob = expected_material_cost_bob + expected_labor_cost
        excepted_total_raw_1x6x8_units = D_fixture("210")
   
        assert result is not None, "Calculator should return a result"
        assert result.quote_id == 1

        assert_calculated_quote_financial_details(
            calculated_quote=result,
            expected_total_material_cost=expected_material_cost_bob,
            expected_total_labor_cost=expected_labor_cost,
            expected_cogs=expected_cogs_bob,
            quote_config=quote_config,
            D_fixture=D_fixture
        )
        
        picket_bom = self._find_bom_entry(result, "JPC 1x6x8 Raw Picket")        
        assert picket_bom is not None, "Picket entry should exist in BOM"
        assert_decimal_equal_conftest(picket_bom.quantity, excepted_total_raw_1x6x8_units, D_fixture, "Picket Quantity for B.O.B.")
        

    def _find_bom_entry(self, result: CalculatedQuote, material_name: str):
        from app.models import BillOfMaterialEntry
        
        for bom_data in result.bill_of_materials_json:
            bom_entry = BillOfMaterialEntry.model_validate(bom_data)
            if bom_entry.material_name == material_name:
                return bom_entry
        return None

    def _report_test(self, test_function_name, mock_quote, calculated_quote_result):
        try:
            
            current_date_str = datetime.now().strftime("%Y-%m-%d")
            output_dir = os.path.join(
                os.path.dirname(__file__), "..", "output"
            ) 
            os.makedirs(output_dir, exist_ok=True)

            file_name = f"{current_date_str}_{test_function_name}_summary.txt"
            file_path = os.path.join(output_dir, file_name)

            summary_content = (
                f"--- Test Summary for: {test_function_name} ---\\n"
                f"Executed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n"
                f"--- Mock Quote Overview (Input) ---\\n"
                f"{str_format_quote(mock_quote)}\\n\\n"
                f"--- Calculated Quote (Output) ---\\n"
                f"{str_format_calculated_quote(calculated_quote_result)}\\n"
            )

            with open(file_path, "w") as f:
                f.write(summary_content)
            logger.info(f"Test summary written to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write test summary to file: {e}")

