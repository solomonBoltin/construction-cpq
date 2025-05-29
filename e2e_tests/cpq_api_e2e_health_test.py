"""
Tests for API health check.
"""
import httpx
from .cpq_api_e2e import client # Import client fixture

def test_health_check(client: httpx.Client):
    """Tests the API health check endpoint."""
    print("Test: Checking API health...")
    health_check_url = client.base_url.copy_with(path="/health")
    response = client.get(health_check_url)
    assert response.status_code == 200, f"Health check failed at {health_check_url}: {response.status_code} - {response.text}"
    assert response.json() == {"status": "ok"}, f"Health check response body mismatch at {health_check_url}: {response.json()}"
    print(f"API health check successful at {health_check_url}.")
