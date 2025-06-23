import logging
from datetime import datetime, timezone
from decimal import Decimal, Decimal as D
from enum import Enum
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, func

# Assuming your models are in a structure like 'app.models'
# and the calculator is in 'app.services.quote_calculator'
from app.models import (
    ProductRole,
    Quote,
    QuoteProductEntry,
    Product,
    ProductCategory,
    QuoteStatus,
    QuoteType,
    VariationGroup,
    VariationOption,
    QuoteProductEntryVariation,
    CalculatedQuote,
    QuoteConfig,
    ProductProductCategoryLink, # Added ProductProductCategoryLink
)
from app.services.quote_calculator import QuoteCalculator

# Configure logger for this service, mirroring QuoteCalculator's style
logger = logging.getLogger("app.services.quote_process_service")
logger.setLevel(logging.DEBUG)
logger.propagate = True


class QuotePreview(BaseModel):
    """A lightweight summary of a quote for list views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: Optional[str]
    description: Optional[str]
    status: str
    quote_type: QuoteType
    updated_at: datetime
    
    @field_validator('status', mode="before")
    def validate_my_field(cls, v):
        if v is None:
            return QuoteStatus.DRAFT
        return v

class CategoryPreview(BaseModel):
    """A lightweight summary of a product category."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    image_url: Optional[str] = None

class ProductPreview(BaseModel):
    """A lightweight summary of a product for catalog views."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    # Assuming Product model has an image_url field
    image_url: Optional[str] = None

class VariationOptionView(BaseModel):
    """Represents a single, selectable option for a variation."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    value_description: Optional[str]
    additional_price: Decimal
    is_selected: bool = False

class VariationGroupView(BaseModel):
    """Represents a group of variation options (e.g., 'Color', 'Style')."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    selection_type: str
    is_required: bool
    options: List[VariationOptionView]

class MaterializedProductEntry(BaseModel):
    """
    A fully detailed DTO for a product entry in a quote.
    It "materializes" data from multiple tables into one object for the UI.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    quote_id: int
    product_id: int
    product_name: str
    role: Optional[ProductRole]
    quantity_of_product_units: Decimal
    notes: Optional[str]
    variation_groups: List[VariationGroupView]


# ===================================================================================
# Quote Process Service
# ===================================================================================

