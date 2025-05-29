from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel # Ensure SQLModel is imported for model_validate if needed directly

from app.database import get_session
from app.models import (
    UnitType, UnitTypeBase,
    Material, MaterialBase,
    Product, ProductBase,
    ProductMaterial, ProductMaterialBase,
    VariationGroup, VariationGroupBase,
    VariationOption, VariationOptionBase,
    VariationOptionMaterial, VariationOptionMaterialBase, # Added VariationOptionMaterial & VariationOptionMaterialBase
    QuoteConfig, QuoteConfigBase,
    Quote, QuoteBase,
    QuoteProductEntry, QuoteProductEntryBase,
    QuoteProductEntryVariation, QuoteProductEntryVariationBase,
    CalculatedQuote, # Added CalculatedQuote for response model
    # ... other models will be added as their APIs are built
)
from app.services.quote_calculator import QuoteCalculator # Added import

router = APIRouter()

# --- UnitType Endpoints ---
@router.post("/unit_types/", response_model=UnitType, tags=["Unit Types"])
def create_unit_type(*, session: Session = Depends(get_session), unit_type: UnitTypeBase):
    db_unit_type = UnitType.model_validate(unit_type)
    session.add(db_unit_type)
    session.commit()
    session.refresh(db_unit_type)
    return db_unit_type

@router.get("/unit_types/", response_model=List[UnitType], tags=["Unit Types"])
def read_unit_types(
    *, 
    session: Session = Depends(get_session), 
    offset: int = 0, 
    limit: int = Query(default=100, le=100)
):
    unit_types = session.exec(select(UnitType).offset(offset).limit(limit)).all()
    return unit_types

@router.get("/unit_types/{unit_type_id}", response_model=UnitType, tags=["Unit Types"])
def read_unit_type(*, session: Session = Depends(get_session), unit_type_id: int = Path(...) ):
    unit_type = session.get(UnitType, unit_type_id)
    if not unit_type:
        raise HTTPException(status_code=404, detail="UnitType not found")
    return unit_type

@router.delete("/unit_types/{unit_type_id}", response_model=dict, tags=["Unit Types"])
def delete_unit_type(
    *, 
    session: Session = Depends(get_session), 
    unit_type_id: int = Path(...)
):
    unit_type = session.get(UnitType, unit_type_id)
    if not unit_type:
        raise HTTPException(status_code=404, detail="UnitType not found")
    session.delete(unit_type)
    session.commit()
    return {"message": "UnitType deleted successfully"}

# --- Material Endpoints ---
@router.post("/materials/", response_model=Material, tags=["Materials"])
def create_material(*, session: Session = Depends(get_session), material: MaterialBase):
    # Basic validation: Ensure related UnitTypes exist
    if material.supplier_unit_type_id and not session.get(UnitType, material.supplier_unit_type_id):
        raise HTTPException(status_code=404, detail=f"Supplier UnitType with id {material.supplier_unit_type_id} not found")
    if not session.get(UnitType, material.base_unit_type_id):
        raise HTTPException(status_code=404, detail=f"Base UnitType with id {material.base_unit_type_id} not found")

    db_material = Material.model_validate(material)
    session.add(db_material)
    session.commit()
    session.refresh(db_material)
    return db_material

@router.get("/materials/", response_model=List[Material], tags=["Materials"])
def read_materials(
    *, 
    session: Session = Depends(get_session), 
    offset: int = 0, 
    limit: int = Query(default=100, le=100)
):
    materials = session.exec(select(Material).offset(offset).limit(limit)).all()
    return materials

@router.get("/materials/{material_id}", response_model=Material, tags=["Materials"])
def read_material(*, session: Session = Depends(get_session), material_id: int = Path(...) ):
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.delete("/materials/{material_id}", response_model=dict, tags=["Materials"])
def delete_material(
    *, 
    session: Session = Depends(get_session), 
    material_id: int = Path(...)
):
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    session.delete(material)
    session.commit()
    return {"message": "Material deleted successfully"}

