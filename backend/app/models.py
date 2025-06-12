from datetime import datetime, timezone
from enum import Enum # Add timezone import
from pydantic import field_serializer, BaseModel as PydanticBaseModel, ConfigDict
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
import json 
from typing import List, Optional, Any, Type # Added Any
from decimal import Decimal
from sqlmodel import DDL, Computed, Field, SQLModel, Relationship
from sqlmodel.main import SQLModelMetaclass
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Boolean, Text, func, UniqueConstraint, event # Add func, UniqueConstraint, and event imports




# Custom SQLAlchemy TypeDecorator for lists of Pydantic models
class PydanticListJSONB(TypeDecorator):
    """Handles lists of Pydantic models for JSONB storage.

    Converts a list of Pydantic model instances to a list of dictionaries
    for storage, and vice-versa. SQLAlchemy's JSONB type handles the
    actual serialization/deserialization to/from a JSON string in the database.
    """
    impl = JSONB  # Use PostgreSQL JSONB type for native JSON support
    cache_ok = True # Indicates that this TypeDecorator is cacheable

    def __init__(self, pydantic_type: Type[PydanticBaseModel], *args: Any, **kwargs: Any):
        self.pydantic_type = pydantic_type
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value: Optional[List[PydanticBaseModel]], dialect: Any) -> Optional[List[dict]]:
        """Convert Pydantic models to a list of dicts for JSONB storage."""
        if value is None:
            return None
        if not all(isinstance(item, self.pydantic_type) for item in value):
            raise ValueError(f"All items must be instances of {self.pydantic_type.__name__}")
        # The `mode='json'` ensures that any custom serializers (like for Decimal) are applied.
        return [item.model_dump(mode='json') for item in value]

    def process_result_value(self, value: Optional[Any], dialect: Any) -> Optional[List[PydanticBaseModel]]:
        """Convert a list of dicts (from JSONB) back to Pydantic models."""
        if value is None:
            return None
        
        # SQLAlchemy's JSONB type should already parse the JSON string from the DB into a Python list of dicts.
        # If it's a string, it might be a default value or an issue with the JSONB type handling.
        # For robustness, especially if dealing with defaults that might be strings.
        data_to_parse: List[dict]
        if isinstance(value, str):
            try:
                loaded_value = json.loads(value)
                if not isinstance(loaded_value, list):
                    # Or raise a more specific error, log a warning, etc.
                    # This path suggests the DB string wasn't a JSON list.
                    return [] 
                data_to_parse = loaded_value
            except json.JSONDecodeError:
                # Handle cases where string is not valid JSON
                # Depending on requirements, could raise error, log, or return empty/default.
                # For now, returning empty list if parsing fails.
                return [] 
        elif isinstance(value, list):
            data_to_parse = value
        else:
            # Unexpected type from the database for this column.
            # Log warning or raise error. For now, returning empty list.
            return []

        try:
            return [self.pydantic_type(**item) for item in data_to_parse]
        except Exception as e: # Catch Pydantic validation errors or other issues
            # Log the error, and decide on behavior (raise, return partial, return empty)
            # For now, re-raising to make issues visible during development/testing
            # In production, might prefer to return None or an empty list with logging.
            # print(f"Error processing result value for PydanticListJSONB: {e}") # Consider proper logging
            raise # Or return [] / None based on error handling strategy


# Pydantic models for JSONB fields (not SQLModel table models)
class BillOfMaterialEntry(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True) # Removed json_encoders

    material_name: str
    quantity: Decimal # Changed from float
    unit_cost: Decimal # Changed from float
    total_cost: Decimal # Changed from float
    # Add unit_name for clarity in BOM
    unit_name: Optional[str] = None
    cull_units: Optional[Decimal] = None # Added cull_units
    leftovers: Optional[Decimal] = None # Added leftovers

    @field_serializer('quantity', 'unit_cost', 'total_cost', 'cull_units', 'leftovers', when_used='json')
    def serialize_decimals_to_str(self, v: Optional[Decimal]):
        if v is None:
            return None
        return str(v)


class AppliedRateInfoEntry(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True) # Removed json_encoders

    name: str
    type: str # e.g., 'margin', 'fee_on_cogs', 'fee_fixed', 'markup'
    rate_value: Decimal # Changed from float
    applied_amount: Decimal # Changed from float

    @field_serializer('rate_value', 'applied_amount', when_used='json')
    def serialize_decimals_to_str(self, v: Decimal):
        return str(v)


