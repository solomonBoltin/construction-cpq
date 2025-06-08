\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import (
    VariationOptionMaterial, VariationOptionMaterialBase, 
    VariationOption, Material
)

router = APIRouter()

@router.post("/variation_option_materials/", response_model=VariationOptionMaterial, tags=["Variation Option Materials"])
def create_variation_option_material(
    *, 
    session: Session = Depends(get_session), 
    vom: VariationOptionMaterialBase
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
    # Assuming VariationOption model has a relationship `materials` or `variation_option_materials`
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

    # Prevent changing variation_option_id and material_id
    if vom_update.variation_option_id != db_vom.variation_option_id or \
       vom_update.material_id != db_vom.material_id:
        # Check if new ones exist if we were to allow changing them
        # For now, disallow changing the core IDs of the link
        raise HTTPException(status_code=400, detail="Cannot change variation_option_id or material_id. Create a new link.")

    update_data = vom_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        # Skip IDs if they are part of the update_data but shouldn't be changed
        if key in ["variation_option_id", "material_id"] and value != getattr(db_vom, key):
            continue 
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
