\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import (
    QuoteProductEntryVariation, QuoteProductEntryVariationBase,
    QuoteProductEntry, VariationOption # Needed for validation/linking
)

router = APIRouter()

@router.post("/quote_product_entry_variations/", response_model=QuoteProductEntryVariation, tags=["Quote Product Entry Variations"])
def create_quote_product_entry_variation(
    *,
    session: Session = Depends(get_session),
    qpev: QuoteProductEntryVariationBase
):
    db_qpe = session.get(QuoteProductEntry, qpev.quote_product_entry_id)
    if not db_qpe:
        raise HTTPException(status_code=404, detail=f"QuoteProductEntry with id {qpev.quote_product_entry_id} not found")

    db_vo = session.get(VariationOption, qpev.variation_option_id)
    if not db_vo:
        raise HTTPException(status_code=404, detail=f"VariationOption with id {qpev.variation_option_id} not found")
    
    # Check for uniqueness: one entry should not have the same variation option twice.
    # Also, an entry should typically select one option per variation group of its product.
    # This logic can be more complex depending on business rules.
    existing_qpev = session.exec(
        select(QuoteProductEntryVariation).where(
            QuoteProductEntryVariation.quote_product_entry_id == qpev.quote_product_entry_id,
            QuoteProductEntryVariation.variation_option_id == qpev.variation_option_id
        )
    ).first()
    if existing_qpev:
        raise HTTPException(status_code=400, detail="This variation option is already selected for this quote entry.")


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
    entry = session.get(QuoteProductEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="QuoteProductEntry not found")
    # Assuming QuoteProductEntry model has a relationship `selected_variations` or similar
    return entry.selected_variations


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
# If a different variation option needs to be selected for a given group, 
# the existing one should be deleted and a new one created.
# An update might only make sense if there are attributes on the link table itself, e.g., a surcharge.

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