class QuoteType(str, Enum):
    """Defines the type of quote, allowing for different business logic flows."""
    GENERAL = "general"
    FENCE_PROJECT = "fence_project"
    DECK_PROJECT = "deck_project"

class ProductRole(str, Enum):
    """Defines the role of a product within a quote."""
    DEFAULT = "default"  # Default role for products
    MAIN = "main"
    SECONDARY = "secondary"
    ADDITIONAL = "additional"



# SQLModel Table Models

class UnitTypeBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    category: str = Field(max_length=50)

class UnitType(UnitTypeBase, table=True):
    __tablename__ = "unit_type" # Explicitly define table name to match plan

    materials_as_supplier_unit: List["Material"] = Relationship(
        back_populates="supplier_unit_type",
        sa_relationship_kwargs={'foreign_keys': '[Material.supplier_unit_type_id]'}
    )
    materials_as_base_unit: List["Material"] = Relationship(
        back_populates="base_unit_type",
        sa_relationship_kwargs={'foreign_keys': '[Material.base_unit_type_id]'}
    )
    products: List["Product"] = Relationship(back_populates="product_unit_type")


# New ProductCategory Model
class ProductCategoryBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Moved id to top
    name: str = Field(max_length=100, unique=True, index=True)
    type: str = Field(default="general", max_length=50) # e.g., 'general', 'material', 'labor'
    image_url: Optional[str] = Field(default=None, max_length=255)

class ProductCategory(ProductCategoryBase, table=True):
    __tablename__ = "product_category"

    product_links: List["ProductProductCategoryLink"] = Relationship(back_populates="category")

# New Link Table for Product and ProductCategory
class ProductProductCategoryLink(SQLModel, table=True):
    __tablename__ = "product_product_category_link"
    product_id: int = Field(default=None, foreign_key="product.id", primary_key=True)
    product_category_id: int = Field(default=None, foreign_key="product_category.id", primary_key=True)

    product: "Product" = Relationship(back_populates="category_links")
    category: "ProductCategory" = Relationship(back_populates="product_links")


class MaterialBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    name: str = Field(max_length=255, unique=True, index=True)
    description: Optional[str] = Field(default=None)
    cost_per_supplier_unit: Decimal = Field(max_digits=10, decimal_places=2)
    supplier_unit_type_id: Optional[int] = Field(default=None, foreign_key="unit_type.id")
    quantity_in_supplier_unit: Decimal = Field(default=Decimal("1.0"), max_digits=10, decimal_places=3)
    base_unit_type_id: int = Field(foreign_key="unit_type.id")
    cull_rate: Optional[float] = Field(default=0.0) # Added cull_rate property

class Material(MaterialBase, table=True):
    __tablename__ = "material"

    supplier_unit_type: Optional["UnitType"] = Relationship(
        back_populates="materials_as_supplier_unit",
        sa_relationship_kwargs={'foreign_keys': '[Material.supplier_unit_type_id]'}
    )
    base_unit_type: "UnitType" = Relationship(
        back_populates="materials_as_base_unit",
        sa_relationship_kwargs={'foreign_keys': '[Material.base_unit_type_id]'}
    )
    
    product_materials: List["ProductMaterial"] = Relationship(back_populates="material")
    variation_option_materials: List["VariationOptionMaterial"] = Relationship(back_populates="material")
    cull_rate: Optional[float] = Field(default=0.0) # Added cull_rate property


class ProductBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Moved id to top
    name: str = Field(max_length=255, unique=True, index=True)
    description: Optional[str] = Field(default=None)
    product_unit_type_id: int = Field(foreign_key="unit_type.id")
    unit_labor_cost: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    image_url: Optional[str] = Field(default=None, max_length=255) # New field for product image

