\
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.models import QuoteConfig, QuoteConfigBase

router = APIRouter()

@router.post("/quote_configs/", response_model=QuoteConfig, tags=["Quote Configuration"])
def create_quote_config(*, session: Session = Depends(get_session), quote_config: QuoteConfigBase):
    existing_config = session.exec(select(QuoteConfig).where(QuoteConfig.name == quote_config.name)).first()
    if existing_config:
        raise HTTPException(status_code=400, detail=f"QuoteConfig with name '{quote_config.name}' already exists.")

    db_quote_config = QuoteConfig.model_validate(quote_config)
    session.add(db_quote_config)
    session.commit()
    session.refresh(db_quote_config)
    return db_quote_config

@router.get("/quote_configs/", response_model=List[QuoteConfig], tags=["Quote Configuration"])
def read_quote_configs(
    *, 
    session: Session = Depends(get_session), 
    offset: int = 0, 
    limit: int = Query(default=100, le=100)
):
    quote_configs = session.exec(select(QuoteConfig).offset(offset).limit(limit)).all()
    return quote_configs

@router.get("/quote_configs/{quote_config_id}", response_model=QuoteConfig, tags=["Quote Configuration"])
def read_quote_config(*, session: Session = Depends(get_session), quote_config_id: int = Path(...) ):
    quote_config = session.get(QuoteConfig, quote_config_id)
    if not quote_config:
        raise HTTPException(status_code=404, detail="QuoteConfig not found")
    return quote_config

@router.delete("/quote_configs/{quote_config_id}", response_model=dict, tags=["Quote Configuration"])
def delete_quote_config(
    *, 
    session: Session = Depends(get_session), 
    quote_config_id: int = Path(...)
):
    quote_config = session.get(QuoteConfig, quote_config_id)
    if not quote_config:
        raise HTTPException(status_code=404, detail="QuoteConfig not found")
    session.delete(quote_config)
    session.commit()
    return {"message": "QuoteConfig deleted successfully"}
