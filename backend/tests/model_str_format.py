from decimal import Decimal
from app.models import (
    Product,
    Quote,
    CalculatedQuote,
    AppliedRateInfoEntry,
    BillOfMaterialEntry,
    # Ensure all potentially accessed sub-models like Material, UnitType, etc., are implicitly available
    # through the main models or are not directly type-hinted if not imported.
)

# Helper to create Decimal with consistent precision, if needed elsewhere, otherwise remove.
def D(value: str) -> Decimal:
    """Converts a string to a Decimal."""
    return Decimal(value)

def str_format_product(product: Product, num_sections: Decimal) -> str:
    """Formats Product details for readable logging."""
    log_lines = [f"  Product: {product.name} (ID: {product.id})"]
    log_lines.append(
        f"    Base Labor per Section: {product.unit_labor_cost}"
    )
    log_lines.append("    Base Materials (per section):")
    if hasattr(product, 'product_materials'):
        for pm in product.product_materials:
            qty_per_section = pm.material_amount
            if hasattr(pm, 'material') and pm.material and hasattr(pm.material, 'name') and "Nails" in pm.material.name:
                if num_sections != Decimal("0"):
                    # Original logic: (pm.material_amount * num_sections / num_sections)
                    # This simplifies to pm.material_amount, assuming it means quantity for the whole job.
                    # If it means quantity per section that needs scaling, the formula would be different.
                    # Sticking to the literal interpretation of the formula provided which simplifies.
                    qty_per_section = pm.material_amount
                else:
                    qty_per_section = pm.material_amount # Avoid division by zero

            log_lines.append(
                f"      - {pm.material.name}: {qty_per_section} {pm.material.base_unit_type.name} @ {pm.material.cost_per_supplier_unit}/{pm.material.quantity_in_supplier_unit} {pm.material.base_unit_type.name}"
            )

    log_lines.append("    Variation Groups:")
    if hasattr(product, 'variation_groups'):
        for group in product.variation_groups:
            log_lines.append(
                f"      Group: {group.name} (Required: {group.is_required}, Type: {group.selection_type})"
            )
            if hasattr(group, 'options'):
                for option in group.options:
                    log_lines.append(f"        Option: {option.name}")
                    log_lines.append(
                        f"          Additional Labor per Section: {option.additional_labor_cost_per_product_unit}"
                    )
                    if hasattr(option, 'variation_option_materials') and option.variation_option_materials:
                        log_lines.append("          Materials Added/Modified (per section):")
                        for vom in option.variation_option_materials:
                            log_lines.append(
                                f"            - {vom.material.name}: {vom.quantity_of_material_base_units_added} {vom.material.base_unit_type.name}"
                            )
    return "\n".join(log_lines)

def str_format_quote(quote: Quote) -> str:
    """Formats Quote details for readable logging."""
    log_lines = [f"Quote: {quote.name} (ID: {quote.id})"]
    if hasattr(quote, 'quote_config') and quote.quote_config:
        log_lines.append(
            f"  Config: {quote.quote_config.name} (ID: {quote.quote_config.id})"
        )
        log_lines.append(
            f"    Sales Commission Rate: {quote.quote_config.sales_commission_rate:%}"
        )
        log_lines.append(
            f"    Franchise Fee Rate: {quote.quote_config.franchise_fee_rate:%}"
        )
        log_lines.append(f"    Margin Rate: {quote.quote_config.margin_rate:%}")
        log_lines.append(f"    Tax Rate: {quote.quote_config.tax_rate:%}")
        log_lines.append(
            f"    Additional Fixed Fees: {quote.quote_config.additional_fixed_fees}"
        )

    log_lines.append("  Product Entries:")
    if hasattr(quote, 'product_entries'):
        for entry in quote.product_entries:
            log_lines.append(f"    Entry ID: {entry.id}")
            if hasattr(entry, 'product') and entry.product:
                log_lines.append(
                    f"      Product: {entry.product.name} (ID: {entry.product.id})"
                )
                log_lines.append(
                    f"      Quantity of Product Units (Sections): {entry.quantity_of_product_units}"
                )
                # Use entry.quantity_of_product_units as num_sections for this specific product entry
                log_lines.append(
                    str_format_product(entry.product, entry.quantity_of_product_units)
                ) 
            log_lines.append("      Selected Variations:")
            if hasattr(entry, 'selected_variations'):
                for qpev in entry.selected_variations:
                    # Ensure path to names is correct and safe
                    group_name = getattr(getattr(getattr(qpev, 'variation_option', {}), 'variation_group', {}), 'name', 'N/A')
                    option_name = getattr(getattr(qpev, 'variation_option', {}), 'name', 'N/A')
                    log_lines.append(
                        f"        - {group_name}: {option_name}"
                    )
    return "\n".join(log_lines)