# --- Product Endpoints ---
@router.post("/products/", response_model=Product, tags=["Products"])
def create_product(*, session: Session = Depends(get_session), product: ProductBase):
    if not session.get(UnitType, product.product_unit_type_id):
        raise HTTPException(status_code=404, detail=f"Product UnitType with id {product.product_unit_type_id} not found")
    
    db_product = Product.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@router.get("/products/", response_model=List[Product], tags=["Products"])
def read_products(
    *, 
    session: Session = Depends(get_session), 
    offset: int = 0, 
    limit: int = Query(default=100, le=100)
):
    products = session.exec(select(Product).offset(offset).limit(limit)).all()
    return products

@router.get("/products/{product_id}", response_model=Product, tags=["Products"])
def read_product(*, session: Session = Depends(get_session), product_id: int = Path(...) ):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.delete("/products/{product_id}", response_model=dict, tags=["Products"])
def delete_product(
    *, 
    session: Session = Depends(get_session), 
    product_id: int = Path(...)
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"message": "Product deleted successfully"}

# --- QuoteConfig Endpoints ---
@router.post("/quote_configs/", response_model=QuoteConfig, tags=["Quote Configuration"])
def create_quote_config(*, session: Session = Depends(get_session), quote_config: QuoteConfigBase):
    # Check if a config with this name already exists to prevent duplicates if name is unique
    existing_config = session.exec(select(QuoteConfig).where(QuoteConfig.name == quote_config.name)).first()
    if existing_config:
        raise HTTPException(status_code=400, detail=f"QuoteConfig with name '{quote_config.name}' already exists.")

    db_quote_config = QuoteConfig.model_validate(quote_config)
    session.add(db_quote_config)
    session.commit()
    session.refresh(db_quote_config)
    return db_quote_config

@router.get("/quote_configs/", response_model=List[QuoteConfig], tags=["Quote Configuration"])
def read_quote_configs(
    *, 
    session: Session = Depends(get_session), 
    offset: int = 0, 
    limit: int = Query(default=100, le=100)
):
    quote_configs = session.exec(select(QuoteConfig).offset(offset).limit(limit)).all()
    return quote_configs

@router.get("/quote_configs/{quote_config_id}", response_model=QuoteConfig, tags=["Quote Configuration"])
def read_quote_config(*, session: Session = Depends(get_session), quote_config_id: int = Path(...) ):
    quote_config = session.get(QuoteConfig, quote_config_id)
    if not quote_config:
        raise HTTPException(status_code=404, detail="QuoteConfig not found")
    return quote_config

@router.delete("/quote_configs/{quote_config_id}", response_model=dict, tags=["Quote Configuration"])
def delete_quote_config(
    *, 
    session: Session = Depends(get_session), 
    quote_config_id: int = Path(...)
):
    quote_config = session.get(QuoteConfig, quote_config_id)
    if not quote_config:
        raise HTTPException(status_code=404, detail="QuoteConfig not found")
    session.delete(quote_config)
    session.commit()
    return {"message": "QuoteConfig deleted successfully"}

# --- ProductMaterial Endpoints (linking Materials to Products) ---

@router.post("/product_materials/", response_model=ProductMaterial, tags=["Product Materials"])
def create_product_material(
    *, 
    session: Session = Depends(get_session), 
    product_material: ProductMaterialBase
):
    # Validate existence of Product and Material
    db_product = session.get(Product, product_material.product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_material.product_id} not found")
    
    db_material = session.get(Material, product_material.material_id)
    if not db_material:
        raise HTTPException(status_code=404, detail=f"Material with id {product_material.material_id} not found")

    # Check for existing unique constraint (product_id, material_id)
    existing_pm = session.exec(
        select(ProductMaterial)
        .where(ProductMaterial.product_id == product_material.product_id)
        .where(ProductMaterial.material_id == product_material.material_id)
    ).first()
    if existing_pm:
        raise HTTPException(status_code=400, detail="This material is already linked to this product.")

    db_product_material = ProductMaterial.model_validate(product_material)
    session.add(db_product_material)
    session.commit()
    session.refresh(db_product_material)
    return db_product_material

