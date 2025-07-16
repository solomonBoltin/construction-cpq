"""
Screenshot helper functions for E2E tests using Playwright.
"""

import os
import asyncio
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any

class ScreenshotHelper:
    """Helper class for taking screenshots during E2E tests."""
    
    def __init__(self, frontend_url: str = "http://frontend:80"):
        self.frontend_url = frontend_url
        self.screenshot_dir = "/app/screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    async def take_screenshot(self, 
                              page_path: str = "/",
                              filename: str = "screenshot.png",
                              full_page: bool = True,
                              viewport: Optional[Dict[str, int]] = None) -> str:
        """Take a screenshot of the specified page."""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport=viewport or {"width": 1280, "height": 720}
            )
            page = await context.new_page()
            
            try:
                # Navigate to the page
                await page.goto(f"{self.frontend_url}{page_path}")
                
                # Wait for the page to load
                await page.wait_for_load_state('networkidle')
                
                # Take screenshot
                screenshot_path = os.path.join(self.screenshot_dir, filename)
                await page.screenshot(path=screenshot_path, full_page=full_page)
                
                return screenshot_path
                
            finally:
                await browser.close()
    
    async def take_element_screenshot(self,
                                      page_path: str = "/",
                                      selector: str = "body",
                                      filename: str = "element_screenshot.png") -> str:
        """Take a screenshot of a specific element."""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(f"{self.frontend_url}{page_path}")
                await page.wait_for_load_state('networkidle')
                
                # Wait for element to be visible
                element = await page.wait_for_selector(selector, state='visible')
                
                # Take screenshot of the element
                screenshot_path = os.path.join(self.screenshot_dir, filename)
                await element.screenshot(path=screenshot_path)
                
                return screenshot_path
                
            finally:
                await browser.close()
    
    async def take_mobile_screenshot(self,
                                     page_path: str = "/",
                                     filename: str = "mobile_screenshot.png") -> str:
        """Take a mobile-responsive screenshot."""
        
        mobile_viewport = {"width": 375, "height": 667}
        return await self.take_screenshot(
            page_path=page_path,
            filename=filename,
            viewport=mobile_viewport
        )
    
    async def take_tablet_screenshot(self,
                                     page_path: str = "/",
                                     filename: str = "tablet_screenshot.png") -> str:
        """Take a tablet-responsive screenshot."""
        
        tablet_viewport = {"width": 768, "height": 1024}
        return await self.take_screenshot(
            page_path=page_path,
            filename=filename,
            viewport=tablet_viewport
        )

# Convenience function for synchronous usage
def take_screenshot_sync(page_path: str = "/",
                        filename: str = "screenshot.png",
                        full_page: bool = True) -> str:
    """Synchronous wrapper for taking screenshots."""
    
    helper = ScreenshotHelper()
    return asyncio.run(helper.take_screenshot(page_path, filename, full_page))