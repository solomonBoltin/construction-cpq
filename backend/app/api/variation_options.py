\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import VariationOption, VariationOptionBase, VariationGroup # VariationGroup needed

router = APIRouter()

@router.post("/variation_options/", response_model=VariationOption, tags=["Variation Options"])
def create_variation_option(
    *, 
    session: Session = Depends(get_session), 
    variation_option: VariationOptionBase
):
    db_variation_group = session.get(VariationGroup, variation_option.variation_group_id)
    if not db_variation_group:
        raise HTTPException(status_code=404, detail=f"VariationGroup with id {variation_option.variation_group_id} not found")

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
    # Assuming VariationGroup model has a relationship `options` or `variation_options`
    return variation_group.variation_options


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
        new_group = session.get(VariationGroup, variation_option_update.variation_group_id)
        if not new_group:
            raise HTTPException(status_code=404, detail=f"New VariationGroup with id {variation_option_update.variation_group_id} not found")

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
