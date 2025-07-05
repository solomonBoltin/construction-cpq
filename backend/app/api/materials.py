\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import Material, MaterialBase, UnitType

router = APIRouter()

@router.post("/materials/", response_model=Material, tags=["Materials"])
def create_material(*, session: Session = Depends(get_session), material: MaterialBase):
    # Use default unit_type_id (1) if not provided
    unit_type_id = material.unit_type_id if material.unit_type_id is not None else 1
    
    # Validate that the unit type exists
    if not session.get(UnitType, unit_type_id):
        raise HTTPException(status_code=404, detail=f"UnitType with id {unit_type_id} not found")

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
