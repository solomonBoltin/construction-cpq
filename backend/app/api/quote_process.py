from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.models import Quote, QuoteType, ProductRole, CalculatedQuote
from app.services.quote_process import (
    QuoteProcessService,
    QuotePreview,
    CategoryPreview,
    ProductPreview,
    MaterializedProductEntry,
)

router = APIRouter(prefix="/quote-process", tags=["Quote Process"])

def get_quote_process_service(session: Session = Depends(get_session)) -> QuoteProcessService:
    return QuoteProcessService(session=session)

@router.get("/quotes", response_model=List[QuotePreview])
def list_quotes(
    quote_type: Optional[QuoteType] = Query(None, description="Filter by quote type"),
    offset: int = 0,
    limit: int = Query(default=100, le=500),
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """List all quotes, with optional filtering and pagination."""
    return service.get_quotes(quote_type=quote_type, offset=offset, limit=limit)

@router.get("/quotes/{quote_id}", response_model=Quote)
def get_quote(
    quote_id: int,
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Get a single quote by its ID."""
    try:
        return service.get_quote_by_id(quote_id=quote_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/quotes", response_model=Quote) # Changed to return full Quote model
def create_quote(
    name: str,
    quote_type: QuoteType,
    description: Optional[str] = None,
    config_id: int = 1, # Assuming a default config_id
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Create a new quote."""
    try:
        return service.create_quote(name=name, description=description, quote_type=quote_type, config_id=config_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/quotes/{quote_id}/ui-state", response_model=Quote)
def update_quote_ui_state(
    quote_id: int,
    ui_state: str,
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Update the UI state of a quote."""
    try:
        return service.update_quote_ui_state(quote_id=quote_id, ui_state=ui_state)
    except HTTPException as e:
        raise e # Re-raise HTTPException directly
    except ValueError as e: # Catch other potential errors like quote not found from service
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/quotes/{quote_id}/status", response_model=Quote)
def set_quote_status(
    quote_id: int,
    status: str,
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Set the status of a quote."""
    try:
        return service.set_quote_status(quote_id=quote_id, status=status)
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/categories", response_model=List[CategoryPreview])
def list_categories(
    category_type: Optional[str] = Query(None, description="Filter by category type"),
    offset: int = 0,
    limit: int = Query(default=100, le=500),
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """List product categories."""
    return service.get_categories_previews(category_type=category_type, offset=offset, limit=limit)

@router.get("/categories/{category_name}/products", response_model=List[ProductPreview])
def list_products_in_category(
    category_name: str,
    offset: int = 0,
    limit: int = Query(default=100, le=500),
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """List products within a specific category."""
    return service.get_products_previews(category_name=category_name, offset=offset, limit=limit)

@router.post("/quotes/{quote_id}/product-entries", response_model=MaterializedProductEntry)
def add_product_to_quote(
    quote_id: int,
    product_id: int,
    quantity: Decimal,
    role: ProductRole,
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Add a product entry to a quote."""
    try:
        return service.add_quote_product_entry(quote_id=quote_id, product_id=product_id, quantity=quantity, role=role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/quotes/{quote_id}/product-entries", response_model=List[MaterializedProductEntry])
def list_quote_product_entries(
    quote_id: int,
    role: Optional[ProductRole] = Query(None, description="Filter by product role"),
    offset: int = 0,
    limit: int = Query(default=100, le=500),
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """List product entries for a quote."""
    return service.get_quote_product_entries(quote_id=quote_id, role=role, offset=offset, limit=limit)

@router.delete("/quotes/{quote_id}/product-entries/{product_entry_id}", status_code=204)
def remove_product_from_quote(
    quote_id: int,
    product_entry_id: int,
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Remove a product entry from a quote."""
    try:
        service.delete_quote_product_entry(quote_id=quote_id, product_entry_id=product_entry_id)
        return None # No content response for 204
    except HTTPException as e:
        raise e # Re-raise HTTPException directly from service (e.g., 404 if not found)
    except ValueError as e: # Catch other potential errors
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/product-entries/{product_entry_id}", response_model=MaterializedProductEntry)
def get_materialized_product_entry(
    product_entry_id: int,
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Get a single materialized product entry."""
    try:
        return service.get_quote_product_entry(product_entry_id=product_entry_id)
    except HTTPException as e: # Catch 404 from service
        raise e


@router.put("/product-entries/{product_entry_id}/variations/{variation_option_id}", response_model=MaterializedProductEntry)
def set_product_variation_option(
    product_entry_id: int,
    variation_option_id: int,
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Set or toggle a variation option for a product entry."""
    try:
        return service.set_quote_product_variation_option(product_entry_id=product_entry_id, variation_option_id=variation_option_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/quotes/{quote_id}/calculate", response_model=CalculatedQuote)
def calculate_quote_totals(
    quote_id: int,
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Calculate the totals for a quote."""
    try:
        return service.calculate_quote(quote_id=quote_id)
    except ValueError as e: # Or any specific exception your calculator might raise for invalid state
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e: # Catch-all for unexpected errors during calculation
        # Log the exception e
        raise HTTPException(status_code=500, detail="An error occurred during quote calculation.")


@router.get("/quotes/{quote_id}/calculate", response_model=Optional[CalculatedQuote])
def get_calculated_quote_details(
    quote_id: int,
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """Get the calculated details of a quote if available."""
    calculated_quote = service.get_calculated_quote(quote_id=quote_id)
    if not calculated_quote:
        # You might return 404 if no calculation exists, or an empty object/specific response
        # For now, returning None which FastAPI handles with the Optional response model
        return None
    return calculated_quote

@router.get("/products/by-category-type/{category_type}", response_model=List[ProductPreview])
def list_products_by_category_type(
    category_type: str,
    offset: int = 0,
    limit: int = Query(default=100, le=500),
    service: QuoteProcessService = Depends(get_quote_process_service),
):
    """List products within all categories of a given type."""
    return service.get_products_previews_by_category_type(category_type=category_type, offset=offset, limit=limit)
