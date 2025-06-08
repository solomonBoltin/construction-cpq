\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import Quote, QuoteBase, CalculatedQuote, QuoteConfig # QuoteConfig for validation
from app.services.quote_calculator import QuoteCalculator

router = APIRouter()

@router.post("/quotes/", response_model=Quote, tags=["Quotes"])
def create_quote(*, session: Session = Depends(get_session), quote: QuoteBase):
    # Validate quote_config_id
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

    if quote_update.quote_config_id != db_quote.quote_config_id:
        new_config = session.get(QuoteConfig, quote_update.quote_config_id)
        if not new_config:
            raise HTTPException(status_code=404, detail=f"New QuoteConfig with id {quote_update.quote_config_id} not found")

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

@router.post("/quotes/{quote_id}/calculate", response_model=CalculatedQuote, tags=["Quotes"])
def calculate_quote_total(
    *,
    session: Session = Depends(get_session),
    quote_id: int = Path(...)
):
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Ensure the quote has a configuration
    if not quote.quote_config: # Assumes quote.quote_config relationship is loaded or accessible
        # If quote_config_id is there but object not loaded, fetch it
        quote_config = session.get(QuoteConfig, quote.quote_config_id)
        if not quote_config:
             raise HTTPException(status_code=404, detail=f"QuoteConfig for quote id {quote_id} not found.")
        # If you need to assign it back for the calculator (though calculator might re-fetch)
        # quote.quote_config = quote_config 
    
    # Assuming QuoteCalculator takes the quote object and session
    calculator = QuoteCalculator(session=session) 
    calculated_quote = calculator.calculate_total_from_quote_object(quote) # Pass the quote model instance
    
    return calculated_quote