@router.get("/products/{product_id}/materials/", response_model=List[ProductMaterial], tags=["Product Materials"])
def read_materials_for_product(
    *, 
    session: Session = Depends(get_session), 
    product_id: int = Path(...)
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.product_materials

@router.get("/product_materials/{product_material_id}", response_model=ProductMaterial, tags=["Product Materials"])
def read_product_material(
    *, 
    session: Session = Depends(get_session), 
    product_material_id: int = Path(...)
):
    product_material = session.get(ProductMaterial, product_material_id)
    if not product_material:
        raise HTTPException(status_code=404, detail="ProductMaterial not found")
    return product_material

@router.put("/product_materials/{product_material_id}", response_model=ProductMaterial, tags=["Product Materials"])
def update_product_material(
    *, 
    session: Session = Depends(get_session), 
    product_material_id: int = Path(...),
    product_material_update: ProductMaterialBase # Assuming ProductMaterialBase can be used for updates
                                                # If only quantity can be updated, create a specific Pydantic model
):
    db_product_material = session.get(ProductMaterial, product_material_id)
    if not db_product_material:
        raise HTTPException(status_code=404, detail="ProductMaterial not found")

    # Ensure product_id and material_id are not being changed, or if they are, validate them
    # For simplicity, this example assumes they are not changed or are validated if changed.
    # If product_id or material_id can change, ensure the new combination doesn't violate unique constraints.
    if product_material_update.product_id != db_product_material.product_id or \
       product_material_update.material_id != db_product_material.material_id:
        # Check for existing unique constraint (product_id, material_id) if IDs are changing
        existing_pm = session.exec(
            select(ProductMaterial)
            .where(ProductMaterial.product_id == product_material_update.product_id)
            .where(ProductMaterial.material_id == product_material_update.material_id)
            .where(ProductMaterial.id != product_material_id) # Exclude self
        ).first()
        if existing_pm:
            raise HTTPException(status_code=400, detail="Another material link for this product already uses the target material ID.")
        
        # Validate new product and material if they are changed
        if product_material_update.product_id != db_product_material.product_id:
            if not session.get(Product, product_material_update.product_id):
                raise HTTPException(status_code=404, detail=f"New Product with id {product_material_update.product_id} not found")
        if product_material_update.material_id != db_product_material.material_id:
            if not session.get(Material, product_material_update.material_id):
                raise HTTPException(status_code=404, detail=f"New Material with id {product_material_update.material_id} not found")

    update_data = product_material_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product_material, key, value)
    
    session.add(db_product_material)
    session.commit()
    session.refresh(db_product_material)
    return db_product_material

@router.delete("/product_materials/{product_material_id}", response_model=dict, tags=["Product Materials"])
def delete_product_material(
    *, 
    session: Session = Depends(get_session), 
    product_material_id: int = Path(...)
):
    product_material = session.get(ProductMaterial, product_material_id)
    if not product_material:
        raise HTTPException(status_code=404, detail="ProductMaterial not found")
    
    session.delete(product_material)
    session.commit()
    return {"message": "ProductMaterial deleted successfully"}

# --- VariationGroup Endpoints (for Product Variations) ---

@router.post("/variation_groups/", response_model=VariationGroup, tags=["Variation Groups"])
def create_variation_group(
    *, 
    session: Session = Depends(get_session), 
    variation_group: VariationGroupBase
):
    db_product = session.get(Product, variation_group.product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail=f"Product with id {variation_group.product_id} not found")

    # Check for existing unique constraint (product_id, name)
    existing_vg = session.exec(
        select(VariationGroup)
        .where(VariationGroup.product_id == variation_group.product_id)
        .where(VariationGroup.name == variation_group.name)
    ).first()
    if existing_vg:
        raise HTTPException(status_code=400, detail=f"VariationGroup with name '{variation_group.name}' already exists for this product.")

    db_variation_group = VariationGroup.model_validate(variation_group)
    session.add(db_variation_group)
    session.commit()
    session.refresh(db_variation_group)
    return db_variation_group

