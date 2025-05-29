"""
Base functions, helper methods, pytest fixtures, and common configurations for CPQ API E2E tests.
"""
import pytest
import httpx
import os
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Generator, Optional

# --- Configuration ---
DELETE_WHEN_FINISHED = True  # Set to False to keep created test data
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000/api/v1")

# Global list to keep track of created entities for cleanup
# Each item will be a dict: {"type": "entity_name", "id": entity_id, "name": "entity_unique_name_for_lookup"}
created_entities: List[Dict[str, Any]] = []

# --- Helper Functions ---
def quantize_d(value, exp="0.01"):
    """Helper to quantize decimals for comparison."""
    if isinstance(value, str):
        value = Decimal(value)
    return value.quantize(Decimal(exp), rounding=ROUND_HALF_UP)

# --- Pytest Fixtures ---
@pytest.fixture(scope="session") # Changed scope to session for all tests
def client() -> Generator[httpx.Client, None, None]:
    """
    Provides an httpx.Client for making API requests to the backend.
    The client is configured with the BASE_URL and a timeout.
    It waits for the backend to be healthy before yielding.
    """
    wait_for_backend()
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c

def wait_for_backend(max_retries=10, delay_seconds=5):
    """
    Waits for the backend health check to pass before proceeding.
    """
    health_check_url = BASE_URL.replace("/api/v1", "") + "/health"
    print(f"Waiting for backend at {health_check_url} ...")
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=10.0) as temp_health_client:
                response = temp_health_client.get(health_check_url)
                if response.status_code == 200 and response.json().get("status") == "ok":
                    print("Backend is healthy.")
                    return
        except httpx.RequestError as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Backend not ready yet ({e}). Retrying in {delay_seconds}s...")
        time.sleep(delay_seconds)
    pytest.fail(f"Backend did not become healthy after {max_retries * delay_seconds} seconds.")


@pytest.fixture(scope="session", autouse=True) # Changed scope to session
def cleanup_created_entities(client: httpx.Client):
    """
    Pytest fixture to clean up (delete) entities created during the test run.
    This runs once after all tests in the session are finished.
    Deletion order is important for entities with dependencies.
    """
    yield  # Tests run here

    if DELETE_WHEN_FINISHED:
        print("\\nCleaning up created entities...")
        deletion_order = [
            "quote_product_entry",
            "variation_option_material",
            "product_material",
            "variation_option",
            "variation_group",
            "quote",
            "product",
            "material",
            "quote_config",
            "unit_type",
        ]

        sorted_entities_for_deletion = sorted(
            created_entities,
            key=lambda x: deletion_order.index(x["type"]) if x["type"] in deletion_order else -1,
        )
        
        for entity in sorted_entities_for_deletion:
            entity_type = entity["type"]
            entity_id = entity["id"]
            entity_name = entity.get("name", f"ID: {entity_id}")
            
            path_segment_map = {
                "unit_type": "unit_types",
                "material": "materials",
                "product": "products",
                "product_material": "product_materials",
                "variation_group": "variation_groups",
                "variation_option": "variation_options",
                "variation_option_material": "variation_option_materials",
                "quote_config": "quote_configs",
                "quote": "quotes",
                "quote_product_entry": "quote_product_entries",
            }
            
            api_path_segment = path_segment_map.get(entity_type)

            if not api_path_segment:
                print(f"  Skipping cleanup for unknown entity type: {entity_type} ('{entity_name}')")
                continue

            if entity_id:
                print(f"  Deleting {entity_type} '{entity_name}' (ID: {entity_id})...")
                try:
                    delete_response = client.delete(f"/{api_path_segment}/{entity_id}")
                    if delete_response.status_code == 200:
                        print(f"    Successfully deleted {entity_type} '{entity_name}'.")
                    elif delete_response.status_code == 404:
                        print(f"    {entity_type} '{entity_name}' (ID: {entity_id}) already deleted or not found.")
                    else:
                        print(f"    WARNING: Failed to delete {entity_type} '{entity_name}' (ID: {entity_id}). Status: {delete_response.status_code}, Response: {delete_response.text}")
                except Exception as e:
                    print(f"    ERROR: Exception during deletion of {entity_type} '{entity_name}' (ID: {entity_id}): {e}")
        print("Cleanup finished.")
    else:
        print("\nSkipping cleanup as DELETE_WHEN_FINISHED is False.")

