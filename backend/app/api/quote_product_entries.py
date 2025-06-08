\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import QuoteProductEntry, QuoteProductEntryBase, Quote, Product # Needed for validation/linking

router = APIRouter()

@router.post("/quote_product_entries/", response_model=QuoteProductEntry, tags=["Quote Product Entries"])
def create_quote_product_entry(
    *,
    session: Session = Depends(get_session),
    quote_product_entry: QuoteProductEntryBase
):
    db_quote = session.get(Quote, quote_product_entry.quote_id)
    if not db_quote:
        raise HTTPException(status_code=404, detail=f"Quote with id {quote_product_entry.quote_id} not found")
    
    db_product = session.get(Product, quote_product_entry.product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail=f"Product with id {quote_product_entry.product_id} not found")

    db_entry = QuoteProductEntry.model_validate(quote_product_entry)
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry

@router.get("/quotes/{quote_id}/product_entries/", response_model=List[QuoteProductEntry], tags=["Quote Product Entries"])
def read_product_entries_for_quote(
    *,
    session: Session = Depends(get_session),
    quote_id: int = Path(...)
):
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    # Assuming Quote model has a relationship `product_entries`
    return quote.product_entries

@router.get("/quote_product_entries/{entry_id}", response_model=QuoteProductEntry, tags=["Quote Product Entries"])
def read_quote_product_entry(
    *,
    session: Session = Depends(get_session),
    entry_id: int = Path(...)
):
    entry = session.get(QuoteProductEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="QuoteProductEntry not found")
    return entry

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

    # Validate foreign keys if they are part of the update
    if entry_update.quote_id != db_entry.quote_id:
        new_quote = session.get(Quote, entry_update.quote_id)
        if not new_quote:
            raise HTTPException(status_code=404, detail=f"New Quote with id {entry_update.quote_id} not found")
    if entry_update.product_id != db_entry.product_id:
        new_product = session.get(Product, entry_update.product_id)
        if not new_product:
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
