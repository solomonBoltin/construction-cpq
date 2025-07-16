"""
E2E tests with screenshot capabilities for the CPQ application.
"""

import pytest
import asyncio
from screenshot_helper import ScreenshotHelper
from cpq_api_e2e import client

class TestScreenshotCapabilities:
    """Test class for screenshot functionality during E2E tests."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up screenshot helper for each test."""
        self.screenshot_helper = ScreenshotHelper()
    
    def test_homepage_screenshot(self, client):
        """Test taking a screenshot of the homepage."""
        
        # Take a basic screenshot of the homepage
        screenshot_path = asyncio.run(
            self.screenshot_helper.take_screenshot(
                page_path="/",
                filename="homepage_test.png"
            )
        )
        
        # Verify the screenshot was created
        import os
        assert os.path.exists(screenshot_path), "Screenshot file was not created"
        
        # Verify file size is reasonable (not empty)
        assert os.path.getsize(screenshot_path) > 1000, "Screenshot file is too small"
    
    def test_mobile_responsive_screenshot(self, client):
        """Test taking a mobile-responsive screenshot."""
        
        screenshot_path = asyncio.run(
            self.screenshot_helper.take_mobile_screenshot(
                page_path="/",
                filename="mobile_homepage_test.png"
            )
        )
        
        import os
        assert os.path.exists(screenshot_path), "Mobile screenshot file was not created"
        assert os.path.getsize(screenshot_path) > 1000, "Mobile screenshot file is too small"
    
    def test_tablet_responsive_screenshot(self, client):
        """Test taking a tablet-responsive screenshot."""
        
        screenshot_path = asyncio.run(
            self.screenshot_helper.take_tablet_screenshot(
                page_path="/",
                filename="tablet_homepage_test.png"
            )
        )
        
        import os
        assert os.path.exists(screenshot_path), "Tablet screenshot file was not created"
        assert os.path.getsize(screenshot_path) > 1000, "Tablet screenshot file is too small"
    
    def test_error_page_screenshot(self, client):
        """Test taking a screenshot of an error page."""
        
        screenshot_path = asyncio.run(
            self.screenshot_helper.take_screenshot(
                page_path="/non-existent-route",
                filename="error_page_test.png"
            )
        )
        
        import os
        assert os.path.exists(screenshot_path), "Error page screenshot file was not created"
        assert os.path.getsize(screenshot_path) > 1000, "Error page screenshot file is too small"
    
    def test_api_health_with_screenshot(self, client):
        """Test API health endpoint and take a screenshot if frontend is accessible."""
        
        # First, test the API health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        # Then take a screenshot to verify frontend is also working
        screenshot_path = asyncio.run(
            self.screenshot_helper.take_screenshot(
                page_path="/",
                filename="api_health_frontend_test.png"
            )
        )
        
        import os
        assert os.path.exists(screenshot_path), "API health screenshot file was not created"