# --- API Interaction Helpers ---

def find_entity_by_name(client: httpx.Client, entity_api_path: str, name: str) -> Optional[Dict[str, Any]]:
    """
    Finds an entity by its name via a GET request to the listing endpoint.
    Assumes the listing endpoint returns a list of entities, each with a 'name' field.
    """
    print(f"Searching for {entity_api_path} with name '{name}'...")
    try:
        response = client.get(f"/{entity_api_path}/")
        response.raise_for_status() 
        entities = response.json()
        for entity in entities:
            if entity.get("name") == name:
                print(f"Found existing {entity_api_path} '{name}' with ID: {entity['id']}")
                return entity
        print(f"{entity_api_path} '{name}' not found.")
        return None
    except httpx.HTTPStatusError as e:
        print(f"Error finding entity {name} at /{entity_api_path}/: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"Exception finding entity {name} at /{entity_api_path}/: {e}")
        return None

def create_entity(client: httpx.Client, entity_api_path: str, payload: Dict[str, Any], entity_type_name: str, unique_name_field: str = "name") -> Dict[str, Any]:
    """
    Creates an entity via a POST request. If an entity with the same unique_name_field (default 'name')
    already exists, it uses the existing one. Adds successfully created or found entities
    (if their name suggests they are test data, e.g., starts with "Test E2E") to the global `created_entities` list.
    """
    entity_name_for_lookup = payload.get(unique_name_field)
    
    if not entity_name_for_lookup:
        print(f"Creating {entity_type_name} (no unique name for pre-check)... Payload: {payload}")
    else:
        print(f"Attempting to create/retrieve {entity_type_name} '{entity_name_for_lookup}'...")
        existing_entity = find_entity_by_name(client, entity_api_path, entity_name_for_lookup)
        if existing_entity:
            print(f"Using existing {entity_type_name} '{entity_name_for_lookup}' with ID {existing_entity['id']}.")
            if isinstance(entity_name_for_lookup, str) and entity_name_for_lookup.startswith("Test E2E"):
                 if not any(e["id"] == existing_entity["id"] and e["type"] == entity_type_name for e in created_entities):
                    created_entities.append({"type": entity_type_name, "id": existing_entity["id"], "name": entity_name_for_lookup})
            return existing_entity

    print(f"Creating new {entity_type_name} with payload: {payload}")
    try:
        response = client.post(f"/{entity_api_path}/", json=payload)
        response.raise_for_status()
        created_entity_data = response.json()
        entity_id = created_entity_data.get("id")
        print(f"Successfully created {entity_type_name} '{entity_name_for_lookup}' with ID: {entity_id}.")
        
        if entity_id and (not entity_name_for_lookup or (isinstance(entity_name_for_lookup, str) and entity_name_for_lookup.startswith("Test E2E"))):
            created_entities.append({"type": entity_type_name, "id": entity_id, "name": entity_name_for_lookup})
        
        return created_entity_data
    except httpx.HTTPStatusError as e:
        error_message = f"Failed to create {entity_type_name} '{entity_name_for_lookup}'. Status: {e.response.status_code}. Response: {e.response.text}"
        print(f"ERROR: {error_message}")
        pytest.fail(error_message)
    except Exception as e:
        error_message = f"Exception during creation of {entity_type_name} '{entity_name_for_lookup}': {e}"
        print(f"ERROR: {error_message}")
        pytest.fail(error_message)

