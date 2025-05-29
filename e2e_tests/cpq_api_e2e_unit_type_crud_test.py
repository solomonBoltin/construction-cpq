"""
CRUD tests for UnitTypes.
"""
import httpx
from .cpq_api_e2e import client, create_entity # Import client and helpers

def test_crud_unit_type(client: httpx.Client):
    """Tests basic CRUD operations for Unit Types (Create, Read, List). Update is not tested as it's not implemented."""
    print("\nTest: CRUD operations for UnitType...")
    
    unit_type_name = "Test E2E - Gram"
    unit_type_category = "Mass"
    
    # 1. Create
    print(f"  Creating UnitType '{unit_type_name}'...")
    created_ut = create_entity(
        client,
        "unit_types",
        {"name": unit_type_name, "category": unit_type_category, "description": "Test E2E unit for mass (Gram)"},
        "unit_type"
    )
    assert "id" in created_ut
    assert created_ut["name"] == unit_type_name
    assert created_ut["category"] == unit_type_category
    unit_type_id = created_ut["id"]
    print(f"  UnitType '{unit_type_name}' created with ID: {unit_type_id}.")

    # 2. Read (Get by ID)
    print(f"  Reading UnitType ID '{unit_type_id}'...")
    response = client.get(f"/unit_types/{unit_type_id}")
    assert response.status_code == 200
    read_ut = response.json()
    assert read_ut["name"] == unit_type_name
    assert read_ut["category"] == unit_type_category
    print(f"  Successfully read UnitType '{unit_type_name}'.")

    # 3. Update - SKIPPED as PUT /unit_types/{id} is not implemented
    print(f"  Skipping Update test for UnitType ID '{unit_type_id}' as endpoint is not available.")

    # 4. List (and check if ours is there)
    print("  Listing UnitTypes...")
    response = client.get("/unit_types/")
    assert response.status_code == 200
    unit_types_list = response.json()
    assert isinstance(unit_types_list, list)
    found_in_list = any(ut["id"] == unit_type_id and ut["name"] == unit_type_name for ut in unit_types_list)
    assert found_in_list, f"UnitType '{unit_type_name}' not found in list."
    print(f"  UnitType '{unit_type_name}' found in list.")

    print("CRUD test (excluding update) for UnitType completed.")
