\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import Product, ProductBase, UnitType

router = APIRouter()

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