@router.get("/products/{product_id}/variation_groups/", response_model=List[VariationGroup], tags=["Variation Groups"])
def read_variation_groups_for_product(
    *, 
    session: Session = Depends(get_session), 
    product_id: int = Path(...)
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.variation_groups

@router.get("/variation_groups/{variation_group_id}", response_model=VariationGroup, tags=["Variation Groups"])
def read_variation_group(
    *, 
    session: Session = Depends(get_session), 
    variation_group_id: int = Path(...)
):
    variation_group = session.get(VariationGroup, variation_group_id)
    if not variation_group:
        raise HTTPException(status_code=404, detail="VariationGroup not found")
    return variation_group

@router.put("/variation_groups/{variation_group_id}", response_model=VariationGroup, tags=["Variation Groups"])
def update_variation_group(
    *, 
    session: Session = Depends(get_session), 
    variation_group_id: int = Path(...),
    variation_group_update: VariationGroupBase
):
    db_variation_group = session.get(VariationGroup, variation_group_id)
    if not db_variation_group:
        raise HTTPException(status_code=404, detail="VariationGroup not found")

    # Check if product_id is being changed and validate new product if so
    if variation_group_update.product_id != db_variation_group.product_id:
        if not session.get(Product, variation_group_update.product_id):
            raise HTTPException(status_code=404, detail=f"New Product with id {variation_group_update.product_id} not found")
    
    # Check for unique constraint (product_id, name) if name or product_id is changing
    if (variation_group_update.name != db_variation_group.name or 
        variation_group_update.product_id != db_variation_group.product_id):
        existing_vg = session.exec(
            select(VariationGroup)
            .where(VariationGroup.product_id == variation_group_update.product_id)
            .where(VariationGroup.name == variation_group_update.name)
            .where(VariationGroup.id != variation_group_id) # Exclude self
        ).first()
        if existing_vg:
            raise HTTPException(status_code=400, detail=f"Another VariationGroup with name '{variation_group_update.name}' already exists for the target product.")

    update_data = variation_group_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_variation_group, key, value)
    
    session.add(db_variation_group)
    session.commit()
    session.refresh(db_variation_group)
    return db_variation_group

@router.delete("/variation_groups/{variation_group_id}", response_model=dict, tags=["Variation Groups"])
def delete_variation_group(
    *, 
    session: Session = Depends(get_session), 
    variation_group_id: int = Path(...)
):
    variation_group = session.get(VariationGroup, variation_group_id)
    if not variation_group:
        raise HTTPException(status_code=404, detail="VariationGroup not found")
    
    session.delete(variation_group)
    session.commit()
    return {"message": "VariationGroup deleted successfully"}

# --- VariationOption Endpoints (Options within a VariationGroup) ---

@router.post("/variation_options/", response_model=VariationOption, tags=["Variation Options"])
def create_variation_option(
    *, 
    session: Session = Depends(get_session), 
    variation_option: VariationOptionBase
):
    db_variation_group = session.get(VariationGroup, variation_option.variation_group_id)
    if not db_variation_group:
        raise HTTPException(status_code=404, detail=f"VariationGroup with id {variation_option.variation_group_id} not found")

    # Check for existing unique constraint (variation_group_id, name)
    existing_vo = session.exec(
        select(VariationOption)
        .where(VariationOption.variation_group_id == variation_option.variation_group_id)
        .where(VariationOption.name == variation_option.name)
    ).first()
    if existing_vo:
        raise HTTPException(status_code=400, detail=f"VariationOption with name '{variation_option.name}' already exists for this group.")

    db_variation_option = VariationOption.model_validate(variation_option)
    session.add(db_variation_option)
    session.commit()
    session.refresh(db_variation_option)
    return db_variation_option

@router.get("/variation_groups/{variation_group_id}/options/", response_model=List[VariationOption], tags=["Variation Options"])
def read_options_for_variation_group(
    *, 
    session: Session = Depends(get_session), 
    variation_group_id: int = Path(...)
):
    variation_group = session.get(VariationGroup, variation_group_id)
    if not variation_group:
        raise HTTPException(status_code=404, detail="VariationGroup not found")
    return variation_group.options

@router.get("/variation_options/{variation_option_id}", response_model=VariationOption, tags=["Variation Options"])
def read_variation_option(
    *, 
    session: Session = Depends(get_session), 
    variation_option_id: int = Path(...)
):
    variation_option = session.get(VariationOption, variation_option_id)
    if not variation_option:
        raise HTTPException(status_code=404, detail="VariationOption not found")
    return variation_option

