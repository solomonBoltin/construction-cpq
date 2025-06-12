import pytest
from app.models import Material, Product, ProductMaterial

def test_product_model_column_order():
    models = [Material, Product, ProductMaterial]
    for model in models:
        columns = [col.name for col in model.__table__.columns]
        print(f"{model.__name__} table columns: {columns}")
        
        if 'id' in columns:
            assert columns[0] == 'id', f"The first column in {model.__name__} table should be 'id'."
        if 'name' in columns and 'id' not in columns:
            assert columns[0] == 'name', f"The first column in {model.__name__} table should be 'name' if 'id' is not present."
        if 'name' in columns and 'id' in columns:
            assert columns[1] == 'name', f"The second column in {model.__name__} table should be 'name' if 'id' is present."





