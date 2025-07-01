from decimal import Decimal
from app.models import (
    Product,
    Quote,
    CalculatedQuote,
    AppliedRateInfoEntry,
    BillOfMaterialEntry,
    Material,
    UnitType,
    ProductMaterial,
    VariationGroup,
    VariationOption,
    VariationOptionMaterial,
    QuoteConfig,
    QuoteProductEntry,
    QuoteProductEntryVariation
)
import pytest

def D(value: str) -> Decimal:
    return Decimal(value)

def str_format_product(product: Product, num_sections: Decimal) -> str:
    log_lines = [f"  Product: {getattr(product, 'name', 'N/A')} (ID: {getattr(product, 'id', 'N/A')})"]
    log_lines.append(
        f"    Base Labor per Section: {getattr(product, 'unit_labor_cost', 'N/A')}"
    )
    log_lines.append("    Base Materials (per section):")
    if hasattr(product, 'product_materials') and product.product_materials:
        for pm in product.product_materials:
            qty_per_section = getattr(pm, 'material_amount', D('0'))
            material_name = getattr(getattr(pm, 'material', {}), 'name', 'N/A')
            unit_type_name = getattr(getattr(getattr(pm, 'material', {}), 'unit_type', {}), 'name', 'N/A')
            cost_per_supplier_unit = getattr(getattr(pm, 'material', {}), 'cost_per_supplier_unit', D('0'))
            quantity_in_supplier_unit = getattr(getattr(pm, 'material', {}), 'quantity_in_supplier_unit', D('1'))


            if "Nails" in material_name: # Simplified logic for nails, assuming qty_per_section is correct as is
                pass # qty_per_section already set

            log_lines.append(
                f"      - {material_name}: {qty_per_section} {unit_type_name} @ {cost_per_supplier_unit}/{quantity_in_supplier_unit} {unit_type_name}"
            )

    log_lines.append("    Variation Groups:")
    if hasattr(product, 'variation_groups') and product.variation_groups:
        for group in product.variation_groups:
            log_lines.append(
                f"      Group: {getattr(group, 'name', 'N/A')} (Required: {getattr(group, 'is_required', 'N/A')}, Type: {getattr(group, 'selection_type', 'N/A')})"
            )
            if hasattr(group, 'options') and group.options:
                for option in group.options:
                    log_lines.append(f"        Option: {getattr(option, 'name', 'N/A')}")
                    log_lines.append(
                        f"          Additional Labor per Section: {getattr(option, 'additional_labor_cost_per_product_unit', D('0'))}"
                    )
                    if hasattr(option, 'variation_option_materials') and option.variation_option_materials:
                        log_lines.append("          Materials Added/Modified (per section):")
                        for vom in option.variation_option_materials:
                            vom_material_name = getattr(getattr(vom, 'material', {}), 'name', 'N/A')
                            vom_unit_type_name = getattr(getattr(getattr(vom, 'material', {}), 'unit_type', {}), 'name', 'N/A')
                            log_lines.append(
                                f"            - {vom_material_name}: {getattr(vom, 'quantity_of_material_base_units_added', D('0'))} {vom_unit_type_name}"
                            )
    return "\\n".join(log_lines)

def str_format_quote(quote: Quote) -> str:
    log_lines = [f"Quote: {getattr(quote, 'name', 'N/A')} (ID: {getattr(quote, 'id', 'N/A')})"]
    if hasattr(quote, 'quote_config') and quote.quote_config:
        quote_config = quote.quote_config
        log_lines.append(
            f"  Config: {getattr(quote_config, 'name', 'N/A')} (ID: {getattr(quote_config, 'id', 'N/A')})"
        )
        log_lines.append(
            f"    Sales Commission Rate: {getattr(quote_config, 'sales_commission_rate', D('0')):%}"
        )
        log_lines.append(
            f"    Franchise Fee Rate: {getattr(quote_config, 'franchise_fee_rate', D('0')):%}"
        )
        log_lines.append(f"    Margin Rate: {getattr(quote_config, 'margin_rate', D('0')):%}")
        log_lines.append(f"    Tax Rate: {getattr(quote_config, 'tax_rate', D('0')):%}")
        log_lines.append(
            f"    Additional Fixed Fees: {getattr(quote_config, 'additional_fixed_fees', D('0'))}"
        )

    log_lines.append("  Product Entries:")
    if hasattr(quote, 'product_entries') and quote.product_entries:
        for entry in quote.product_entries:
            log_lines.append(f"    Entry ID: {getattr(entry, 'id', 'N/A')}")
            if hasattr(entry, 'product') and entry.product:
                product_entry_product = entry.product
                log_lines.append(
                    f"      Product: {getattr(product_entry_product, 'name', 'N/A')} (ID: {getattr(product_entry_product, 'id', 'N/A')})"
                )
                quantity_of_product_units = getattr(entry, 'quantity_of_product_units', D('0'))
                log_lines.append(
                    f"      Quantity of Product Units (Sections): {quantity_of_product_units}"
                )
                log_lines.append(
                    str_format_product(product_entry_product, quantity_of_product_units)
                ) 
            log_lines.append("      Selected Variations:")
            if hasattr(entry, 'selected_variations') and entry.selected_variations:
                for qpev in entry.selected_variations:
                    variation_option = getattr(qpev, 'variation_option', None)
                    group_name = getattr(getattr(variation_option, 'variation_group', {}), 'name', 'N/A') if variation_option else 'N/A'
                    option_name = getattr(variation_option, 'name', 'N/A') if variation_option else 'N/A'
                    log_lines.append(
                        f"        - {group_name}: {option_name}"
                    )
    return "\\n".join(log_lines)

