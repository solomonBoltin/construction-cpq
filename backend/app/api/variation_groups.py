\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import VariationGroup, VariationGroupBase, Product # Product needed for validation/linking

router = APIRouter()

@router.post("/variation_groups/", response_model=VariationGroup, tags=["Variation Groups"])
def create_variation_group(
    *, 
    session: Session = Depends(get_session), 
    variation_group: VariationGroupBase
):
    # Example validation: Check if product exists
    db_product = session.get(Product, variation_group.product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail=f"Product with id {variation_group.product_id} not found")
    
    # Check for uniqueness if name should be unique per product
    # existing_vg = session.exec(
    #     select(VariationGroup).where(
    #         VariationGroup.product_id == variation_group.product_id,
    #         VariationGroup.name == variation_group.name
    #     )
    # ).first()
    # if existing_vg:
    #     raise HTTPException(status_code=400, detail="Variation group with this name already exists for this product.")

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
    # Assuming Product model has a relationship `variation_groups`
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

    # Ensure product_id is not changed, or if it is, validate the new product_id
    if variation_group_update.product_id != db_variation_group.product_id:
        new_product = session.get(Product, variation_group_update.product_id)
        if not new_product:
            raise HTTPException(status_code=404, detail=f"New product with id {variation_group_update.product_id} not found")
    
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
