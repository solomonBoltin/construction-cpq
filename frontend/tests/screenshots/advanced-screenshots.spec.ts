import { test, expect } from '@playwright/test';

test.describe('CPQ Application Advanced Screenshots', () => {
  test('Full application flow screenshots', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Take initial homepage screenshot
    await page.screenshot({ 
      path: 'screenshots/flow-01-homepage.png',
      fullPage: true 
    });
    
    // Test navigation if exists
    const navLinks = page.locator('nav a, [role="navigation"] a');
    const linkCount = await navLinks.count();
    
    if (linkCount > 0) {
      const firstLink = navLinks.first();
      await firstLink.click();
      await page.waitForLoadState('networkidle');
      
      await page.screenshot({ 
        path: 'screenshots/flow-02-navigation.png',
        fullPage: true 
      });
    }
    
    // Test form interactions if they exist
    const forms = page.locator('form');
    const formCount = await forms.count();
    
    if (formCount > 0) {
      await page.screenshot({ 
        path: 'screenshots/flow-03-forms.png',
        fullPage: true 
      });
    }
  });

  test('Component-specific screenshots', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Screenshot different components
    const components = [
      { selector: 'header', name: 'header' },
      { selector: 'nav', name: 'navigation' },
      { selector: 'main', name: 'main-content' },
      { selector: 'footer', name: 'footer' },
      { selector: '[data-testid]', name: 'test-components' }
    ];
    
    for (const component of components) {
      const element = page.locator(component.selector).first();
      if (await element.count() > 0) {
        await element.screenshot({ 
          path: `screenshots/component-${component.name}.png` 
        });
      }
    }
  });

  test('Loading states screenshots', async ({ page }) => {
    // Intercept requests to capture loading states
    await page.route('**/*', route => {
      // Delay responses by 1 second to capture loading states
      setTimeout(() => route.continue(), 1000);
    });
    
    await page.goto('/');
    
    // Take screenshot during loading
    await page.screenshot({ 
      path: 'screenshots/loading-state.png',
      fullPage: true 
    });
    
    // Wait for full load and take final screenshot
    await page.waitForLoadState('networkidle');
    await page.screenshot({ 
      path: 'screenshots/loaded-state.png',
      fullPage: true 
    });
  });

  test('Different page sizes screenshots', async ({ page }) => {
    const viewports = [
      { width: 320, height: 568, name: 'mobile-small' },
      { width: 375, height: 667, name: 'mobile-medium' },
      { width: 414, height: 896, name: 'mobile-large' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1024, height: 768, name: 'tablet-landscape' },
      { width: 1280, height: 720, name: 'desktop-small' },
      { width: 1920, height: 1080, name: 'desktop-large' }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      await page.screenshot({ 
        path: `screenshots/viewport-${viewport.name}.png`,
        fullPage: true 
      });
    }
  });

  test('Dark mode screenshots', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Try to enable dark mode if toggle exists
    const darkModeToggle = page.locator('[aria-label*="dark"], [data-theme="dark"], .dark-mode-toggle');
    if (await darkModeToggle.count() > 0) {
      await darkModeToggle.click();
      await page.waitForTimeout(1000);
      
      await page.screenshot({ 
        path: 'screenshots/dark-mode.png',
        fullPage: true 
      });
    }
    
    // Also test system dark mode preference
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    await page.screenshot({ 
      path: 'screenshots/system-dark-mode.png',
      fullPage: true 
    });
  });

  test('Accessibility screenshots', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Focus on interactive elements and screenshot
    const interactiveElements = page.locator('button, input, select, textarea, a');
    const count = await interactiveElements.count();
    
    if (count > 0) {
      const firstElement = interactiveElements.first();
      await firstElement.focus();
      
      await page.screenshot({ 
        path: 'screenshots/focus-state.png',
        fullPage: true 
      });
    }
    
    // Test high contrast mode
    await page.emulateMedia({ forcedColors: 'active' });
    await page.screenshot({ 
      path: 'screenshots/high-contrast.png',
      fullPage: true 
    });
  });
});