# Screenshot Testing and Reporting

This document explains the screenshot testing and reporting functionality implemented in the CPQ application.

## Overview

The CPQ application includes automated screenshot testing that captures visual states of the application across different devices and scenarios. Screenshots are automatically generated during CI/CD pipeline runs and made available as artifacts.

## Features

### 1. Multi-Device Screenshots
- **Desktop**: Full-page and viewport screenshots
- **Mobile**: Responsive screenshots at 375x667 resolution
- **Tablet**: Responsive screenshots at 768x1024 resolution
- **Cross-Browser**: Chromium, Firefox, and Safari (WebKit) support

### 2. Automated Testing
- **E2E Integration**: Screenshots taken during end-to-end tests
- **Playwright Tests**: Dedicated screenshot test suite
- **Error State Capture**: Automatic screenshots when tests fail

### 3. CI/CD Integration
- **GitHub Actions**: Automated screenshot generation on PR/push
- **Artifact Upload**: Screenshots uploaded and accessible via GitHub Actions
- **PR Comments**: Automatic comments with screenshot reports

## File Structure

```
├── .github/
│   └── workflows/
│       ├── docker-compose-ci.yml      # Basic CI workflow
│       ├── screenshot-tests.yml        # Screenshot testing workflow
│       └── screenshot-report.yml       # Screenshot reporting workflow
├── frontend/
│   ├── playwright.config.ts           # Playwright configuration
│   └── tests/
│       └── screenshots/
│           └── basic-screenshots.spec.ts  # Screenshot test suite
├── e2e_tests/
│   ├── screenshot_helper.py           # Python screenshot utilities
│   └── cpq_screenshot_e2e_test.py     # E2E screenshot tests
├── docker-compose.yml                 # Main Docker Compose configuration
└── docker-compose.ci.yml              # CI overrides
```

## Usage

### Running Screenshot Tests Locally

1. **Start the application**:
   ```bash
   docker network create traefik-network
   docker compose up -d cpq_db backend frontend
   ```

2. **Run Playwright screenshot tests**:
   ```bash
   cd frontend
   npm install
   npx playwright install --with-deps
   npm run test:screenshots
   ```

3. **Run E2E tests with screenshots**:
   ```bash
   docker compose up --build e2e_tests
   ```

### GitHub Actions Workflows

#### 1. Basic CI (`docker-compose-ci.yml`)
- Triggered on push/PR to main/develop branches
- Runs basic Docker Compose setup and E2E tests
- Validates application functionality

#### 2. Screenshot Tests (`screenshot-tests.yml`)
- Runs Playwright screenshot tests
- Uploads screenshots as artifacts
- Supports multiple browsers and devices

#### 3. Screenshot Report (`screenshot-report.yml`)
- Comprehensive screenshot testing on PRs
- Automatically comments on PRs with screenshot reports
- Provides links to download artifacts

## Screenshot Types

### 1. Basic Screenshots
- **Homepage**: Full-page and viewport screenshots
- **Navigation**: Screenshots of navigation elements
- **Content Areas**: Main content sections
- **Error Pages**: 404 and error states

### 2. Responsive Screenshots
- **Mobile View**: Portrait mobile layout
- **Tablet View**: Tablet-optimized layout
- **Desktop View**: Full desktop experience

### 3. Test-Driven Screenshots
- **API Integration**: Screenshots after API calls
- **User Flows**: Screenshots during user interactions
- **Error Scenarios**: Screenshots when tests fail

## Configuration

### Playwright Configuration (`playwright.config.ts`)
```typescript
export default defineConfig({
  testDir: './tests/screenshots',
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },
  ],
});
```

### Docker Compose CI Override (`docker-compose.ci.yml`)
- Disables unnecessary services (Traefik, NocoDb)
- Enables E2E tests with screenshot mounting
- Optimized for CI/CD environments

## Accessing Screenshots

### 1. From GitHub Actions
1. Navigate to the **Actions** tab
2. Select the workflow run
3. Download artifacts:
   - `screenshots-{run_number}`: E2E test screenshots
   - `playwright-report-{run_number}`: Playwright test results

### 2. From PR Comments
- Automatic comments provide direct links to artifacts
- Summary of available screenshots
- Instructions for downloading and viewing

### 3. Local Development
- Screenshots saved to:
  - `frontend/screenshots/`: Playwright screenshots
  - `screenshots/`: E2E test screenshots
  - `frontend/test-results/`: Test failure screenshots

## Best Practices

### 1. Screenshot Naming
- Use descriptive filenames: `homepage_desktop.png`
- Include device type: `mobile_navigation.png`
- Add test context: `api_health_frontend_test.png`

### 2. Test Organization
- Group related screenshots in test classes
- Use fixtures for common setup
- Handle async operations properly

### 3. CI/CD Optimization
- Use `continue-on-error: true` for non-critical tests
- Implement proper cleanup procedures
- Set appropriate artifact retention periods

## Troubleshooting

### Common Issues

1. **Screenshots not generated**:
   - Verify services are running and healthy
   - Check network connectivity between containers
   - Ensure proper wait conditions

2. **Artifacts not uploaded**:
   - Check GitHub Actions permissions
   - Verify file paths in upload actions
   - Ensure files exist before upload

3. **PR comments not posting**:
   - Verify `pull-requests: write` permission
   - Check GitHub token authentication
   - Validate comment script syntax

### Debug Commands

```bash
# Check service health
docker compose ps

# View logs
docker compose logs backend
docker compose logs frontend

# Test manual screenshot
cd frontend
npx playwright test --headed --debug

# Verify E2E test environment
docker compose exec e2e_tests pytest -v --tb=short
```

## Future Enhancements

1. **Visual Regression Testing**: Compare screenshots across commits
2. **Performance Monitoring**: Capture loading times with screenshots
3. **Accessibility Testing**: Screenshots with accessibility overlays
4. **Custom Viewports**: Support for additional device sizes
5. **Screenshot Optimization**: Automatic compression and formatting