class QuoteProcessService:
    """
    Orchestrates the creation and modification of quotes and their components.
    This service is designed to be called by an API layer.
    """
    def __init__(self, session: Session):
        """
        Initializes the service with a database session.

        Args:
            session: The SQLAlchemy/SQLModel session for database operations.
        """
        self.session = session
        self.calculator = QuoteCalculator()

    def _materialize_product_entry(self, entry: QuoteProductEntry) -> MaterializedProductEntry:
        """
        Private helper to convert a QuoteProductEntry model into a rich DTO.
        
        This fetches all related data (product info, variations, selected options)
        and assembles it into a MaterializedProductEntry.
        """
        product = self.session.get(Product, entry.product_id)
        if not product:
            raise ValueError(f"Product with ID {entry.product_id} not found for entry {entry.id}")

        # Eagerly load variation options to avoid N+1 queries
        statement = select(VariationGroup).where(VariationGroup.product_id == product.id).options(selectinload(VariationGroup.options))
        variation_groups = self.session.exec(statement).all()

        materialized_groups = []
        for group in variation_groups:
            materialized_options = []
            for option in group.options:
                is_selected = any(
                    sel_var.variation_option_id == option.id
                    for sel_var in entry.selected_variations
                )
                materialized_options.append(
                    VariationOptionView(
                        id=option.id,
                        name=option.name,
                        value_description=option.value_description,
                        additional_price=option.additional_price,
                        is_selected=is_selected,
                    )
                )
            materialized_groups.append(
                VariationGroupView(
                    id=group.id,
                    name=group.name,
                    selection_type=group.selection_type,
                    is_required=group.is_required,
                    options=materialized_options,
                )
            )

        return MaterializedProductEntry(
            id=entry.id,
            quote_id=entry.quote_id,
            product_id=entry.product_id,
            product_name=product.name,
            role=entry.role,
            quantity_of_product_units=entry.quantity_of_product_units,
            notes=entry.notes,
            variation_groups=materialized_groups,
        )

    # === Quote Management ===
    
    def get_quotes(self, quote_type: Optional[QuoteType] = None, offset: int = 0, limit: int = 100) -> List[QuotePreview]:
        """Fetches a list of quotes, optionally filtered by type, with pagination."""
        logger.info(f"Fetching quotes with type: {quote_type}, offset: {offset}, limit: {limit}")
        statement = select(Quote).offset(offset).limit(limit)
        if quote_type:
            statement = statement.where(Quote.quote_type == quote_type)
        # Consider adding an order_by, e.g., .order_by(Quote.updated_at.desc())
        statement = statement.order_by(Quote.updated_at.desc()) # Added default sorting
        quotes = self.session.exec(statement).all()
        
        logger.debug(f"Raw quotes from database: {quotes}")
        validated_quotes = [QuotePreview.model_validate(q) for q in quotes]
        logger.debug(f"Validated quotes: {validated_quotes}")
        return validated_quotes

    def get_quote_by_id(self, quote_id: int) -> Quote:
        """Fetches a single quote by its ID."""
        logger.info(f"Fetching quote with ID: {quote_id}")
        quote = self.session.get(Quote, quote_id)
        if not quote:
            raise ValueError(f"Quote with ID {quote_id} not found")
        return quote

    def create_quote(self, name: str, description: Optional[str], quote_type: QuoteType, config_id: int = 1) -> Quote:
        """Creates a new quote with a specific type."""
        logger.info(f"Creating new quote '{name}' of type '{quote_type.value}'")
        quote_config = self.session.get(QuoteConfig, config_id)
        if not quote_config:
            raise ValueError(f"QuoteConfig with id {config_id} not found.")

        try:
            new_quote = Quote(
                name=name,
                description=description,
                quote_type=quote_type,
                status=QuoteStatus.DRAFT,
                quote_config_id=config_id,
                quote_config=quote_config,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.session.add(new_quote)
            self.session.commit()
            self.session.refresh(new_quote)
            logger.info(f"Successfully created Quote ID: {new_quote.id}")
            return new_quote
        except Exception as e:
            logger.error(f"Error creating quote: {e}", exc_info=True)
            self.session.rollback()
            raise

    def update_quote_ui_state(self, quote_id: int, ui_state: str) -> Quote:
        """Updates the UI state of a specific quote."""
        logger.info(f"Updating UI state for Quote ID: {quote_id} to '{ui_state}'")
        quote = self.session.get(Quote, quote_id)
        if not quote:
            logger.warning(f"Quote ID {quote_id} not found for UI state update.")
            raise HTTPException(status_code=404, detail=f"Quote with id {quote_id} not found")
        
        try:
            quote.ui_state = ui_state
            quote.updated_at = datetime.now(timezone.utc) # Also update timestamp
            self.session.add(quote)
            self.session.commit()
            self.session.refresh(quote)
            logger.info(f"Successfully updated UI state for Quote ID: {quote_id} to '{ui_state}'")
            return quote
        except Exception as e:
            logger.error(f"Error updating UI state for quote {quote_id}: {e}", exc_info=True)
            self.session.rollback()
            raise

    def set_quote_status(self, quote_id: int, status: str) -> Quote:
        """Sets the overall status of a quote (e.g., draft, calculated, finalized)."""
        logger.info(f"Setting status for Quote ID: {quote_id} to '{status}'")
        quote = self.session.get(Quote, quote_id)
        if not quote:
            logger.warning(f"Quote ID {quote_id} not found for status update.")
            raise HTTPException(status_code=404, detail=f"Quote with id {quote_id} not found")

        # Optional: Add validation for allowed status values or transitions if needed
        # Example: allowed_statuses = ["draft", "calculated", "finalized", "archived"]
        # if status not in allowed_statuses:
        #     raise ValueError(f"Invalid status: {status}. Allowed statuses are: {', '.join(allowed_statuses)}")

        try:
            quote.status = status
            quote.updated_at = datetime.now(timezone.utc) # Also update timestamp
            self.session.add(quote)
            self.session.commit()
            self.session.refresh(quote)
            logger.info(f"Successfully set status for Quote ID: {quote_id} to '{status}'")
            return quote
        except Exception as e:
            logger.error(f"Error setting status for quote {quote_id}: {e}", exc_info=True)
            self.session.rollback()
            raise

    # === Product & Category Discovery ===

    def get_categories_previews(self, category_type: Optional[str] = None, offset: int = 0, limit: int = 100) -> List[CategoryPreview]: # Added pagination params
        """Gets product categories, optionally filtered by type, with pagination."""
        logger.info(f"Fetching category previews with type: {category_type}, offset: {offset}, limit: {limit}")
        statement = select(ProductCategory).offset(offset).limit(limit)
        if category_type:
            statement = statement.where(ProductCategory.type == category_type)
        statement = statement.order_by(ProductCategory.name) # Added default sorting by name
        categories = self.session.exec(statement).all()
        return [CategoryPreview.model_validate(c) for c in categories]

    def get_products_previews(self, category_name: str, offset: int = 0, limit: int = 100) -> List[ProductPreview]: # Added pagination params
        """Gets product previews for a given category, with pagination."""
        logger.info(f"Fetching product previews for category: {category_name}, offset: {offset}, limit: {limit}")
        # First, find the category to get its ID
        category = self.session.exec(select(ProductCategory).where(ProductCategory.name == category_name)).first()
        if not category:
            logger.warning(f"Category '{category_name}' not found.")
            return [] # Or raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")

        # Then, find products linked to this category via ProductProductCategoryLink
        statement = (
            select(Product)
            .join(ProductProductCategoryLink, Product.id == ProductProductCategoryLink.product_id)
            .where(ProductProductCategoryLink.product_category_id == category.id)
            .offset(offset)
            .limit(limit)
            .order_by(Product.name) # Added default sorting by name
        )
        products = self.session.exec(statement).all()
        return [ProductPreview.model_validate(p) for p in products]

    # === Quote Product Entry Management ===

    def add_quote_product_entry(self, quote_id: int, product_id: int, quantity: Decimal, role: ProductRole) -> MaterializedProductEntry:
        """Adds a product to a quote with a specific role."""
        logger.info(f"Attempting to add product {product_id} with role {role.value} to quote {quote_id}")
        
        quote = self.session.get(Quote, quote_id)
        if not quote:
            raise ValueError(f"Quote with id {quote_id} not found.")

        # Business Rule: Enforce only one MAIN product.
        if role == ProductRole.MAIN:
            statement = select(QuoteProductEntry).where(QuoteProductEntry.quote_id == quote_id, QuoteProductEntry.role == ProductRole.MAIN)
            existing_main = self.session.exec(statement).first()
            if existing_main:
                logger.warning(f"Quote {quote_id} already has a MAIN product (Entry ID: {existing_main.id}). Cannot add another.")
                raise ValueError("A main product already exists for this quote. Please remove it before adding a new one.")

        try:
            new_entry = QuoteProductEntry(
                quote_id=quote_id,
                product_id=product_id,
                quantity_of_product_units=quantity,
                role=role
            )
            self.session.add(new_entry)
            self.session.commit()
            self.session.refresh(new_entry)
            logger.info(f"Successfully created QuoteProductEntry ID: {new_entry.id}")
            return self._materialize_product_entry(new_entry)
        except Exception as e:
            logger.error(f"Error adding product entry to quote {quote_id}: {e}", exc_info=True)
            self.session.rollback()
            raise

    def get_quote_product_entries(self, quote_id: int, role: Optional[ProductRole] = None, offset: int = 0, limit: int = 100) -> List[MaterializedProductEntry]:
        """Gets materialized product entries for a quote, optionally filtered by role, with pagination."""
        logger.info(f"Fetching product entries for Quote ID: {quote_id}, Role: {role}, Offset: {offset}, Limit: {limit}")
        statement = (
            select(QuoteProductEntry)
            .where(QuoteProductEntry.quote_id == quote_id)
            .options(selectinload(QuoteProductEntry.selected_variations), 
                     selectinload(QuoteProductEntry.product).selectinload(Product.variation_groups).selectinload(VariationGroup.options) # For materialization
            )
            .offset(offset)
            .limit(limit)
            .order_by(QuoteProductEntry.id) # Added default sorting
        )
        if role:
            statement = statement.where(QuoteProductEntry.role == role)
        
        entries = self.session.exec(statement).all()
        if not entries:
            logger.info(f"No product entries found for Quote ID: {quote_id} with specified criteria.")
            return []
        
        materialized_entries = [self._materialize_product_entry(entry) for entry in entries]
        return materialized_entries
    
    def delete_quote_product_entry(self, quote_id: int, product_entry_id: int) -> None:
        """Removes a product entry from a quote, ensuring it belongs to the quote."""
        logger.info(f"Attempting to delete QuoteProductEntry ID: {product_entry_id} from Quote ID: {quote_id}")
        entry = self.session.get(QuoteProductEntry, product_entry_id)
        
        if not entry:
            logger.warning(f"QuoteProductEntry ID {product_entry_id} not found for deletion.")
            # Raise an HTTPException to inform the client, consistent with other error handling.
            raise HTTPException(status_code=404, detail=f"QuoteProductEntry with id {product_entry_id} not found")

        if entry.quote_id != quote_id:
            logger.warning(f"QuoteProductEntry ID {product_entry_id} (belongs to quote {entry.quote_id}) does not belong to quote {quote_id}. Deletion aborted.")
            raise HTTPException(status_code=400, detail=f"QuoteProductEntry with id {product_entry_id} does not belong to quote {quote_id}")

        try:
            self.session.delete(entry)
            self.session.commit()
            logger.info(f"Successfully deleted QuoteProductEntry ID: {product_entry_id}")
        except Exception as e:
            logger.error(f"Error deleting entry {product_entry_id}: {e}", exc_info=True)
            self.session.rollback()
            raise

    def get_quote_product_entry(self, product_entry_id: int) -> MaterializedProductEntry:
        """Gets a single materialized product entry by its ID."""
        logger.info(f"Fetching materialized product entry for ID: {product_entry_id}")
        
        # Eagerly load selected variations to prevent N+1 queries in the materialization step
        # Also load the product itself for materialization
        statement = select(QuoteProductEntry).where(QuoteProductEntry.id == product_entry_id).options(
            selectinload(QuoteProductEntry.selected_variations),
            selectinload(QuoteProductEntry.product).selectinload(Product.variation_groups).selectinload(VariationGroup.options) # For materialization
        )
        entry = self.session.exec(statement).first()
        
        if not entry:
            logger.warning(f"QuoteProductEntry ID {product_entry_id} not found.")
            raise HTTPException(status_code=404, detail=f"QuoteProductEntry with id {product_entry_id} not found")
        
        return self._materialize_product_entry(entry)

    # === Variation Management ===

    def set_quote_product_variation_option(self, product_entry_id: int, variation_option_id: int) -> MaterializedProductEntry:
        """Sets the selected option for a variation group."""
        logger.info(f"Setting variation option {variation_option_id} for entry {product_entry_id}")
        
        entry = self.session.get(QuoteProductEntry, product_entry_id)
        if not entry:
            raise ValueError(f"QuoteProductEntry with id {product_entry_id} not found.")

        option_to_set = self.session.get(VariationOption, variation_option_id)
        if not option_to_set:
            raise ValueError(f"VariationOption with id {variation_option_id} not found.")

        group = self.session.get(VariationGroup, option_to_set.variation_group_id)
        if not group:
            raise ValueError("Could not find parent variation group for the selected option.")
        
        try:
            # If single choice, remove any other selections in the same group
            if group.selection_type == "single_choice":
                statement = select(QuoteProductEntryVariation).where(
                    QuoteProductEntryVariation.quote_product_entry_id == product_entry_id
                ).join(VariationOption).where(
                    VariationOption.variation_group_id == group.id
                )
                existing_selections_in_group = self.session.exec(statement).all()
                for sel in existing_selections_in_group:
                    self.session.delete(sel)
                
                # After clearing, add the new single choice
                new_selection = QuoteProductEntryVariation(
                    quote_product_entry_id=product_entry_id,
                    variation_option_id=variation_option_id
                )
                self.session.add(new_selection)

            elif group.selection_type == "multi_choice":
                # Check if this specific option is already selected
                statement = select(QuoteProductEntryVariation).where(
                    QuoteProductEntryVariation.quote_product_entry_id == product_entry_id,
                    QuoteProductEntryVariation.variation_option_id == variation_option_id
                )
                existing_specific_selection = self.session.exec(statement).first()

                if existing_specific_selection:
                    # Option is already selected, so deselect it (delete)
                    self.session.delete(existing_specific_selection)
                    logger.info(f"Deselected multi-choice option {variation_option_id} for entry {product_entry_id}")
                else:
                    # Option is not selected, so add it
                    new_selection = QuoteProductEntryVariation(
                        quote_product_entry_id=product_entry_id,
                        variation_option_id=variation_option_id
                    )
                    self.session.add(new_selection)
                    logger.info(f"Selected multi-choice option {variation_option_id} for entry {product_entry_id}")
            
            else: # Should not happen with current data model
                logger.error(f"Unknown selection type: {group.selection_type} for group {group.id}")
                raise ValueError(f"Unsupported variation group selection type: {group.selection_type}")

            self.session.commit()
            self.session.refresh(entry) # Refresh entry to load the new/changed selection state
            logger.info(f"Successfully updated variation for entry {product_entry_id}")
            return self._materialize_product_entry(entry)

        except Exception as e:
            logger.error(f"Error setting variation for entry {product_entry_id}: {e}", exc_info=True)
            self.session.rollback()
            raise

    # === Calculation & Finalization ===

    def calculate_quote(self, quote_id: int) -> CalculatedQuote:
        """Triggers the full quote calculation by delegating to QuoteCalculator."""
        logger.info(f"Delegating calculation for Quote ID: {quote_id} to QuoteCalculator.")
        return self.calculator.calculate_and_save_quote(quote_id, self.session)

    def get_calculated_quote(self, quote_id: int) -> Optional[CalculatedQuote]:
        """Retrieves the results of a previous calculation for a quote."""
        logger.info(f"Fetching calculated results for Quote ID: {quote_id}")
        statement = select(CalculatedQuote).where(CalculatedQuote.quote_id == quote_id)
        return self.session.exec(statement).first()