@router.put("/variation_options/{variation_option_id}", response_model=VariationOption, tags=["Variation Options"])
def update_variation_option(
    *, 
    session: Session = Depends(get_session), 
    variation_option_id: int = Path(...),
    variation_option_update: VariationOptionBase
):
    db_variation_option = session.get(VariationOption, variation_option_id)
    if not db_variation_option:
        raise HTTPException(status_code=404, detail="VariationOption not found")

    if variation_option_update.variation_group_id != db_variation_option.variation_group_id:
        if not session.get(VariationGroup, variation_option_update.variation_group_id):
            raise HTTPException(status_code=404, detail=f"New VariationGroup with id {variation_option_update.variation_group_id} not found")

    if (variation_option_update.name != db_variation_option.name or
        variation_option_update.variation_group_id != db_variation_option.variation_group_id):
        existing_vo = session.exec(
            select(VariationOption)
            .where(VariationOption.variation_group_id == variation_option_update.variation_group_id)
            .where(VariationOption.name == variation_option_update.name)
            .where(VariationOption.id != variation_option_id)
        ).first()
        if existing_vo:
            raise HTTPException(status_code=400, detail=f"Another VariationOption with name '{variation_option_update.name}' already exists for the target group.")

    update_data = variation_option_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_variation_option, key, value)
    
    session.add(db_variation_option)
    session.commit()
    session.refresh(db_variation_option)
    return db_variation_option

@router.delete("/variation_options/{variation_option_id}", response_model=dict, tags=["Variation Options"])
def delete_variation_option(
    *, 
    session: Session = Depends(get_session), 
    variation_option_id: int = Path(...)
):
    variation_option = session.get(VariationOption, variation_option_id)
    if not variation_option:
        raise HTTPException(status_code=404, detail="VariationOption not found")
    
    session.delete(variation_option)
    session.commit()
    return {"message": "VariationOption deleted successfully"}

# --- VariationOptionMaterial Endpoints (linking Materials to VariationOptions) ---

@router.post("/variation_option_materials/", response_model=VariationOptionMaterial, tags=["Variation Option Materials"])
def create_variation_option_material(
    *, 
    session: Session = Depends(get_session), 
    vom: VariationOptionMaterialBase # vom short for VariationOptionMaterial
):
    db_variation_option = session.get(VariationOption, vom.variation_option_id)
    if not db_variation_option:
        raise HTTPException(status_code=404, detail=f"VariationOption with id {vom.variation_option_id} not found")
    
    db_material = session.get(Material, vom.material_id)
    if not db_material:
        raise HTTPException(status_code=404, detail=f"Material with id {vom.material_id} not found")

    # Check for existing unique constraint (variation_option_id, material_id)
    existing_vom = session.exec(
        select(VariationOptionMaterial)
        .where(VariationOptionMaterial.variation_option_id == vom.variation_option_id)
        .where(VariationOptionMaterial.material_id == vom.material_id)
    ).first()
    if existing_vom:
        raise HTTPException(status_code=400, detail="This material is already linked to this variation option.")

    db_vom = VariationOptionMaterial.model_validate(vom)
    session.add(db_vom)
    session.commit()
    session.refresh(db_vom)
    return db_vom

@router.get("/variation_options/{variation_option_id}/materials/", response_model=List[VariationOptionMaterial], tags=["Variation Option Materials"])
def read_materials_for_variation_option(
    *, 
    session: Session = Depends(get_session), 
    variation_option_id: int = Path(...)
):
    variation_option = session.get(VariationOption, variation_option_id)
    if not variation_option:
        raise HTTPException(status_code=404, detail="VariationOption not found")
    return variation_option.variation_option_materials

@router.get("/variation_option_materials/{vom_id}", response_model=VariationOptionMaterial, tags=["Variation Option Materials"])
def read_variation_option_material(
    *, 
    session: Session = Depends(get_session), 
    vom_id: int = Path(...)
):
    vom = session.get(VariationOptionMaterial, vom_id)
    if not vom:
        raise HTTPException(status_code=404, detail="VariationOptionMaterial not found")
    return vom

