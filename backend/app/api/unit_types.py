from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import UnitType, UnitTypeBase

router = APIRouter()

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