class Product(ProductBase, table=True):
    __tablename__ = "product"
    
    product_unit_type: "UnitType" = Relationship(back_populates="products")
    category_links: List["ProductProductCategoryLink"] = Relationship(back_populates="product")
    product_materials: List["ProductMaterial"] = Relationship(back_populates="product", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    variation_groups: List["VariationGroup"] = Relationship(back_populates="product", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    quote_product_entries: List["QuoteProductEntry"] = Relationship(back_populates="product", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class ProductMaterialBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Added id as surrogate PK
    name:  Optional[str] = Field(
        sa_column=Column(
            String, 
            comment="Autogenerated by trigger: 'quantity of material_name'"
        )
    )
    product_id: int = Field(foreign_key="product.id")
    material_id: int = Field(foreign_key="material.id")
    material_amount: Decimal = Field(max_digits=50, decimal_places=25)


class ProductMaterial(ProductMaterialBase, table=True):
    __tablename__ = "product_material"
    # product_id and material_id are part of a unique constraint, not composite PK here
    __table_args__ = (UniqueConstraint("product_id", "material_id", name="uq_product_material_prod_mat"),)

    product: "Product" = Relationship(back_populates="product_materials")
    material: "Material" = Relationship(back_populates="product_materials")


# PostgreSQL script to autogenerate the name field in model
set_product_material_name_trigger = DDL('''
    CREATE OR REPLACE FUNCTION set_product_material_name()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.name := (
            SELECT CONCAT(
                NEW.material_amount::numeric(50, 2), -- Cast for consistent formatting
                ' of ', 
                m.name
            )
            FROM material AS m 
            WHERE m.id = NEW.material_id
        );
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- Drop the trigger if it already exists to prevent errors on re-creation
    DROP TRIGGER IF EXISTS trg_set_product_material_name ON product_material;

    -- Create the trigger that executes the function before an insert or update
    CREATE TRIGGER trg_set_product_material_name
    BEFORE INSERT OR UPDATE ON product_material
    FOR EACH ROW
    EXECUTE FUNCTION set_product_material_name();
''')

# Register the trigger when the model is created
event.listen(
    ProductMaterial.__table__,
    'after_create',
    set_product_material_name_trigger
)


class VariationGroupBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Moved id to top
    name: str = Field(max_length=100)
    product_id: int = Field(foreign_key="product.id")
    selection_type: str = Field(default="single_choice", max_length=20) # 'single_choice', 'multi_choice'
    is_required: bool = Field(default=False)

class VariationGroup(VariationGroupBase, table=True):
    __tablename__ = "variation_group"
    # id is inherited from VariationGroupBase and used as PK
    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_variation_group_product_name"),)

    product: "Product" = Relationship(back_populates="variation_groups")
    options: List["VariationOption"] = Relationship(back_populates="variation_group", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class VariationOptionBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Moved id to top
    name: str = Field(max_length=100)
    variation_group_id: int = Field(foreign_key="variation_group.id")
    value_description: Optional[str] = Field(default=None)
    additional_price: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    price_multiplier: Decimal = Field(default=Decimal("1.000"), max_digits=5, decimal_places=3)
    additional_labor_cost_per_product_unit: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)

class VariationOption(VariationOptionBase, table=True):
    __tablename__ = "variation_option"
    # id is inherited from VariationOptionBase and used as PK
    __table_args__ = (UniqueConstraint("variation_group_id", "name", name="uq_variation_option_group_name"),)

    variation_group: "VariationGroup" = Relationship(back_populates="options")
    variation_option_materials: List["VariationOptionMaterial"] = Relationship(back_populates="variation_option", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    quote_product_entry_variations: List["QuoteProductEntryVariation"] = Relationship(back_populates="variation_option")


class VariationOptionMaterialBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Added id as surrogate PK
    variation_option_id: int = Field(foreign_key="variation_option.id")
    material_id: int = Field(foreign_key="material.id")
    quantity_of_material_base_units_added: Decimal = Field(max_digits=10, decimal_places=3)

class VariationOptionMaterial(VariationOptionMaterialBase, table=True):
    __tablename__ = "variation_option_material"
    # id is inherited from VariationOptionMaterialBase and used as PK
    __table_args__ = (UniqueConstraint("variation_option_id", "material_id", name="uq_vom_option_material"),)

    variation_option: "VariationOption" = Relationship(back_populates="variation_option_materials")
    material: "Material" = Relationship(back_populates="variation_option_materials")


class QuoteConfigBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Moved id to top
    name: str = Field(default="Default Quote Config", max_length=100, unique=True, index=True)
    margin_rate: Decimal = Field(default=Decimal("0.30"), max_digits=5, decimal_places=4)
    tax_rate: Decimal = Field(default=Decimal("0.00"), max_digits=5, decimal_places=4)
    sales_commission_rate: Decimal = Field(default=Decimal("0.00"), max_digits=5, decimal_places=4)
    franchise_fee_rate: Decimal = Field(default=Decimal("0.00"), max_digits=5, decimal_places=4)
    additional_fixed_fees: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    round_up_materials: bool = Field(default=True) # New field

class QuoteConfig(QuoteConfigBase, table=True):
    __tablename__ = "quote_config"
    id: Optional[int] = Field(default=None, primary_key=True)
    quotes: List["Quote"] = Relationship(back_populates="quote_config")


class QuoteBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Moved id to top
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    quote_config_id: int = Field(foreign_key="quote_config.id")
    status: str = Field(default="draft", max_length=20, index=True) # Added index
    quote_type: QuoteType = Field(default=QuoteType.GENERAL, sa_column_kwargs={"server_default": QuoteType.GENERAL}) # Default to GENERAL type
    ui_state: Optional[str] = Field(default=None, max_length=100, index=True) # New field for UI state tracking
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), # Replaced datetime.utcnow
        sa_column_kwargs={"server_default": func.now()}
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), # Replaced datetime.utcnow
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )

class Quote(QuoteBase, table=True):
    __tablename__ = "quote"
    quote_config: "QuoteConfig" = Relationship(back_populates="quotes")
    product_entries: List["QuoteProductEntry"] = Relationship(back_populates="quote", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    calculated_quote: Optional["CalculatedQuote"] = Relationship(
        back_populates="quote",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False} # One-to-one
    )


class QuoteProductEntryBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Moved id to top
    quote_id: int = Field(foreign_key="quote.id")
    product_id: int = Field(foreign_key="product.id") # ON DELETE RESTRICT is default if not specified for FK
    quantity_of_product_units: Decimal = Field(max_digits=10, decimal_places=2)
    notes: Optional[str] = Field(default=None)
    role: ProductRole = Field(default=ProductRole.DEFAULT, sa_column_kwargs={"server_default": ProductRole.DEFAULT}) # Default to MAIN role

class QuoteProductEntry(QuoteProductEntryBase, table=True):
    __tablename__ = "quote_product_entry"
    id: Optional[int] = Field(default=None, primary_key=True)

    quote: "Quote" = Relationship(back_populates="product_entries")
    product: "Product" = Relationship(back_populates="quote_product_entries")
    selected_variations: List["QuoteProductEntryVariation"] = Relationship(
        back_populates="quote_product_entry",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class QuoteProductEntryVariationBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Added id as surrogate PK
    quote_product_entry_id: int = Field(foreign_key="quote_product_entry.id")
    variation_option_id: int = Field(foreign_key="variation_option.id") # ON DELETE RESTRICT

class QuoteProductEntryVariation(QuoteProductEntryVariationBase, table=True):
    __tablename__ = "quote_product_entry_variation"
    id: Optional[int] = Field(default=None, primary_key=True) # Surrogate PK
    __table_args__ = (UniqueConstraint("quote_product_entry_id", "variation_option_id", name="uq_qpev_entry_option"),)

    quote_product_entry: "QuoteProductEntry" = Relationship(back_populates="selected_variations")
    variation_option: "VariationOption" = Relationship(back_populates="quote_product_entry_variations")


class CalculatedQuoteBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Moved id to top
    quote_id: int = Field(foreign_key="quote.id", unique=True) # Ensures one-to-one with Quote
    bill_of_materials_json: Optional[List[BillOfMaterialEntry]] = Field(
        default=None, sa_column=Column(PydanticListJSONB(BillOfMaterialEntry)) # Use custom TypeDecorator
    )
    total_material_cost: Decimal = Field(max_digits=12, decimal_places=2)
    total_labor_cost: Decimal = Field(max_digits=12, decimal_places=2)
    cost_of_goods_sold: Decimal = Field(max_digits=12, decimal_places=2)
    applied_rates_info_json: Optional[List[AppliedRateInfoEntry]] = Field(
        default=None, sa_column=Column(PydanticListJSONB(AppliedRateInfoEntry)) # Use custom TypeDecorator
    )
    subtotal_before_tax: Decimal = Field(max_digits=12, decimal_places=2)
    tax_amount: Decimal = Field(max_digits=12, decimal_places=2)
    final_price: Decimal = Field(max_digits=12, decimal_places=2)
    calculated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), # Replaced datetime.utcnow
        sa_column_kwargs={"server_default": func.now()}
    )

class CalculatedQuote(CalculatedQuoteBase, table=True):
    __tablename__ = "calculated_quote"
    id: Optional[int] = Field(default=None, primary_key=True)
    quote: "Quote" = Relationship(back_populates="calculated_quote")