def str_format_calculated_quote(calculated_quote: CalculatedQuote) -> str:
    log_lines = [
        f"Calculated Quote (ID: {getattr(calculated_quote, 'id', 'N/A')}, For Quote ID: {getattr(calculated_quote, 'quote_id', 'N/A')})"
    ]
    log_lines.append(
        f"  Total Material Cost: {getattr(calculated_quote, 'total_material_cost', D('0')):.2f}"
    )
    log_lines.append(f"  Total Labor Cost: {getattr(calculated_quote, 'total_labor_cost', D('0')):.2f}")
    log_lines.append(
        f"  Cost of Goods Sold (COGS): {getattr(calculated_quote, 'cost_of_goods_sold', D('0')):.2f}"
    )
    log_lines.append("  Applied Rates & Fees:")
    
    applied_rates_info_json = getattr(calculated_quote, 'applied_rates_info_json', [])
    if isinstance(applied_rates_info_json, list):
        for rate_info_data in applied_rates_info_json:
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
            
            if rate_info is None:
                log_lines.append(f"    - Failed to process rate_info_data: {rate_info_data}")
                continue

            log_lines.append(f"    - Name: {getattr(rate_info, 'name', 'N/A')}")
            log_lines.append(f"      Type: {getattr(rate_info, 'type', 'N/A')}")
            log_lines.append(
                f"      Rate Value: {Decimal(getattr(rate_info, 'rate_value', '0')):.4f}"
            )
            log_lines.append(
                f"      Applied Amount: {Decimal(getattr(rate_info, 'applied_amount', '0')):.2f}"
            )

    log_lines.append(
        f"  Subtotal Before Tax: {getattr(calculated_quote, 'subtotal_before_tax', D('0')):.2f}"
    )
    log_lines.append(f"  Tax Amount: {getattr(calculated_quote, 'tax_amount', D('0')):.2f}")
    log_lines.append(f"  Final Price: {getattr(calculated_quote, 'final_price', D('0')):.2f}")
    log_lines.append("  Bill of Materials:")

    bill_of_materials_json = getattr(calculated_quote, 'bill_of_materials_json', [])
    if isinstance(bill_of_materials_json, list):
        for bom_entry_data in bill_of_materials_json:
            bom_entry = None
            if isinstance(bom_entry_data, dict):
                try:
                    if hasattr(BillOfMaterialEntry, 'model_validate'):
                        bom_entry = BillOfMaterialEntry.model_validate(bom_entry_data)
                    elif hasattr(BillOfMaterialEntry, 'parse_obj'):
                        bom_entry = BillOfMaterialEntry.parse_obj(bom_entry_data) # type: ignore
                    else:
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

            log_lines.append(f"    - Material: {getattr(bom_entry, 'material_name', 'N/A')}")
            log_lines.append(
                f"      Quantity: {getattr(bom_entry, 'quantity', D('0'))} {getattr(bom_entry, 'unit_name', 'N/A')}"
            )
            log_lines.append(f"      Unit Cost: {getattr(bom_entry, 'unit_cost', D('0')):.2f}")
            log_lines.append(f"      Total Cost: {getattr(bom_entry, 'total_cost', D('0')):.2f}")
            
            cull_units = getattr(bom_entry, 'cull_units', D('0'))
            if cull_units is not None and cull_units > D("0"):
                log_lines.append(
                    f"      Cull Units: {cull_units} {getattr(bom_entry, 'unit_name', 'N/A')}"
                )
            
            leftovers = getattr(bom_entry, 'leftovers', D('0'))
            if leftovers is not None and leftovers > D("0"):
                log_lines.append(
                    f"      Leftovers: {leftovers} {getattr(bom_entry, 'unit_name', 'N/A')}"
                )
    return "\\n".join(log_lines)
