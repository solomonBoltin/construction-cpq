# test_quote_calculator_postmaster_h_refactored.py

from datetime import datetime
import logging
import os
import pytest
from decimal import Decimal
from unittest.mock import MagicMock
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

logger = logging.getLogger(__name__)


class TestQuoteCalculatorPostmasterHorizontalRawJPC6ft:
    """Test suite for QuoteCalculator with Postmaster Horizontal Fence scenarios."""

    @pytest.fixture
    def unit_types(self):
        """Create mock unit types."""
        return {
            'linear_foot': UnitType(id=2, name="linear foot", category="Length"),
            'bag': UnitType(id=3, name="bag", category="Count")
        }

    @pytest.fixture
    def materials(self, unit_types):
        """Create mock materials with realistic pricing."""
        return {
            "postmaster_8ft": Material(
                id=2,
                name="8' Postmaster",
                cost_per_supplier_unit=Decimal("18.01"),
                quantity_in_supplier_unit=Decimal("1"),
                base_unit_type=unit_types['linear_foot'],
            ),
            "picket_raw_1x6x8": Material(
                id=6,
                name="JPC 1x6x8 Raw Picket",
                cost_per_supplier_unit=Decimal("5.40"),
                quantity_in_supplier_unit=Decimal("1"),
                base_unit_type=unit_types['linear_foot'],
                cull_rate=Decimal("0.05"),
            ),
            "rail_raw_2x4x12": Material(
                id=10,
                name="JPC 2x4x12 Raw Rail",
                cost_per_supplier_unit=Decimal("12.50"),
                quantity_in_supplier_unit=Decimal("1"),
                base_unit_type=unit_types['linear_foot'],
            ),
            "kickboard_2x6x16": Material(
                id=12,
                name="SYP 2x6x16 Color Treated Kickboard",
                cost_per_supplier_unit=Decimal("12.45"),
                quantity_in_supplier_unit=Decimal("1"),
                base_unit_type=unit_types['linear_foot'],
            ),
            "nails": Material(
                id=14,
                name='Hardware - 2.25" Galvanized Ring Shank Nails',
                cost_per_supplier_unit=Decimal("0.01"),
                quantity_in_supplier_unit=Decimal("1"),
                base_unit_type=unit_types['linear_foot'],
            ),
            "concrete": Material(
                id=15,
                name="Concrete",
                cost_per_supplier_unit=Decimal("5.35"),
                quantity_in_supplier_unit=Decimal("1"),
                base_unit_type=unit_types['bag'],
            ),
        }

    @pytest.fixture
    def variation_options(self, materials):
        """Create variation options for fence customization."""
        # Cap options
        cap_group = VariationGroup(
            id=2, name="Cap", product_id=1, selection_type="single_choice", is_required=False
        )
        cap_yes = VariationOption(id=3, name="Yes", variation_group_id=2)
        cap_no = VariationOption(id=4, name="No", variation_group_id=2)
        cap_group.options = [cap_yes, cap_no]

        # Trim options
        trim_group = VariationGroup(
            id=3, name="Trim", product_id=1, selection_type="single_choice", is_required=False
        )
        trim_yes = VariationOption(id=5, name="Yes", variation_group_id=3)
        trim_no = VariationOption(id=6, name="No", variation_group_id=3)
        trim_group.options = [trim_yes, trim_no]

        # Style options
        style_group = VariationGroup(
            id=4, name="Style", product_id=1, selection_type="single_choice", is_required=True
        )
        style_sxs = VariationOption(id=7, name="SxS", variation_group_id=4)
        style_bob = VariationOption(id=8, name="B.O.B.", variation_group_id=4)
        
        # B.O.B. style needs 0.5 more raw pickets per linear foot
        style_bob.variation_option_materials = [
            VariationOptionMaterial(
                variation_option_id=8,
                material_id=6,  # picket_raw_1x6x8
                material=materials["picket_raw_1x6x8"],
                quantity_of_material_base_units_added=Decimal("0.5")
            )
        ]
        style_group.options = [style_sxs, style_bob]

        return {
            'cap': {'group': cap_group, 'yes': cap_yes, 'no': cap_no},
            'trim': {'group': trim_group, 'yes': trim_yes, 'no': trim_no},
            'style': {'group': style_group, 'sxs': style_sxs, 'bob': style_bob}
        }

    @pytest.fixture
    def base_product(self, materials, variation_options, unit_types):
        """Create base product with materials and variations."""
        product = Product(
            id=1,
            name="Postmaster Horizontal Fence - 6ft H - Raw",
            base_labor_cost_per_product_unit=Decimal("8.00"),
            product_unit_type_id=unit_types['linear_foot'].id,
            product_materials=[
                ProductMaterial(
                    material=materials["postmaster_8ft"],
                    quantity_of_material_base_units_per_product_unit=Decimal("0.125")
                ),
                ProductMaterial(
                    material=materials["picket_raw_1x6x8"],
                    quantity_of_material_base_units_per_product_unit=Decimal("1.5")
                ),
                ProductMaterial(
                    material=materials["rail_raw_2x4x12"],
                    quantity_of_material_base_units_per_product_unit=Decimal("0.0625")
                ),
                ProductMaterial(
                    material=materials["kickboard_2x6x16"],
                    quantity_of_material_base_units_per_product_unit=Decimal("0.0625")
                ),
                ProductMaterial(
                    material=materials["nails"],
                    quantity_of_material_base_units_per_product_unit=Decimal("50")
                ),
                ProductMaterial(
                    material=materials["concrete"],
                    quantity_of_material_base_units_per_product_unit=Decimal("0.125")
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
    def quote_config(self):
        """Create standard quote configuration."""
        return QuoteConfig(
            id=1,
            name="Postmaster Horizontal Config",
            sales_commission_rate=Decimal("0.07"),
            franchise_fee_rate=Decimal("0.04"),
            margin_rate=Decimal("0.30"),
            additional_fixed_fees=Decimal("0.00"),
            tax_rate=Decimal("0.085"),
            round_up_materials=False,
        )

    def create_quote(self, product, quote_config, quantity, variation_selections):
        """Factory method to create quotes with specific configurations."""
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

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        return session

    @pytest.fixture
    def calculator(self):
        """QuoteCalculator instance."""
        return QuoteCalculator()


    def test_calculate_100ft_raw_fence_no_cap_no_trim_sxs(
        self, calculator, mock_session, base_product, quote_config, variation_options
    ):
        """Test calculation for 100ft raw fence with SxS style, no cap, no trim."""
        # Arrange
        quantity = Decimal("100")
        variations = [
            variation_options['cap']['no'],
            variation_options['trim']['no'],
            variation_options['style']['sxs']
        ]
        
        quote = self.create_quote(base_product, quote_config, quantity, variations)
        mock_session.get.return_value = quote

        # Expected values based on Excel calculations
        expected_material_cost = Decimal("1348.45")
        expected_labor_cost = Decimal("800.00")
        expected_cogs = expected_material_cost + expected_labor_cost

        # Act
        result = calculator.calculate_and_save_quote(quote_id=1, session=mock_session)

        # Report test results
        self._report_test("fence_pm_jpc_6ft_raw_100ft_no_cap_no_trim_sxs", quote, result)
        
        # Assert
        assert result is not None, "Calculator should return a result"
        assert result.quote_id == 1
        
        # Core cost assertions
        self._assert_decimal_equal(result.total_material_cost, expected_material_cost)
        self._assert_decimal_equal(result.total_labor_cost, expected_labor_cost)
        self._assert_decimal_equal(result.cost_of_goods_sold, expected_cogs)

        # Validate calculated fees and margins
        self._validate_calculated_fees(result, quote_config, expected_cogs)
        
        # Verify session interactions
        mock_session.add.assert_any_call(result)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_any_call(result)

    def test_picket_cull_rate_calculation(
        self, calculator, mock_session, base_product, quote_config, variation_options
    ):
        """Test that cull rates are correctly applied to pickets."""
        # Arrange
        quantity = Decimal("100")
        variations = [
            variation_options['cap']['no'],
            variation_options['trim']['no'],
            variation_options['style']['sxs']
        ]
        
        quote = self.create_quote(base_product, quote_config, quantity, variations)
        mock_session.get.return_value = quote

        # Act
        result = calculator.calculate_and_save_quote(quote_id=1, session=mock_session)

        # Assert
        picket_bom = self._find_bom_entry(result, "JPC 1x6x8 Raw Picket")
        assert picket_bom is not None, "Picket entry should exist in BOM"
        
        # Expected: 100ft * 1.5 pickets/ft = 150 base pickets
        # With 5% cull: 150 * 0.05 = 7.5 cull units
        # Total: 150 + 7.5 = 157.5 pickets
        expected_base_quantity = Decimal("150")  # 100 * 1.5
        expected_cull_units = Decimal("7.5")     # 150 * 0.05
        expected_total_quantity = Decimal("157.5")

        assert picket_bom.cull_units == quantize_decimal(expected_cull_units)
        assert picket_bom.quantity == expected_total_quantity

    @pytest.mark.parametrize("round_up_materials,expected_picket_qty", [
        (False, Decimal("157.5")),
        (True, Decimal("158")),  # ceil(157.5)
    ])
    def test_material_rounding_behavior(
        self, calculator, mock_session, base_product, quote_config, variation_options,
        round_up_materials, expected_picket_qty
    ):
        """Test material quantity rounding based on configuration."""
        # Arrange
        quote_config.round_up_materials = round_up_materials
        quantity = Decimal("100")
        variations = [
            variation_options['cap']['no'],
            variation_options['trim']['no'],
            variation_options['style']['sxs']
        ]
        
        quote = self.create_quote(base_product, quote_config, quantity, variations)
        mock_session.get.return_value = quote

        # Act
        result = calculator.calculate_and_save_quote(quote_id=1, session=mock_session)

        # Assert
        picket_bom = self._find_bom_entry(result, "JPC 1x6x8 Raw Picket")
        assert picket_bom.quantity == expected_picket_qty

   
    def test_variation_selection_impacts_calculation(
        self, calculator, mock_session, base_product, quote_config, variation_options
    ):
        """Test that different variation selections affect the calculation appropriately."""
        # This test would compare SxS vs B.O.B. if they had different costs
        # For now, it validates that the variation selection is processed
        quantity = Decimal("100")
        
        # Test with B.O.B. style
        variations_bob = [
            variation_options['cap']['no'],
            variation_options['trim']['no'],
            variation_options['style']['bob']
        ]
        
        quote = self.create_quote(base_product, quote_config, quantity, variations_bob)
        mock_session.get.return_value = quote

        result = calculator.calculate_and_save_quote(quote_id=1, session=mock_session)
        
        # Report test results
        self._report_test("fence_pm_jpc_6ft_raw_100ft_no_cap_no_trim_bob", quote, result)
        
        # Expected values based on Excel calculations for B.O.B. style
        expected_material_cost_bob = Decimal("1631.95")
        expected_labor_cost = Decimal("800.00")
        expected_cogs_bob = expected_material_cost_bob + expected_labor_cost
        excepted_total_raw_1x6x8_units = Decimal("210")

        # Assert    
        assert result is not None, "Calculator should return a result"
        assert result.quote_id == 1
        self._assert_decimal_equal(result.total_material_cost, expected_material_cost_bob)
        self._assert_decimal_equal(result.total_labor_cost, expected_labor_cost)
        self._assert_decimal_equal(result.cost_of_goods_sold, expected_cogs_bob)
        self._validate_calculated_fees(result, quote_config, expected_cogs_bob)
        
        picket_bom = self._find_bom_entry(result, "JPC 1x6x8 Raw Picket")        
        assert picket_bom is not None, "Picket entry should exist in BOM"
        assert picket_bom.quantity == excepted_total_raw_1x6x8_units, \
            f"Expected {excepted_total_raw_1x6x8_units} pickets, got {picket_bom.quantity}"
        
        

    # Helper methods
    def _assert_decimal_equal(self, actual: Decimal, expected: Decimal, msg: str = ""):
        """Assert two decimals are equal after final quantization."""
        assert final_quantize_decimal(actual) == final_quantize_decimal(expected), \
            f"{msg} Expected: {expected}, Got: {actual}"

    def _validate_calculated_fees(self, result: CalculatedQuote, config: QuoteConfig, cogs: Decimal):
        """Validate that fees and margins are calculated correctly."""
        expected_commission = cogs * config.sales_commission_rate
        expected_franchise_fee = cogs * config.franchise_fee_rate
        
        cost_base = cogs + expected_commission + expected_franchise_fee
        expected_margin = (cost_base * config.margin_rate) / (Decimal("1") - config.margin_rate)
        expected_subtotal = cost_base + expected_margin
        expected_tax = expected_subtotal * config.tax_rate
        expected_final_price = expected_subtotal + expected_tax

        self._assert_decimal_equal(result.subtotal_before_tax, expected_subtotal)
        self._assert_decimal_equal(result.tax_amount, expected_tax)
        self._assert_decimal_equal(result.final_price, expected_final_price)

        # Validate applied rates
        assert len(result.applied_rates_info_json) == 3
        
        rate_amounts = {rate.name: rate.applied_amount for rate in result.applied_rates_info_json}
        self._assert_decimal_equal(rate_amounts["Sales Commission"], expected_commission)
        self._assert_decimal_equal(rate_amounts["Franchise Fee"], expected_franchise_fee)
        self._assert_decimal_equal(rate_amounts["Margin"], expected_margin)

    def _find_bom_entry(self, result: CalculatedQuote, material_name: str):
        """Find a specific BOM entry by material name."""
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
                os.path.dirname(os.path.dirname(__file__)), "output"
            )  # tests/output/
            os.makedirs(output_dir, exist_ok=True)

            file_name = f"{current_date_str}_{test_function_name}_summary.txt"
            file_path = os.path.join(output_dir, file_name)

            summary_content = (
                f"--- Test Summary for: {test_function_name} ---\n"
                f"Executed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"--- Mock Quote Overview (Input) ---\n"
                f"{str_format_quote(mock_quote)}\n\n"
                f"--- Calculated Quote (Output) ---\n"
                f"{str_format_calculated_quote(calculated_quote_result)}\n"
            )

            with open(file_path, "w") as f:
                f.write(summary_content)
            logger.info(f"Test summary written to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write test summary to file: {e}")
    
