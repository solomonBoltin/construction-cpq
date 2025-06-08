\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import ProductMaterial, ProductMaterialBase, Product, Material

router = APIRouter()

@router.post("/product_materials/", response_model=ProductMaterial, tags=["Product Materials"])
def create_product_material(
    *, 
    session: Session = Depends(get_session), 
    product_material: ProductMaterialBase
):
    db_product = session.get(Product, product_material.product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_material.product_id} not found")
    
    db_material = session.get(Material, product_material.material_id)
    if not db_material:
        raise HTTPException(status_code=404, detail=f"Material with id {product_material.material_id} not found")

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
    product_material_update: ProductMaterialBase
):
    db_product_material = session.get(ProductMaterial, product_material_id)
    if not db_product_material:
        raise HTTPException(status_code=404, detail="ProductMaterial not found")
    
    # Update logic based on ProductMaterialBase fields
    # Assuming product_id and material_id should not change or are handled carefully
    # For now, only updating other fields like quantity if present in ProductMaterialBase
    
    update_data = product_material_update.model_dump(exclude_unset=True)

    # Prevent changing product_id and material_id via this endpoint directly
    # Or add complex validation if it's allowed
    if "product_id" in update_data and update_data["product_id"] != db_product_material.product_id:
        raise HTTPException(status_code=400, detail="Cannot change product_id. Create a new link.")
    if "material_id" in update_data and update_data["material_id"] != db_product_material.material_id:
        raise HTTPException(status_code=400, detail="Cannot change material_id. Create a new link.")
        
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
    # Implementation from similar delete endpoints
    db_product_material = session.get(ProductMaterial, product_material_id)
    if not db_product_material:
        raise HTTPException(status_code=404, detail="ProductMaterial not found")
    session.delete(db_product_material)
    session.commit()
    return {"message": "ProductMaterial deleted successfully"}
