from fastapi import APIRouter

# Import individual routers
from app.api import (
    unit_types, 
    materials, 
    products, 
    quote_configs, 
    product_materials, 
    variation_groups,
    variation_options,
    variation_option_materials,
    quotes,
    quote_product_entries,
    quote_product_entry_variations
)

router = APIRouter()

# Include routers from the api module
router.include_router(unit_types.router)
router.include_router(materials.router)
router.include_router(products.router)
router.include_router(quote_configs.router)
router.include_router(product_materials.router)
router.include_router(variation_groups.router)
router.include_router(variation_options.router)
router.include_router(variation_option_materials.router)
router.include_router(quotes.router)
router.include_router(quote_product_entries.router)
router.include_router(quote_product_entry_variations.router)

# Placeholder for other CRUD operations (PUT, DELETE) and more complex endpoints
# These will be added as development progresses.