@router.put("/variation_option_materials/{vom_id}", response_model=VariationOptionMaterial, tags=["Variation Option Materials"])
def update_variation_option_material(
    *, 
    session: Session = Depends(get_session), 
    vom_id: int = Path(...),
    vom_update: VariationOptionMaterialBase 
):
    db_vom = session.get(VariationOptionMaterial, vom_id)
    if not db_vom:
        raise HTTPException(status_code=404, detail="VariationOptionMaterial not found")

    if vom_update.variation_option_id != db_vom.variation_option_id or \
       vom_update.material_id != db_vom.material_id:
        existing_vom = session.exec(
            select(VariationOptionMaterial)
            .where(VariationOptionMaterial.variation_option_id == vom_update.variation_option_id)
            .where(VariationOptionMaterial.material_id == vom_update.material_id)
            .where(VariationOptionMaterial.id != vom_id) # Exclude self
        ).first()
        if existing_vom:
            raise HTTPException(status_code=400, detail="Another material link for this variation option already uses the target material ID.")
        
        if vom_update.variation_option_id != db_vom.variation_option_id:
            if not session.get(VariationOption, vom_update.variation_option_id):
                raise HTTPException(status_code=404, detail=f"New VariationOption with id {vom_update.variation_option_id} not found")
        if vom_update.material_id != db_vom.material_id:
            if not session.get(Material, vom_update.material_id):
                raise HTTPException(status_code=404, detail=f"New Material with id {vom_update.material_id} not found")

    update_data = vom_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_vom, key, value)
    
    session.add(db_vom)
    session.commit()
    session.refresh(db_vom)
    return db_vom

@router.delete("/variation_option_materials/{vom_id}", response_model=dict, tags=["Variation Option Materials"])
def delete_variation_option_material(
    *, 
    session: Session = Depends(get_session), 
    vom_id: int = Path(...)
):
    vom = session.get(VariationOptionMaterial, vom_id)
    if not vom:
        raise HTTPException(status_code=404, detail="VariationOptionMaterial not found")
    
    session.delete(vom)
    session.commit()
    return {"message": "VariationOptionMaterial deleted successfully"}

# --- Quote Endpoints ---

@router.post("/quotes/", response_model=Quote, tags=["Quotes"])
def create_quote(*, session: Session = Depends(get_session), quote: QuoteBase):
    # Validate existence of QuoteConfig
    db_quote_config = session.get(QuoteConfig, quote.quote_config_id)
    if not db_quote_config:
        raise HTTPException(status_code=404, detail=f"QuoteConfig with id {quote.quote_config_id} not found")

    db_quote = Quote.model_validate(quote)
    session.add(db_quote)
    session.commit()
    session.refresh(db_quote)
    return db_quote

@router.get("/quotes/", response_model=List[Quote], tags=["Quotes"])
def read_quotes(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    quotes = session.exec(select(Quote).offset(offset).limit(limit)).all()
    return quotes

@router.get("/quotes/{quote_id}", response_model=Quote, tags=["Quotes"])
def read_quote(*, session: Session = Depends(get_session), quote_id: int = Path(...)):
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@router.put("/quotes/{quote_id}", response_model=Quote, tags=["Quotes"])
def update_quote(
    *,
    session: Session = Depends(get_session),
    quote_id: int = Path(...),
    quote_update: QuoteBase 
):
    db_quote = session.get(Quote, quote_id)
    if not db_quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Validate QuoteConfig if it's being changed
    if quote_update.quote_config_id != db_quote.quote_config_id:
        db_quote_config = session.get(QuoteConfig, quote_update.quote_config_id)
        if not db_quote_config:
            raise HTTPException(status_code=404, detail=f"QuoteConfig with id {quote_update.quote_config_id} not found")

    update_data = quote_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_quote, key, value)
    
    session.add(db_quote)
    session.commit()
    session.refresh(db_quote)
    return db_quote

