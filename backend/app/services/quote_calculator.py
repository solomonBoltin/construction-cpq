from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple
from datetime import datetime, timezone
import logging
import math # Add this import

from sqlmodel import Session, select

from app.models import (
    Quote,
    QuoteProductEntry,
    ProductMaterial,
    VariationOptionMaterial,
    Material,
    CalculatedQuote,
    CalculatedQuoteBase,
    BillOfMaterialEntry,
    AppliedRateInfoEntry,
    UnitType,
)

# Helper to get a Decimal with a specific precision (e.g., for currency)
def quantize_decimal(value: Decimal, precision: str = "0.0001") -> Decimal: 
    return value.quantize(Decimal(precision), rounding=ROUND_HALF_UP)

def final_quantize_decimal(value: Decimal, precision: str = "0.01") -> Decimal: 
    return value.quantize(Decimal(precision), rounding=ROUND_HALF_UP)

# Explicitly configure logger for this module
logger = logging.getLogger("app.services.quote_calculator")
logger.setLevel(logging.DEBUG)

# Add a test log message
logger.debug("QuoteCalculator logging is configured correctly.")
# Enable logger propagation
logger.propagate = True

# Add another test log message
logger.info("Logger propagation is enabled for QuoteCalculator.")

class QuoteCalculator:
    def _get_material_cost_per_base_unit(self, material: Material) -> Decimal:
        if material.quantity_in_supplier_unit == Decimal(0):
            # Avoid division by zero if quantity_in_supplier_unit is zero
            return Decimal(0)
        return material.cost_per_supplier_unit / material.quantity_in_supplier_unit

    def calculate_and_save_quote(
        self, quote_id: int, session: Session
    ) -> CalculatedQuote:
        logger.info(f"Starting quote calculation for Quote ID: {quote_id}")
        
        try: # Add try-except block for robust error logging
            quote = session.get(Quote, quote_id)
            if not quote:
                logger.error(f"Quote with id {quote_id} not found during calculation.")
                raise ValueError(f"Quote with id {quote_id} not found")
            if not quote.quote_config:
                logger.error(f"QuoteConfig not found for Quote with id {quote_id} during calculation.")
                raise ValueError(
                    f"QuoteConfig not found for Quote with id {quote_id}"
                )
            logger.debug(f"Successfully fetched Quote ID: {quote_id} and its QuoteConfig ID: {quote.quote_config_id}")

            total_material_cost_for_quote = Decimal(0)
            total_labor_cost_for_quote = Decimal(0)
            bill_of_materials_aggregated: Dict[
                Tuple[int, str], BillOfMaterialEntry
            ] = {}  # (material_id, base_unit_name) -> BillOfMaterialEntry

            for entry in quote.product_entries:
                logger.debug(f"Processing QuoteProductEntry ID: {entry.id}")
                product = entry.product
                if not product:
                    logger.error(f"Product not found for QuoteProductEntry ID: {entry.id}")
                    raise ValueError(
                        f"Product not found for QuoteProductEntry with id {entry.id}"
                    )

                product_quantity = entry.quantity_of_product_units
                product_base_labor_cost = (
                    product.base_labor_cost_per_product_unit * product_quantity
                )
                total_labor_cost_for_quote += product_base_labor_cost

                # --- Material cost calculation for the product entry ---
                # 1. Base materials for the product
                for pm in product.product_materials:
                    material = pm.material
                    logger.debug(f"Processing Material ID: {material.id}, Name: {material.name}")
                    if not material or not material.base_unit_type: # Ensure base_unit_type is loaded
                        logger.error(f"Material or its base unit type not found for ProductMaterial ID: {pm.id}")
                        raise ValueError(f"Material or its base unit type not found for ProductMaterial id {pm.id}")

                    cost_per_base_unit = self._get_material_cost_per_base_unit(material)
                    quantity_needed_for_product = (
                        pm.quantity_of_material_base_units_per_product_unit
                        * product_quantity
                    )
                    
                    cull_units = Decimal(0)
                    if material.cull_rate and material.cull_rate > 0:
                        cull_units = quantity_needed_for_product * Decimal(str(material.cull_rate))
                    
                    total_quantity_needed = quantity_needed_for_product + cull_units

                    bom_key = (material.id, material.base_unit_type.name)
                    if bom_key not in bill_of_materials_aggregated:
                        bill_of_materials_aggregated[bom_key] = BillOfMaterialEntry(
                            material_name=material.name,
                            quantity=Decimal(0),
                            unit_cost=cost_per_base_unit,
                            total_cost=Decimal(0),
                            unit_name=material.base_unit_type.name,
                            cull_units=Decimal(0) 
                        )
                    
                    bill_of_materials_aggregated[bom_key].quantity += total_quantity_needed
                    if bill_of_materials_aggregated[bom_key].cull_units is None: # Ensure cull_units is initialized
                        bill_of_materials_aggregated[bom_key].cull_units = Decimal(0)
                    bill_of_materials_aggregated[bom_key].cull_units += cull_units
                    # Total cost will be recalculated later after rounding quantities

                # 2. Materials from selected variations for the product entry
                for qpev in entry.selected_variations:
                    variation_option = qpev.variation_option
                    logger.debug(f"Processing VariationOption ID: {variation_option.id}, Name: {variation_option.name}")
                    if not variation_option:
                        logger.error(f"VariationOption not found for QuoteProductEntryVariation ID: {qpev.id}")
                        raise ValueError(
                            f"VariationOption not found for QuoteProductEntryVariation id {qpev.id}"
                        )

                    # Add variation's direct additional labor cost
                    total_labor_cost_for_quote += (
                        variation_option.additional_labor_cost_per_product_unit
                        * product_quantity
                    )
                    
                    # Add/modify materials based on variation
                    for vom in variation_option.variation_option_materials:
                        material = vom.material
                        if not material or not material.base_unit_type: # Ensure base_unit_type is loaded
                            logger.error(f"Material or its base unit type not found for VariationOptionMaterial id {vom.id}")
                            raise ValueError(f"Material or its base unit type not found for VariationOptionMaterial id {vom.id}")
                        
                        cost_per_base_unit = self._get_material_cost_per_base_unit(
                            material
                        )
                        quantity_added_or_removed_for_product = (
                            vom.quantity_of_material_base_units_added * product_quantity
                        )

                        cull_units_variation = Decimal(0)
                        if material.cull_rate and material.cull_rate > 0:
                             # Apply cull rate only to added quantities, not removed (negative)
                            if quantity_added_or_removed_for_product > 0:
                                cull_units_variation = quantity_added_or_removed_for_product * Decimal(str(material.cull_rate))

                        total_quantity_added_or_removed = quantity_added_or_removed_for_product + cull_units_variation

                        bom_key = (material.id, material.base_unit_type.name)
                        if bom_key not in bill_of_materials_aggregated:
                            bill_of_materials_aggregated[bom_key] = BillOfMaterialEntry(
                                material_name=material.name,
                                quantity=Decimal(0),
                                unit_cost=cost_per_base_unit,
                                total_cost=Decimal(0),
                                unit_name=material.base_unit_type.name,
                                cull_units=Decimal(0)
                            )
                        
                        bill_of_materials_aggregated[bom_key].quantity += total_quantity_added_or_removed
                        if bill_of_materials_aggregated[bom_key].cull_units is None: # Ensure cull_units is initialized
                            bill_of_materials_aggregated[bom_key].cull_units = Decimal(0)
                        bill_of_materials_aggregated[bom_key].cull_units += cull_units_variation
                        # Total cost will be recalculated later
            
            # Recalculate BOM entries with rounded quantities and update total material cost
            total_material_cost_for_quote = Decimal(0) # Re-initialize before summing up rounded costs
            for bom_entry in bill_of_materials_aggregated.values():
                # Calculate leftovers before rounding up quantity
                original_quantity = bom_entry.quantity
                
                if quote.quote_config.round_up_materials: # Check the flag
                    rounded_quantity = Decimal(math.ceil(original_quantity))
                    leftover_amount = rounded_quantity - original_quantity
                    bom_entry.leftovers = quantize_decimal(leftover_amount) if leftover_amount > 0 else Decimal(0)
                else:
                    rounded_quantity = original_quantity # No rounding
                    bom_entry.leftovers = Decimal(0) # No leftovers if not rounding up
                
                bom_entry.quantity = rounded_quantity

                # Round up cull units separately for reporting, if needed, or keep as calculated
                if bom_entry.cull_units is not None:
                    bom_entry.cull_units = quantize_decimal(bom_entry.cull_units) # Or math.ceil if whole units are culled

                bom_entry.total_cost = bom_entry.quantity * bom_entry.unit_cost
                bom_entry.total_cost = final_quantize_decimal(bom_entry.total_cost) 
                total_material_cost_for_quote += bom_entry.total_cost

            # Finalize BOM list
            final_bom_list = [
                bom_entry for bom_entry in bill_of_materials_aggregated.values()
            ]

            # --- COGS Calculation ---
            cost_of_goods_sold = total_material_cost_for_quote + total_labor_cost_for_quote

            # --- Apply QuoteConfig Rates ---
            quote_config = quote.quote_config
            applied_rates_info: List[AppliedRateInfoEntry] = []
            current_subtotal = cost_of_goods_sold

            # 1. Sales Commission (on COGS)
            if quote_config.sales_commission_rate > 0:
                commission_amount = cost_of_goods_sold * quote_config.sales_commission_rate
                applied_rates_info.append(
                    AppliedRateInfoEntry(
                        name="Sales Commission",
                        type="fee_on_cogs",
                        rate_value=quote_config.sales_commission_rate,
                        applied_amount=commission_amount,
                    )
                )
                current_subtotal += commission_amount

            # 2. Franchise Fee (on COGS)
            if quote_config.franchise_fee_rate > 0:
                franchise_fee_amount = cost_of_goods_sold * quote_config.franchise_fee_rate
                applied_rates_info.append(
                    AppliedRateInfoEntry(
                        name="Franchise Fee",
                        type="fee_on_cogs",
                        rate_value=quote_config.franchise_fee_rate,
                        applied_amount=franchise_fee_amount,
                    )
                )
                current_subtotal += franchise_fee_amount
            
            # 3. Margin (on the subtotal after COGS-based fees)
            # The plan implies margin is on COGS, but typically margin is applied on the cost *after* direct fees tied to COGS.
            # Let's assume margin is applied on (COGS + COGS-based fees).
            # If margin is strictly on COGS, then `cost_base_for_margin = cost_of_goods_sold`
            cost_base_for_margin = current_subtotal 
            if quote_config.margin_rate > 0:
                # Margin calculation: Price = Cost / (1 - MarginRate)
                # Markup Amount = Price - Cost = Cost * MarginRate / (1 - MarginRate)
                if quote_config.margin_rate >= 1:
                     raise ValueError("Margin rate cannot be 100% or more.")
                margin_amount = (cost_base_for_margin * quote_config.margin_rate) / (1 - quote_config.margin_rate)
                
                applied_rates_info.append(
                    AppliedRateInfoEntry(
                        name="Margin",
                        type="margin", # This is a margin, not a simple markup fee
                        rate_value=quote_config.margin_rate,
                        applied_amount=margin_amount,
                    )
                )
                current_subtotal += margin_amount


            # 4. Additional Fixed Fees (added after margin)
            if quote_config.additional_fixed_fees > 0:
                applied_rates_info.append(
                    AppliedRateInfoEntry(
                        name="Additional Fixed Fees",
                        type="fee_fixed",
                        rate_value=quote_config.additional_fixed_fees, # Store the fixed amount as 'rate'
                        applied_amount=quote_config.additional_fixed_fees,
                    )
                )
                current_subtotal += quote_config.additional_fixed_fees
            
            subtotal_before_tax = current_subtotal

            # --- Tax Calculation (on subtotal_before_tax) ---
            tax_amount = Decimal(0)
            if quote_config.tax_rate > 0:
                tax_amount = subtotal_before_tax * quote_config.tax_rate
            
            final_price = subtotal_before_tax + tax_amount

            # --- Create or Update CalculatedQuote ---
            # Round all final Decimal values to 2 decimal places
            rounding_precision = Decimal('0.01')
            logger.debug(f"Preparing CalculatedQuote data for Quote ID: {quote_id}")

            calculated_quote_data = CalculatedQuoteBase(
                quote_id=quote_id,
                bill_of_materials_json=[ # Convert list of Pydantic models to list of dicts
                    bom.model_dump(mode='json') # Use model_dump(mode='json') for Pydantic models
                    for bom in final_bom_list
                ],
                total_material_cost=total_material_cost_for_quote.quantize(rounding_precision, ROUND_HALF_UP),
                total_labor_cost=total_labor_cost_for_quote.quantize(rounding_precision, ROUND_HALF_UP),
                cost_of_goods_sold=cost_of_goods_sold.quantize(rounding_precision, ROUND_HALF_UP),
                applied_rates_info_json=[ # Convert list of Pydantic models to list of dicts
                    rate.model_dump(mode='json') # Use model_dump(mode='json') for Pydantic models
                    for rate in applied_rates_info
                ],
                subtotal_before_tax=subtotal_before_tax.quantize(rounding_precision, ROUND_HALF_UP),
                tax_amount=tax_amount.quantize(rounding_precision, ROUND_HALF_UP),
                final_price=final_price.quantize(rounding_precision, ROUND_HALF_UP),
            )
            logger.debug(f"CalculatedQuoteBase data prepared: {calculated_quote_data.model_dump_json(indent=2)}")

            # Check if a CalculatedQuote already exists for this quote_id
            logger.debug(f"Checking for existing CalculatedQuote for Quote ID: {quote_id}")
            existing_calculated_quote = session.exec(
                select(CalculatedQuote).where(CalculatedQuote.quote_id == quote_id)
            ).first()

            if existing_calculated_quote:
                logger.info(f"Found existing CalculatedQuote ID: {existing_calculated_quote.id} for Quote ID: {quote_id}. Updating.")
                # Update existing
                for key, value in calculated_quote_data.model_dump(exclude_unset=True).items():
                    setattr(existing_calculated_quote, key, value)
                db_calculated_quote = existing_calculated_quote
            else:
                logger.info(f"No existing CalculatedQuote found for Quote ID: {quote_id}. Creating new.")
                # Create new
                db_calculated_quote = CalculatedQuote.model_validate(calculated_quote_data)
            
            logger.debug(f"Adding CalculatedQuote object to session for Quote ID: {quote_id}")
            session.add(db_calculated_quote)
            
            # Update quote status
            logger.debug(f"Updating status of Quote ID: {quote_id} to 'calculated'.")
            quote.status = "calculated"
            session.add(quote)
            
            logger.info(f"Committing session for Quote ID: {quote_id}")
            session.commit()
            logger.info(f"Session committed successfully for Quote ID: {quote_id}")

            logger.debug(f"Refreshing db_calculated_quote instance for Quote ID: {quote_id}")
            session.refresh(db_calculated_quote)
            if quote: # mypy check
                 logger.debug(f"Refreshing quote instance for Quote ID: {quote_id}")
                 session.refresh(quote)

            logger.info(f"Quote calculation and save successful for Quote ID: {quote_id}. Returning CalculatedQuote ID: {db_calculated_quote.id}")
            return db_calculated_quote

        except Exception as e:
            logger.error(f"Error during quote calculation for Quote ID: {quote_id}: {str(e)}", exc_info=True)
            session.rollback() # Rollback in case of error
            logger.info(f"Session rolled back for Quote ID: {quote_id} due to error.")
            raise # Re-raise the exception after logging
