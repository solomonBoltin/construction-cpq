"""
Comprehensive E2E quote calculation scenario test.
"""
import httpx
from decimal import Decimal
from .cpq_api_e2e import client, create_entity, quantize_d, created_entities # Import client, helpers and created_entities

def test_e2e_full_quote_calculation_scenario(client: httpx.Client):
    print("\\nTest: E2E Full Quote Calculation Scenario...")

    # --- 1. Get or Create Seeded Data IDs (Unit Types) ---
    print("  Fetching/Creating unit types...")
    ut_each = create_entity(client, "unit_types", {"name": "Test E2E - Each", "category": "Quantity", "description": "Each unit"}, "unit_type")
    ut_each_id = ut_each["id"]
    
    ut_lft = create_entity(client, "unit_types", {"name": "Test E2E - Linear Foot", "category": "Length", "description": "Linear Foot unit"}, "unit_type")
    ut_lft_id = ut_lft["id"]

    # --- 2. Create Materials ---
    print("  Creating test-specific materials...")
    material1_payload = {
        "name": "Test E2E - Picket Type A", "description": "Standard wood picket",
        "cost_per_supplier_unit": "1.50", "unit_type_id": ut_each_id,
        "quantity_in_supplier_unit": "1"
    }
    material1 = create_entity(client, "materials", material1_payload, "material")
    material1_id = material1["id"]

    material2_payload = {
        "name": "Test E2E - 2x4 Rail", "description": "Pressure-treated 2x4 rail",
        "cost_per_supplier_unit": "8.00", "unit_type_id": ut_lft_id,
        "quantity_in_supplier_unit": "8"
    }
    material2 = create_entity(client, "materials", material2_payload, "material")
    material2_id = material2["id"]

    # --- 3. Create Product: "Basic Fence Section" ---
    print("  Creating product 'Test E2E - Basic Fence Section'...")
    product_payload = {
        "name": "Test E2E - Basic Fence Section", "description": "A simple fence section",
        "product_unit_type_id": ut_lft_id,
        "unit_labor_cost": "10.00"
    }
    product = create_entity(client, "products", product_payload, "product")
    product_id = product["id"]

    # --- 4. Create ProductMaterials for "Basic Fence Section" ---
    print("  Creating product materials...")
    pm1_payload = {"product_id": product_id, "material_id": material1_id, "material_amount": "2.5"}
    pm1_response = client.post("/product_materials/", json=pm1_payload)
    assert pm1_response.status_code == 200, f"Failed to create PM1: {pm1_response.text}"
    pm1_id = pm1_response.json()["id"]
    created_entities.append({"type": "product_material", "id": pm1_id, "name": f"PM for Product {product_id} Material {material1_id}"})
    
    pm2_payload = {"product_id": product_id, "material_id": material2_id, "material_amount": "0.375"}
    pm2_response = client.post("/product_materials/", json=pm2_payload)
    assert pm2_response.status_code == 200, f"Failed to create PM2: {pm2_response.text}"
    pm2_id = pm2_response.json()["id"]
    created_entities.append({"type": "product_material", "id": pm2_id, "name": f"PM for Product {product_id} Material {material2_id}"})

    # --- 5. Create Variation Group for Product ---
    print("  Creating variation group 'Fence Style'...")
    vg_payload = {"product_id": product_id, "name": "Test E2E - Fence Style", "selection_type": "SINGLE_SELECT", "is_required": True}
    vg = create_entity(client, "variation_groups", vg_payload, "variation_group")
    vg_id = vg["id"]

    # --- 6. Create Variation Options ---
    print("  Creating variation options...")
    vo1_payload = {
        "variation_group_id": vg_id, "name": "Test E2E - Board-on-Board",
        "additional_price": "0.00", 
        "price_multiplier": "1.0",
        "additional_labor_cost_per_product_unit": "2.00"
    }
    vo1 = create_entity(client, "variation_options", vo1_payload, "variation_option")
    vo1_id = vo1["id"]
    
    vom1_payload = {"variation_option_id": vo1_id, "material_id": material1_id, "quantity_of_material_base_units_added": "1.0"}
    vom1_response = client.post("/variation_option_materials/", json=vom1_payload)
    assert vom1_response.status_code == 200, f"Failed to create VOM1: {vom1_response.text}"
    vom1_id = vom1_response.json()["id"]
    created_entities.append({"type": "variation_option_material", "id": vom1_id, "name": f"VOM for VO {vo1_id} Material {material1_id}"})

    vo2_payload = {
        "variation_group_id": vg_id, "name": "Test E2E - Standard Style",
        "additional_price": "0.00", "price_multiplier": "1.0",
        "additional_labor_cost_per_product_unit": "0.00"
    }
    create_entity(client, "variation_options", vo2_payload, "variation_option")

    # --- 7. Create Quote Configuration ---
    print("  Creating quote configuration 'E2E Test Config'...")
    quote_config_payload = {
        "name": "Test E2E - Quote Config", "margin_rate": "0.20", "tax_rate": "0.10",
        "sales_commission_rate": "0.05", "franchise_fee_rate": "0.02",
        "additional_fixed_fees": "50.00"
    }
    quote_config = create_entity(client, "quote_configs", quote_config_payload, "quote_config")
    quote_config_id = quote_config["id"]

    # --- 8. Create a Quote ---
    print("  Creating quote 'E2E Test Quote'...")
    quote_payload = {"name": "Test E2E - Quote", "quote_config_id": quote_config_id}
    quote = create_entity(client, "quotes", quote_payload, "quote")
    quote_id = quote["id"]

    # --- 9. Add Product Entry to Quote ---
    print("  Adding product entry to quote...")
    qpe_payload = {"quote_id": quote_id, "product_id": product_id, "quantity_of_product_units": "10"}
    qpe_response = client.post("/quote_product_entries/", json=qpe_payload)
    assert qpe_response.status_code == 200, f"Failed to create QPE: {qpe_response.text}"
    qpe_data = qpe_response.json()
    qpe_id = qpe_data["id"]
    created_entities.append({"type": "quote_product_entry", "id": qpe_id, "name": f"QPE for Quote {quote_id}"})

    # --- 10. Select Variation for Product Entry ---
    print("  Selecting variation for product entry...")
    qpev_payload = {"quote_product_entry_id": qpe_id, "variation_option_id": vo1_id}
    qpev_response = client.post("/quote_product_entry_variations/", json=qpev_payload)
    assert qpev_response.status_code == 200, f"Failed to create QPEV: {qpev_response.text}"

    # --- 11. Trigger Quote Calculation ---
    print(f"  Triggering calculation for quote ID {quote_id}...")
    calc_response = client.post(f"/quotes/{quote_id}/calculate")
    assert calc_response.status_code == 200, f"Quote calculation failed: {calc_response.text}"
    calculated_quote = calc_response.json()
    print("  Quote calculation successful. Verifying details...")

    # --- 12. Verify CalculatedQuote Details ---
    expected_total_material_cost = Decimal("56.25")
    assert quantize_d(calculated_quote["total_material_cost"]) == expected_total_material_cost

    expected_total_labor_cost = Decimal("120.00")
    assert quantize_d(calculated_quote["total_labor_cost"]) == expected_total_labor_cost

    expected_cogs = Decimal("176.25")
    assert quantize_d(calculated_quote["cost_of_goods_sold"]) == expected_cogs

    raw_subtotal_before_tax_for_calc = Decimal("285.734375")
    expected_subtotal_before_tax_field = quantize_d(raw_subtotal_before_tax_for_calc)
    assert quantize_d(calculated_quote["subtotal_before_tax"]) == expected_subtotal_before_tax_field

    raw_tax_amount_for_calc = raw_subtotal_before_tax_for_calc * Decimal(quote_config_payload["tax_rate"])
    expected_tax_amount_field = quantize_d(raw_tax_amount_for_calc)
    assert quantize_d(calculated_quote["tax_amount"]) == expected_tax_amount_field

    expected_final_price = quantize_d(raw_subtotal_before_tax_for_calc + raw_tax_amount_for_calc)
    assert quantize_d(calculated_quote["final_price"]) == expected_final_price

    bom = calculated_quote["bill_of_materials_json"]
    assert len(bom) == 2

    picket_bom_entry = next((item for item in bom if item["material_name"] == "Test E2E - Picket Type A"), None)
    assert picket_bom_entry is not None
    assert quantize_d(picket_bom_entry["quantity"], "0.001") == quantize_d("35.000", "0.001")
    assert quantize_d(picket_bom_entry["unit_cost"]) == quantize_d("1.50")
    assert quantize_d(picket_bom_entry["total_cost"]) == quantize_d("52.50")

    rail_bom_entry = next((item for item in bom if item["material_name"] == "Test E2E - 2x4 Rail"), None)
    assert rail_bom_entry is not None
    assert quantize_d(rail_bom_entry["quantity"], "0.001") == quantize_d("3.750", "0.001")
    assert quantize_d(rail_bom_entry["unit_cost"]) == quantize_d("1.00") 
    assert quantize_d(rail_bom_entry["total_cost"]) == quantize_d("3.75")
    
    applied_rates = calculated_quote["applied_rates_info_json"]
    sales_comm_rate = Decimal(quote_config_payload["sales_commission_rate"])
    if sales_comm_rate > 0:
        sales_comm_entry = next((rate for rate in applied_rates if rate["name"] == "Sales Commission"), None)
        assert sales_comm_entry is not None
        assert quantize_d(sales_comm_entry["applied_amount"]) == quantize_d(expected_cogs * sales_comm_rate)

    franchise_fee_rate = Decimal(quote_config_payload["franchise_fee_rate"])
    if franchise_fee_rate > 0:
        franchise_fee_entry = next((rate for rate in applied_rates if rate["name"] == "Franchise Fee"), None)
        assert franchise_fee_entry is not None
        assert quantize_d(franchise_fee_entry["applied_amount"]) == quantize_d(expected_cogs * franchise_fee_rate)

    margin_rate_val = Decimal(quote_config_payload["margin_rate"])
    if margin_rate_val > 0:
        margin_entry = next((rate for rate in applied_rates if rate["name"] == "Margin"), None)
        assert margin_entry is not None
        assert Decimal(margin_entry["applied_amount"]) > 0

    additional_fixed_fees_val = Decimal(quote_config_payload["additional_fixed_fees"])
    if additional_fixed_fees_val > 0:
        fixed_fee_entry = next((rate for rate in applied_rates if rate["name"] == "Additional Fixed Fees"), None)
        assert fixed_fee_entry is not None
        assert quantize_d(fixed_fee_entry["applied_amount"]) == quantize_d(additional_fixed_fees_val)

    print("E2E Full Quote Calculation Scenario test completed successfully.")