@router.delete("/quotes/{quote_id}", response_model=dict, tags=["Quotes"])
def delete_quote(
    *,
    session: Session = Depends(get_session),
    quote_id: int = Path(...)
):
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    session.delete(quote)
    session.commit()
    return {"message": "Quote deleted successfully"}

# --- QuoteProductEntry Endpoints ---

@router.post("/quote_product_entries/", response_model=QuoteProductEntry, tags=["Quote Product Entries"])
def create_quote_product_entry(
    *,
    session: Session = Depends(get_session),
    quote_product_entry: QuoteProductEntryBase
):
    # Validate existence of Quote and Product
    db_quote = session.get(Quote, quote_product_entry.quote_id)
    if not db_quote:
        raise HTTPException(status_code=404, detail=f"Quote with id {quote_product_entry.quote_id} not found")
    
    db_product = session.get(Product, quote_product_entry.product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail=f"Product with id {quote_product_entry.product_id} not found")

    db_quote_product_entry = QuoteProductEntry.model_validate(quote_product_entry)
    session.add(db_quote_product_entry)
    session.commit()
    session.refresh(db_quote_product_entry)
    return db_quote_product_entry

@router.get("/quotes/{quote_id}/product_entries/", response_model=List[QuoteProductEntry], tags=["Quote Product Entries"])
def read_product_entries_for_quote(
    *,
    session: Session = Depends(get_session),
    quote_id: int = Path(...)
):
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote.product_entries

@router.get("/quote_product_entries/{entry_id}", response_model=QuoteProductEntry, tags=["Quote Product Entries"])
def read_quote_product_entry(
    *,
    session: Session = Depends(get_session),
    entry_id: int = Path(...)
):
    quote_product_entry = session.get(QuoteProductEntry, entry_id)
    if not quote_product_entry:
        raise HTTPException(status_code=404, detail="QuoteProductEntry not found")
    return quote_product_entry

@router.put("/quote_product_entries/{entry_id}", response_model=QuoteProductEntry, tags=["Quote Product Entries"])
def update_quote_product_entry(
    *,
    session: Session = Depends(get_session),
    entry_id: int = Path(...),
    entry_update: QuoteProductEntryBase
):
    db_entry = session.get(QuoteProductEntry, entry_id)
    if not db_entry:
        raise HTTPException(status_code=404, detail="QuoteProductEntry not found")

    # Validate Quote if it's being changed
    if entry_update.quote_id != db_entry.quote_id:
        db_quote = session.get(Quote, entry_update.quote_id)
        if not db_quote:
            raise HTTPException(status_code=404, detail=f"New Quote with id {entry_update.quote_id} not found")
    
    # Validate Product if it's being changed
    if entry_update.product_id != db_entry.product_id:
        db_product = session.get(Product, entry_update.product_id)
        if not db_product:
            raise HTTPException(status_code=404, detail=f"New Product with id {entry_update.product_id} not found")

    update_data = entry_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_entry, key, value)
    
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry

@router.delete("/quote_product_entries/{entry_id}", response_model=dict, tags=["Quote Product Entries"])
def delete_quote_product_entry(
    *,
    session: Session = Depends(get_session),
    entry_id: int = Path(...)
):
    entry = session.get(QuoteProductEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="QuoteProductEntry not found")
    
    session.delete(entry)
    session.commit()
    return {"message": "QuoteProductEntry deleted successfully"}

# --- QuoteProductEntryVariation Endpoints ---

