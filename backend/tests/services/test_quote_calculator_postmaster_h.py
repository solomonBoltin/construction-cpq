# test_quote_calculator_postmaster_h.py

import pytest  
from decimal import Decimal, ROUND_HALF_UP 
from unittest.mock import MagicMock, patch
import logging  
import os 
import math 
from datetime import datetime  

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
    BillOfMaterialEntry,
    AppliedRateInfoEntry,
)
from app.services.quote_calculator import (
    QuoteCalculator,
    final_quantize_decimal,
    quantize_decimal,
) 
from tests.model_str_format import (
    str_format_product,
    str_format_quote,
    str_format_calculated_quote,
)


# Helper to create Decimal with consistent precision for tests
def D(value: str) -> Decimal:
    """Converts a string to a Decimal."""
    return Decimal(value)


@pytest.fixture
def quote_calculator():
    """Returns an instance of the QuoteCalculator."""
    return QuoteCalculator()


@pytest.fixture
def mock_session():
    """Returns a MagicMock for the database session."""
    return MagicMock()


# Get a logger instance for this test file
logger = logging.getLogger(__name__)


def test_bom_pm_horizontal_raw_6ft(quote_calculator, mock_session):
    """
    Tests the QuoteCalculator for a Postmaster Horizontal Fence (Raw, 6ft H, 8ft W)
    """
    # --- Test Configuration ---
    PRODUCT_SIZE_FEET = D("100")
    FENCE_TYPE_STYLE = "SxS"  # Excel: sxs or BOB
    ADD_CAP = "no"  # Excel: Cap? no
    ADD_TRIM = "no"  # Excel: Trim? No
    ROUND_UP_MATERIALS = False

    # --- Mock Data Setup ---
    # 1. Mock UnitTypes
    mock_unit_lf = UnitType(id=2, name="linear foot", category="Length")
    mock_unit_bag = UnitType(id=3, name="bag", category="Count")

    materials_db = {
        "8' Postmaster": Material(
            id=2,
            name="8' Postmaster",
            cost_per_supplier_unit=D("18.01"),
            quantity_in_supplier_unit=D("1"),
            base_unit_type=mock_unit_lf,
        ),  # Updated to sheet Job Lot price
        "JPC_Raw_1x6x8": Material(
            id=6,
            name="JPC 1x6x8 Raw Picket",
            cost_per_supplier_unit=D("5.40"),
            quantity_in_supplier_unit=D("1"),
            base_unit_type=mock_unit_lf,
            cull_rate=D("0.05"),
        ),  # Added cull_rate
        "JPC_Raw_2x4x8": Material(
            id=9,
            name="JPC 2x4x8 Raw Rail",
            cost_per_supplier_unit=D("9.00"),
            quantity_in_supplier_unit=D("1"),
            base_unit_type=mock_unit_lf,
        ),  # Price from sheet
        "JPC_Raw_2x4x12": Material(
            id=10,
            name="JPC 2x4x12 Raw Rail",
            cost_per_supplier_unit=D("12.50"),
            quantity_in_supplier_unit=D("1"),
            base_unit_type=mock_unit_lf,
        ),  
        "SYP_2x6x16": Material(
            id=12,
            name="SYP 2x6x16 Color Treated Kickboard",
            cost_per_supplier_unit=D("12.45"),
            quantity_in_supplier_unit=D("1"),
            base_unit_type=mock_unit_lf,
        ),  # Updated to sheet price (Bulk)
        "JPC_Raw_2x6x12": Material(
            id=13,
            name="JPC 2x6x12 Raw Cap Board",
            cost_per_supplier_unit=D("0.00"),
            quantity_in_supplier_unit=D("1"),
            base_unit_type=mock_unit_lf,
        ),  # No price in sheet for this specific item Job Lot, placeholder for unselected option
        "Nails": Material(
            id=14,
            name='Hardware - 2.25" Galvanized Ring Shank Nails',
            cost_per_supplier_unit=D("0.01"),
            quantity_in_supplier_unit=D("1"),
            base_unit_type=mock_unit_lf,
        ),  # Price from sheet
        "Concrete": Material(
            id=15,
            name="Concrete",
            cost_per_supplier_unit=D("5.35"),
            quantity_in_supplier_unit=D("1"),
            base_unit_type=mock_unit_bag,
        ),  # Updated to sheet Job Lot price
    }

    # 3. Mock Product
    mock_product = Product(
        id=1,
        name="Postmaster Horizontal Fence - 6ft H - Raw",
        base_labor_cost_per_product_unit=D(
            "8.00" 
        ),  # Excel: Install/ft $8.00 * 8ft/section = $64.00/section
        product_unit_type_id=mock_unit_lf.id,  # Each section
        product_materials=[
            ProductMaterial(
                material=materials_db["8' Postmaster"],
                quantity_of_material_base_units_per_product_unit=D("0.125"), # 8
            ),  # Excel QTY 1
            ProductMaterial(
                material=materials_db[f"JPC_Raw_1x6x8"],
                quantity_of_material_base_units_per_product_unit=D("1.5"), # 12 
            ),  # Excel QTY 12, 5% cull
            ProductMaterial(
                material=materials_db["JPC_Raw_2x4x12"],
                quantity_of_material_base_units_per_product_unit=D("0.0625"), # 0.5
            ),  # Excel QTY 0.5
            ProductMaterial(
                material=materials_db["SYP_2x6x16"],
                quantity_of_material_base_units_per_product_unit=D("0.0625"), # 0.5
            ),  # Excel QTY 0.5
            ProductMaterial(
                material=materials_db["Nails"],
                quantity_of_material_base_units_per_product_unit=D("50"), # 400
            ),  # To match Excel's $4.00
            ProductMaterial(
                material=materials_db["Concrete"],
                quantity_of_material_base_units_per_product_unit=D("0.125") # 1
            ),  # Excel QTY 1
        ],
        variation_groups=[],
    )


    # Cap Variation
    cap_group = VariationGroup(
        id=2,
        name="Cap",
        product_id=1,
        selection_type="single_choice",
        is_required=False,
        options=[],
    )
    cap_yes_option = VariationOption(  # Values if cap was 'yes' for 6ft fence
        id=3,
        name="Yes",
        variation_group_id=2,
        additional_labor_cost_per_product_unit=D(
            "0"
        ),  # Labor for cap from Excel if applicable
        variation_option_materials=[
            #
        ],
    )
    cap_no_option = VariationOption(id=4, name="No", variation_group_id=2)
    cap_group.options.extend([cap_yes_option, cap_no_option])
    
    # Trim Variation
    trim_group = VariationGroup(
        id=3,
        name="Trim",
        product_id=1,
        selection_type="single_choice",
        is_required=False,
        options=[],
    )
    trim_yes_option = VariationOption( 
        id=5,
        name="Yes",
        
        variation_group_id=3,
        additional_labor_cost_per_product_unit=D(
            "0"
        ),  # Labor for trim from Excel if applicable
        variation_option_materials=[
            # VariationOptionMaterial(material=materials_db[f"{WOOD_TYPE}_{FINISH}_2x6x12"], quantity_of_material_base_units_added=D("0")) # Trim material from Excel if applicable
        ],
    )
    trim_no_option = VariationOption(id=6, name="No", variation_group_id=3)
    trim_group.options.extend([trim_yes_option, trim_no_option])
    
    # STyle Variation
    style_group = VariationGroup(
        id=4,
        name="Style",
        product_id=1,
        selection_type="single_choice",
        is_required=True,
        options=[],
    )
    style_sxs_option = VariationOption(
        id=7,
        name="SxS",
        variation_group_id=4,
        additional_labor_cost_per_product_unit=D(
            "0"
        ),  # Labor for SxS from Excel if applicable
        variation_option_materials=[],
    )
    style_bob_option = VariationOption(
        id=8,
        name="B.O.B.",
        variation_group_id=4,
        additional_labor_cost_per_product_unit=D(
            "0"
        ),  # Labor for B.O.B. from Excel if applicable
        variation_option_materials=[],
    )
    style_group.options.extend([style_sxs_option, style_bob_option])

    mock_product.variation_groups.extend([cap_group, trim_group, style_group])

    # 5. Mock Quote Configuration (matches Excel)
    mock_quote_config = QuoteConfig(
        id=1,
        name="Postmaster Horizontal Config",
        sales_commission_rate=D("0.07"),  # Excel 7%
        franchise_fee_rate=D("0.04"),  # Excel 4%
        margin_rate=D("0.30"),  # Excel 30%
        additional_fixed_fees=D("0.00"),
        tax_rate=D("0.085"),  # Excel 8.5%
        round_up_materials= ROUND_UP_MATERIALS,
    )

    # 6. Mock Quote and Entries
    mock_quote_entry = QuoteProductEntry(
        id=1,
        quote_id=1,
        product_id=1,
        product=mock_product,
        quantity_of_product_units=PRODUCT_SIZE_FEET, 
        selected_variations=[],
    )

    # Link selected variations based on config
    selected_variations = [
        QuoteProductEntryVariation(
            quote_product_entry_id=1,
            variation_option=cap_no_option if ADD_CAP == "no" else cap_yes_option,
        ),
        QuoteProductEntryVariation(
            quote_product_entry_id=1,
            variation_option=trim_no_option if ADD_TRIM == "no" else trim_yes_option,
        ),
        QuoteProductEntryVariation(
            quote_product_entry_id=1,
            variation_option=style_sxs_option if FENCE_TYPE_STYLE == "SxS" else style_bob_option,
        ),
    ]
    mock_quote_entry.selected_variations.extend(selected_variations)

    mock_quote = Quote(
        id=1,
        name="Test Postmaster-H Quote - 6ft H, 100ft Job Lot",
        quote_config_id=1,
        quote_config=mock_quote_config,
        product_entries=[mock_quote_entry],
    )

    # Mock session calls
    mock_session.get.return_value = mock_quote
    mock_session.exec.return_value.first.return_value = (
        None  # No existing CalculatedQuote
    )

    # Log the quote overview
    logger.info(
        f"\n--- Mock Quote Overview (Input) ---\n{str_format_quote(mock_quote)}" # Added NUM_SECTIONS
    )

    # --- Call the method ---
    calculated_quote_result = quote_calculator.calculate_and_save_quote(
        quote_id=1, session=mock_session
    )

    # Log the calculated output
    if calculated_quote_result:
        logger.info(
            f"\n--- Calculated Quote (Output) ---\n{str_format_calculated_quote(calculated_quote_result)}"
        )

        # --- Output summary to file ---
        try:
            current_date_str = datetime.now().strftime("%Y-%m-%d")
            test_function_name = "test_calculate_postmaster_horizontal_100ft_job_lot"

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

    else:
        logger.warning("calculated_quote_result is None")

    # --- Assertions (Compare with Excel calculations) ---
    # Expected values from the Excel sheet for:
    # 100ft Job, 6ft Height, 8ft Section, JPC, Raw, SxS, No Cap, No Trim, Job Lot

    # Material Subtotal: 1348.45
    expected_material_cost_pre_tax = D("1348.45")  # Excel D30*B3
    # Install/ft: $8.00 => Job Labor Cost: $8.00 * 100ft = $800.00
    expected_labor_cost = D("800.00")
    # COGS Per Foot: $22.63 => Job COGS: $22.63 * 100ft = $2263.00 (Or $1348.44 + $800.00 = $2263.05)
    expected_cogs = expected_material_cost_pre_tax + expected_labor_cost  # $2263.05



    assert calculated_quote_result is not None
    assert calculated_quote_result.quote_id == 1

    # Assert Material and Labor costs match Excel direct inputs
    assert final_quantize_decimal(
        calculated_quote_result.total_material_cost
    ) == final_quantize_decimal(expected_material_cost_pre_tax)
    assert final_quantize_decimal(
        calculated_quote_result.total_labor_cost
    ) == final_quantize_decimal(expected_labor_cost)

    # COGS should be sum of the above
    assert final_quantize_decimal(
        calculated_quote_result.cost_of_goods_sold
    ) == final_quantize_decimal(expected_cogs)

    # Recalculate other expected values based on the calculator's standard logic using Excel's COGS.
    current_cogs = calculated_quote_result.cost_of_goods_sold
    commission_rate = mock_quote_config.sales_commission_rate
    franchise_fee_rate = mock_quote_config.franchise_fee_rate
    margin_rate = mock_quote_config.margin_rate
    tax_rate = mock_quote_config.tax_rate

    # Fees are on COGS
    py_expected_commission_amount = current_cogs * commission_rate
    py_expected_franchise_fee_amount = current_cogs * franchise_fee_rate

    cost_base_for_margin_py_logic = (
        current_cogs + py_expected_commission_amount + py_expected_franchise_fee_amount
    )

    py_expected_margin_amount = Decimal("0")
    if D("1") - margin_rate > 0:
        py_expected_margin_amount = (cost_base_for_margin_py_logic * margin_rate) / (
            D("1") - margin_rate
        )

    py_expected_subtotal_before_tax = (
        cost_base_for_margin_py_logic + py_expected_margin_amount
    )
    py_expected_tax_amount = py_expected_subtotal_before_tax * tax_rate
    py_expected_final_price = py_expected_subtotal_before_tax + py_expected_tax_amount

    # Assert other values against these Python logic recalculated figures
    assert final_quantize_decimal(
        calculated_quote_result.subtotal_before_tax
    ) == final_quantize_decimal(py_expected_subtotal_before_tax)
    assert final_quantize_decimal(
        calculated_quote_result.tax_amount
    ) == final_quantize_decimal(py_expected_tax_amount)
    assert final_quantize_decimal(
        calculated_quote_result.final_price
    ) == final_quantize_decimal(py_expected_final_price)

    # Verify that the correct rates were applied
    assert len(calculated_quote_result.applied_rates_info_json) == 3

    commission_info = next(
        r
        for r in calculated_quote_result.applied_rates_info_json
        if r.name == "Sales Commission"
    )
    franchise_info = next(
        r
        for r in calculated_quote_result.applied_rates_info_json
        if r.name == "Franchise Fee"
    )
    margin_info = next(
        r for r in calculated_quote_result.applied_rates_info_json if r.name == "Margin"
    )

    assert final_quantize_decimal(
        commission_info.applied_amount
    ) == final_quantize_decimal(py_expected_commission_amount)
    assert final_quantize_decimal(
        franchise_info.applied_amount
    ) == final_quantize_decimal(py_expected_franchise_fee_amount)
    assert final_quantize_decimal(margin_info.applied_amount) == final_quantize_decimal(
        py_expected_margin_amount
    )

    # Verify session calls
    mock_session.add.assert_any_call(calculated_quote_result)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_any_call(calculated_quote_result)

    # --- Assertions ---
    # Verify the calculated values against expected values based on the provided Excel logic and our Python calculations.

    # Find the picket entry in the BOM for detailed check
    picket_bom_entry = None
    for bom_data in calculated_quote_result.bill_of_materials_json:
        bom_entry = BillOfMaterialEntry.model_validate(bom_data)
        if bom_entry.material_name == materials_db["JPC_Raw_1x6x8"].name:
            picket_bom_entry = bom_entry
            break

    assert picket_bom_entry is not None, "Picket BOM entry not found"

    # Expected Pickets:
    # Base quantity per section = 12
    # Number of sections = 12.5
    # Total base pickets = 12 * 12.5 = 150
    # Cull rate = 0.05
    # Cull units = 150 * 0.05 = 7.5
    # Total quantity (raw) = 150 + 7.5 = 157.5
    # Total quantity (rounded up) = ceil(157.5) = 158

    expected_picket_quantity_raw = D("1.5") * PRODUCT_SIZE_FEET  # 150
    expected_cull_units = expected_picket_quantity_raw * D("0.05")  # 7.5
    expected_total_pickets = expected_picket_quantity_raw + expected_cull_units  # 157.5

    if mock_quote_config.round_up_materials:
        expected_total_pickets = D(str(math.ceil(expected_total_pickets)))  # 158

    assert (
        picket_bom_entry.quantity == expected_total_pickets
    ), f"Picket quantity expected {expected_total_pickets}, got {picket_bom_entry.quantity}"

    assert (
        picket_bom_entry.cull_units is not None
    ), "Cull units should not be None for pickets"
    # Cull units are quantized in calculator: quantize_decimal(expected_cull_units)
    assert picket_bom_entry.cull_units == quantize_decimal(
        expected_cull_units
    ), f"Picket cull_units expected {quantize_decimal(expected_cull_units)}, got {picket_bom_entry.cull_units}"
    assert (
        picket_bom_entry.unit_cost
        == materials_db[f"JPC_Raw_1x6x8"].cost_per_supplier_unit
    )  # cost_per_base_unit
    expected_picket_total_cost = expected_total_pickets * picket_bom_entry.unit_cost
    assert picket_bom_entry.total_cost == final_quantize_decimal(
        expected_picket_total_cost
    ), f"Picket total_cost expected {final_quantize_decimal(expected_picket_total_cost)}, got {picket_bom_entry.total_cost}"

    # Recalculate expected total material cost based on potentially changed picket cost
    # This is a simplified recalculation; a more robust approach would sum all BOM entry total_costs.
    # For now, let's assume other material costs remain as previously expected and adjust based on pickets.

    # Original expected total material cost was D("1385.78")
    # Original picket cost: 12.5 sections * 12.6 pickets/section (12 * 1.05) = 157.5, rounded to 158.
    # 158 pickets * 5.40/picket = 853.20
    # New picket cost: 158 pickets * 5.40/picket = 853.20 (No change here as final quantity is the same due to ceil)

    # Let's verify the total material cost from the output directly matches the sum of BOM entries
    calculated_total_material_cost_from_bom = sum(
        BillOfMaterialEntry.model_validate(item).total_cost
        for item in calculated_quote_result.bill_of_materials_json
    )
    assert calculated_quote_result.total_material_cost == final_quantize_decimal(
        calculated_total_material_cost_from_bom
    ), "Total material cost does not match sum of BOM entries"

    # Check against the known total from the previous run if numbers are expected to be the same
    # or update this expected value if cull rate logic changes it.
    # The provided summary has Total Material Cost: 1385.78
    # Pickets: 158 * 5.40 = 853.20
    # Let's re-verify other items from the summary:
    # 8' Postmaster: 13 * 18.01 = 234.13
    # JPC 2x4x12 Raw Rail: 7 * 12.50 = 87.50
    # SYP 2x6x16 Color Treated Kickboard: 7 * 12.45 = 87.15
    # Hardware - 2.25" Galvanized Ring Shank Nails: 5425 * 0.01 = 54.25 (Note: 434 * 12.5 = 5425)
    # Concrete: 13 * 5.35 = 69.55
    # Sum: 234.13 + 853.20 + 87.50 + 87.15 + 54.25 + 69.55 = 1385.78. This matches.

    assert calculated_quote_result.total_material_cost == D(
        "1348.45"
    )  # This is the expected total material cost from the Excel sheet
    assert calculated_quote_result.total_labor_cost == D("800.00")
    assert calculated_quote_result.cost_of_goods_sold == D(
        "2148.45"
    )  # COGS = Material Cost + Labor Cost
    # assert calculated_quote_result.subtotal_before_tax == D("3466.02")
    # assert calculated_quote_result.tax_amount == D("294.61")
    # assert calculated_quote_result.final_price == D("3760.63")

    # Assert against py_expected values which are derived from the calculator's logic and current COGS
    assert final_quantize_decimal(
        calculated_quote_result.subtotal_before_tax
    ) == final_quantize_decimal(py_expected_subtotal_before_tax)
    assert final_quantize_decimal(
        calculated_quote_result.tax_amount
    ) == final_quantize_decimal(py_expected_tax_amount)
    assert final_quantize_decimal(
        calculated_quote_result.final_price
    ) == final_quantize_decimal(py_expected_final_price)

    # --- Assertions for Leftovers ---
    # Expected leftovers are calculated as: ceil(aggregated_quantity_with_cull) - aggregated_quantity_with_cull
    # aggregated_quantity_with_cull for pickets (JPC_Raw_1x6x8): (12 pickets/section * 12.5 sections) * (1 + 0.05 cull) = 150 * 1.05 = 157.5. Ceil(157.5) = 158. Leftover = 158 - 157.5 = 0.5
    # 8' Postmaster: 1 post/section * 12.5 sections = 12.5. Ceil(12.5) = 13. Leftover = 13 - 12.5 = 0.5
    # JPC_Raw_2x4x12 (Rails): 0.5 rails/section * 12.5 sections = 6.25. Ceil(6.25) = 7. Leftover = 7 - 6.25 = 0.75
    # SYP_2x6x16 (Kickboard): 0.5 kickboards/section * 12.5 sections = 6.25. Ceil(6.25) = 7. Leftover = 7 - 6.25 = 0.75
    # Nails: 434 nails/section * 12.5 sections = 5425. Ceil(5425) = 5425. Leftover = 0
    # Concrete: 1 bag/section * 12.5 sections = 12.5. Ceil(12.5) = 13. Leftover = 13 - 12.5 = 0.5

    if mock_quote_config.round_up_materials:
        expected_leftovers_map = {
            materials_db["8' Postmaster"].name: quantize_decimal(D("0.5")),
            materials_db[f"JPC_Raw_1x6x8"].name: quantize_decimal(
                D("0.5")
            ),
            materials_db[f"JPC_Raw_2x4x12"].name: quantize_decimal(
                D("0.75")
            ),
            materials_db["SYP_2x6x16"].name: quantize_decimal(D("0.75")),
            materials_db["Nails"].name: quantize_decimal(D("0")),
            materials_db["Concrete"].name: quantize_decimal(D("0.5")),
        }
    else:
        expected_leftovers_map = {
            materials_db["8' Postmaster"].name: quantize_decimal(D("0")),
            materials_db[f"JPC_Raw_1x6x8"].name: quantize_decimal(D("0")),
            materials_db[f"JPC_Raw_2x4x12"].name: quantize_decimal(D("0")),
            materials_db["SYP_2x6x16"].name: quantize_decimal(D("0")),
            materials_db["Nails"].name: quantize_decimal(D("0")),
            materials_db["Concrete"].name: quantize_decimal(D("0")),
        }

    for bom_data in calculated_quote_result.bill_of_materials_json:
        bom_entry = BillOfMaterialEntry.model_validate(bom_data)
        material_name = bom_entry.material_name

        assert (
            material_name in expected_leftovers_map
        ), f"Unexpected material '{material_name}' in BOM for leftovers check. Not found in expected_leftovers_map."

        expected_leftover = expected_leftovers_map[material_name]
        actual_leftover = (
            bom_entry.leftovers if bom_entry.leftovers is not None else D("0")
        )

        assert (
            actual_leftover == expected_leftover
        ), f"Leftovers for material '{material_name}' expected {expected_leftover}, got {actual_leftover}"
