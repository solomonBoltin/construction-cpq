import { test, expect } from '@playwright/test';

test.describe('CPQ Application Screenshot Tests', () => {
  test('homepage screenshot', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Take a full page screenshot
    await expect(page).toHaveScreenshot('homepage.png');
  });

  test('homepage mobile screenshot', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Take a full page screenshot
    await expect(page).toHaveScreenshot('homepage-mobile.png');
  });

  test('application components screenshot', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Take screenshots of specific components if they exist
    const mainContent = page.locator('main, #root, .app');
    if (await mainContent.count() > 0) {
      await expect(mainContent.first()).toHaveScreenshot('main-content.png');
    }
    
    // Take a full page screenshot as fallback
    await expect(page).toHaveScreenshot('application-full.png');
  });

  test('navigation elements screenshot', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check for navigation elements
    const nav = page.locator('nav, .navbar, .navigation');
    if (await nav.count() > 0) {
      await expect(nav.first()).toHaveScreenshot('navigation.png');
    }
    
    // Check for header elements
    const header = page.locator('header, .header');
    if (await header.count() > 0) {
      await expect(header.first()).toHaveScreenshot('header.png');
    }
  });
});