@router.post("/quote_product_entry_variations/", response_model=QuoteProductEntryVariation, tags=["Quote Product Entry Variations"])
def create_quote_product_entry_variation(
    *,
    session: Session = Depends(get_session),
    qpev: QuoteProductEntryVariationBase # qpev for QuoteProductEntryVariation
):
    # Validate existence of QuoteProductEntry and VariationOption
    db_qpe = session.get(QuoteProductEntry, qpev.quote_product_entry_id)
    if not db_qpe:
        raise HTTPException(status_code=404, detail=f"QuoteProductEntry with id {qpev.quote_product_entry_id} not found")
    
    db_vo = session.get(VariationOption, qpev.variation_option_id)
    if not db_vo:
        raise HTTPException(status_code=404, detail=f"VariationOption with id {qpev.variation_option_id} not found")

    # Additional validation: Ensure the VariationOption belongs to the Product of the QuoteProductEntry
    if db_vo.variation_group.product_id != db_qpe.product_id:
        raise HTTPException(status_code=400, detail="VariationOption does not belong to the product in the quote entry.")

    # Check for existing unique constraint (quote_product_entry_id, variation_option_id)
    existing_qpev = session.exec(
        select(QuoteProductEntryVariation)
        .where(QuoteProductEntryVariation.quote_product_entry_id == qpev.quote_product_entry_id)
        .where(QuoteProductEntryVariation.variation_option_id == qpev.variation_option_id)
    ).first()
    if existing_qpev:
        raise HTTPException(status_code=400, detail="This variation option is already selected for this quote product entry.")

    # Check selection_type of the VariationGroup (single_choice constraint)
    variation_group = db_vo.variation_group
    if variation_group.selection_type == "single_choice":
        # Check if any other option from the same group is already selected for this quote_product_entry
        existing_options_in_group = session.exec(
            select(QuoteProductEntryVariation)
            .join(VariationOption)
            .where(QuoteProductEntryVariation.quote_product_entry_id == qpev.quote_product_entry_id)
            .where(VariationOption.variation_group_id == variation_group.id)
        ).all()
        if existing_options_in_group:
            raise HTTPException(status_code=400, detail=f"Cannot select multiple options for single-choice group '{variation_group.name}'.")

    db_qpev = QuoteProductEntryVariation.model_validate(qpev)
    session.add(db_qpev)
    session.commit()
    session.refresh(db_qpev)
    return db_qpev

@router.get("/quote_product_entries/{entry_id}/variations/", response_model=List[QuoteProductEntryVariation], tags=["Quote Product Entry Variations"])
def read_variations_for_quote_product_entry(
    *,
    session: Session = Depends(get_session),
    entry_id: int = Path(...)
):
    qpe = session.get(QuoteProductEntry, entry_id)
    if not qpe:
        raise HTTPException(status_code=404, detail="QuoteProductEntry not found")
    return qpe.selected_variations

@router.get("/quote_product_entry_variations/{qpev_id}", response_model=QuoteProductEntryVariation, tags=["Quote Product Entry Variations"])
def read_quote_product_entry_variation(
    *,
    session: Session = Depends(get_session),
    qpev_id: int = Path(...)
):
    qpev = session.get(QuoteProductEntryVariation, qpev_id)
    if not qpev:
        raise HTTPException(status_code=404, detail="QuoteProductEntryVariation not found")
    return qpev

# PUT for QuoteProductEntryVariation is generally not needed as it's a link table.
# If a different variation option needs to be selected, the existing one should be deleted and a new one created.

@router.delete("/quote_product_entry_variations/{qpev_id}", response_model=dict, tags=["Quote Product Entry Variations"])
def delete_quote_product_entry_variation(
    *,
    session: Session = Depends(get_session),
    qpev_id: int = Path(...)
):
    qpev = session.get(QuoteProductEntryVariation, qpev_id)
    if not qpev:
        raise HTTPException(status_code=404, detail="QuoteProductEntryVariation not found")
    
    session.delete(qpev)
    session.commit()
    return {"message": "QuoteProductEntryVariation deleted successfully"}


# --- Quote Calculation Endpoint ---

@router.post("/quotes/{quote_id}/calculate", response_model=CalculatedQuote, tags=["Quotes"])
def calculate_quote_endpoint(
    *,
    session: Session = Depends(get_session),
    quote_id: int = Path(...)
):
    """
    Calculates the costs and final price for a given quote based on its
    product entries, selected variations, and the associated quote configuration.
    Saves the calculation results in the CalculatedQuote table.
    """
    calculator = QuoteCalculator()
    try:
        calculated_quote = calculator.calculate_and_save_quote(quote_id=quote_id, session=session)
        return calculated_quote
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) # Or 400 for bad input if more appropriate
    except Exception as e:
        # Log the exception e for debugging
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during quote calculation: {str(e)}")


# Placeholder for other CRUD operations (PUT, DELETE) and more complex endpoints
# These will be added as development progresses.