def str_format_calculated_quote(calculated_quote: CalculatedQuote) -> str:
    """Formats CalculatedQuote details for readable logging."""
    log_lines = [
        f"Calculated Quote (ID: {calculated_quote.id}, For Quote ID: {calculated_quote.quote_id})"
    ]
    log_lines.append(
        f"  Total Material Cost: {calculated_quote.total_material_cost:.2f}"
    )
    log_lines.append(f"  Total Labor Cost: {calculated_quote.total_labor_cost:.2f}")
    log_lines.append(
        f"  Cost of Goods Sold (COGS): {calculated_quote.cost_of_goods_sold:.2f}"
    )
    log_lines.append("  Applied Rates & Fees:")
    if isinstance(
        calculated_quote.applied_rates_info_json, list
    ):
        for rate_info_data in calculated_quote.applied_rates_info_json:
            rate_info = None
            if isinstance(rate_info_data, dict):
                try:
                    rate_info = AppliedRateInfoEntry(**rate_info_data)
                except Exception as e:
                    log_lines.append(f"    - Error creating AppliedRateInfoEntry from dict: {rate_info_data}, Error: {e}")
                    continue
            elif isinstance(rate_info_data, AppliedRateInfoEntry):
                rate_info = rate_info_data
            else:
                log_lines.append(f"    - Unknown type for rate_info_data: {type(rate_info_data)}")
                continue
            
            # Ensure rate_info is not None before proceeding
            if rate_info is None:
                log_lines.append(f"    - Failed to process rate_info_data: {rate_info_data}")
                continue # Skip to the next item if rate_info could not be determined

            log_lines.append(f"    - Name: {rate_info.name}") # Corrected: rate_info.name
            log_lines.append(f"      Type: {rate_info.type}")
            log_lines.append(
                f"      Rate Value: {Decimal(rate_info.rate_value):.4f}"
            )
            log_lines.append(
                f"      Applied Amount: {Decimal(rate_info.applied_amount):.2f}"
            )

    log_lines.append(
        f"  Subtotal Before Tax: {calculated_quote.subtotal_before_tax:.2f}"
    )
    log_lines.append(f"  Tax Amount: {calculated_quote.tax_amount:.2f}")
    log_lines.append(f"  Final Price: {calculated_quote.final_price:.2f}")
    log_lines.append("  Bill of Materials:")
    if isinstance(calculated_quote.bill_of_materials_json, list):
        for bom_entry_data in calculated_quote.bill_of_materials_json:
            bom_entry = None
            if isinstance(bom_entry_data, dict):
                try:
                    if hasattr(BillOfMaterialEntry, 'model_validate'): # Pydantic v2
                        bom_entry = BillOfMaterialEntry.model_validate(bom_entry_data)
                    elif hasattr(BillOfMaterialEntry, 'parse_obj'): # Pydantic v1
                        bom_entry = BillOfMaterialEntry.parse_obj(bom_entry_data)
                    else: # Standard class
                        bom_entry = BillOfMaterialEntry(**bom_entry_data)
                except Exception as e:
                    log_lines.append(f"    - Error creating BillOfMaterialEntry from dict: {bom_entry_data}, Error: {e}")
                    continue
            elif isinstance(bom_entry_data, BillOfMaterialEntry):
                bom_entry = bom_entry_data
            else:
                log_lines.append(f"    - Unknown type for bom_entry_data: {type(bom_entry_data)}")
                continue
            
            if bom_entry is None:
                log_lines.append(f"    - Failed to process bom_entry_data: {bom_entry_data}")
                continue

            log_lines.append(f"    - Material: {bom_entry.material_name}")
            log_lines.append(
                f"      Quantity: {bom_entry.quantity} {bom_entry.unit_name}"
            )
            log_lines.append(f"      Unit Cost: {bom_entry.unit_cost:.2f}")
            log_lines.append(f"      Total Cost: {bom_entry.total_cost:.2f}")
            if hasattr(bom_entry, 'cull_units') and bom_entry.cull_units is not None and bom_entry.cull_units > 0:
                log_lines.append(
                    f"      Cull Units: {bom_entry.cull_units} {bom_entry.unit_name}"
                )
            if hasattr(bom_entry, 'leftovers') and bom_entry.leftovers is not None and bom_entry.leftovers > D("0"):
                log_lines.append(
                    f"      Leftovers: {bom_entry.leftovers} {bom_entry.unit_name}"
                )
    return "\n".join(log_lines)
