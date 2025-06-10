from app.models import Material, Product, ProductMaterial
from decimal import Decimal
from sqlmodel import Session

def test_product_model_column_order():
    """
    Tests that the 'name' column is the second column in the Product table,
    following the 'id' primary key.
    """
    
    models = [Material, Product, ProductMaterial]
    for model in models:
        columns = [col.name for col in model.__table__.columns]
        print(f"Product table columns: {columns}")  # Log all columns
        # Expected order: id, name, description, ...
        

        # if has id assert its first 
        # if has name assert its first or second if id is present
        
        if 'id' in columns:
            assert columns[0] == 'id', f"The first column in {model.__name__} table should be 'id'."
        if 'name' in columns and 'id' not in columns:
            assert columns[0] == 'name', f"The first column in {model.__name__} table should be 'name' if 'id' is not present."
        if 'name' in columns and 'id' in columns:
            assert columns[1] == 'name', f"The second column in {model.__name__} table should be 'name' if 'id' is present."

        # It's assumed that a 'session' fixture is available in conftest.py or similar,
        # providing a database session where the DDL for triggers has been executed (e.g., on a PostgreSQL test DB).
        # Example fixture (if not already present):
        # @pytest.fixture(name="session")
        # def session_fixture(engine): # Assuming an 'engine' fixture is also available
        #     with Session(engine) as session:
        #         yield session





