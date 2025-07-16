# Screenshot Testing with Playwright

This project includes automated screenshot testing using Playwright to capture visual changes in the frontend application.

## 🚀 Features

- **Automated Screenshots**: Captures screenshots of key application pages and components
- **Multi-browser Support**: Tests across Chrome, Firefox, Safari, and mobile viewports
- **GitHub Actions Integration**: Runs on every push and pull request
- **Artifact Upload**: Screenshots and reports are uploaded as GitHub Actions artifacts
- **PR Comments**: Visual test results are automatically commented on pull requests

## 📋 Test Configuration

The screenshot tests are configured in:
- `frontend/playwright.config.ts` - Main Playwright configuration
- `frontend/tests/screenshot.spec.ts` - Screenshot test specifications

## 🔧 Running Tests Locally

### Prerequisites
```bash
cd frontend
npm install
```

### Install Playwright browsers
```bash
npx playwright install --with-deps
```

### Run tests
```bash
# Run all tests
npm run test

# Run tests in headed mode (see browser)
npm run test:headed

# Run tests with UI mode
npm run test:ui

# Debug tests
npm run test:debug
```

## 📊 GitHub Actions Workflows

### 1. Screenshot Tests (`screenshot-tests.yml`)
- Runs on push to main/master branches
- Captures screenshots and uploads as artifacts
- Provides basic screenshot testing

### 2. Visual Regression Tests (`visual-regression.yml`)
- Runs on pull requests
- Captures screenshots for visual comparison
- Comments on PR with links to artifacts
- Continues on test failures to ensure screenshots are always captured

## 📸 Screenshot Artifacts

After tests run, the following artifacts are available:
- **playwright-report**: HTML report with test results and screenshots
- **playwright-results**: Raw test results and failure screenshots
- **screenshots**: All captured screenshots

## 🎯 Test Structure

The screenshot tests capture:
1. **Homepage**: Full page screenshots on desktop and mobile
2. **Components**: Individual component screenshots
3. **Navigation**: Header and navigation element screenshots
4. **Multi-device**: Tests across different screen sizes and browsers

## 🔍 Viewing Results

1. Go to the GitHub Actions tab in your repository
2. Click on the workflow run
3. Download the artifacts to view screenshots and reports
4. For PR comments, check the pull request for automated visual test summaries

## 🛠️ Customization

### Adding New Screenshot Tests

Edit `frontend/tests/screenshot.spec.ts` to add new test cases:

```typescript
test('new component screenshot', async ({ page }) => {
  await page.goto('/your-route');
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveScreenshot('new-component.png');
});
```

### Modifying Browser Configuration

Edit `frontend/playwright.config.ts` to add or modify browser configurations:

```typescript
projects: [
  {
    name: 'custom-browser',
    use: { 
      ...devices['Desktop Chrome'],
      viewport: { width: 1920, height: 1080 }
    },
  },
]
```

## 📝 Best Practices

1. **Wait for Load States**: Always wait for `networkidle` or specific elements
2. **Stable Selectors**: Use stable CSS selectors for component screenshots
3. **Conditional Screenshots**: Check if elements exist before taking screenshots
4. **Meaningful Names**: Use descriptive names for screenshot files
5. **Mobile Testing**: Include mobile viewport tests for responsive design

## 🐛 Troubleshooting

- **Browser Installation Issues**: Ensure `npx playwright install --with-deps` runs successfully
- **Test Timeouts**: Increase timeout values in playwright.config.ts if needed
- **Screenshot Differences**: Use `npm run test:ui` to debug visual differences
- **Missing Elements**: Add proper wait conditions for dynamic content