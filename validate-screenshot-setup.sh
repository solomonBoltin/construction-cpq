#!/bin/bash

# Screenshot Setup Validation Script
# This script validates that all screenshot functionality is properly configured

set -e

echo "🔍 Validating Screenshot Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

echo
echo "📁 Checking file structure..."

# Check GitHub Actions workflows
if [ -d ".github/workflows" ]; then
    print_success "GitHub Actions workflows directory exists"
    
    workflows=("docker-compose-ci.yml" "screenshot-tests.yml" "screenshot-report.yml" "manual-screenshot-test.yml")
    for workflow in "${workflows[@]}"; do
        if [ -f ".github/workflows/$workflow" ]; then
            print_success "Workflow $workflow exists"
        else
            print_error "Workflow $workflow missing"
        fi
    done
else
    print_error "GitHub Actions workflows directory missing"
fi

# Check Docker Compose files
if [ -f "docker-compose.yml" ]; then
    print_success "Main docker-compose.yml exists"
else
    print_error "Main docker-compose.yml missing"
fi

if [ -f "docker-compose.ci.yml" ]; then
    print_success "CI override docker-compose.ci.yml exists"
else
    print_error "CI override docker-compose.ci.yml missing"
fi

# Check frontend structure
if [ -d "frontend" ]; then
    print_success "Frontend directory exists"
    
    if [ -f "frontend/package.json" ]; then
        print_success "Frontend package.json exists"
        
        # Check if Playwright is in package.json
        if grep -q "@playwright/test" frontend/package.json; then
            print_success "Playwright dependency found in package.json"
        else
            print_error "Playwright dependency missing from package.json"
        fi
        
        # Check if test script exists
        if grep -q "test:screenshots" frontend/package.json; then
            print_success "Screenshot test script found in package.json"
        else
            print_error "Screenshot test script missing from package.json"
        fi
    else
        print_error "Frontend package.json missing"
    fi
    
    if [ -f "frontend/playwright.config.ts" ]; then
        print_success "Playwright configuration exists"
    else
        print_error "Playwright configuration missing"
    fi
    
    if [ -d "frontend/tests/screenshots" ]; then
        print_success "Frontend screenshot tests directory exists"
        
        # Check for test files
        test_files=$(find frontend/tests/screenshots -name "*.spec.ts" 2>/dev/null | wc -l)
        if [ "$test_files" -gt 0 ]; then
            print_success "Found $test_files screenshot test files"
        else
            print_warning "No screenshot test files found"
        fi
    else
        print_error "Frontend screenshot tests directory missing"
    fi
else
    print_error "Frontend directory missing"
fi

# Check E2E tests structure
if [ -d "e2e_tests" ]; then
    print_success "E2E tests directory exists"
    
    if [ -f "e2e_tests/Dockerfile" ]; then
        print_success "E2E tests Dockerfile exists"
        
        # Check if Playwright is in Dockerfile
        if grep -q "playwright" e2e_tests/Dockerfile; then
            print_success "Playwright installation found in E2E Dockerfile"
        else
            print_error "Playwright installation missing from E2E Dockerfile"
        fi
    else
        print_error "E2E tests Dockerfile missing"
    fi
    
    if [ -f "e2e_tests/requirements.txt" ]; then
        print_success "E2E requirements.txt exists"
        
        # Check if playwright is in requirements
        if grep -q "playwright" e2e_tests/requirements.txt; then
            print_success "Playwright found in E2E requirements.txt"
        else
            print_error "Playwright missing from E2E requirements.txt"
        fi
    else
        print_error "E2E requirements.txt missing"
    fi
    
    if [ -f "e2e_tests/screenshot_helper.py" ]; then
        print_success "Screenshot helper module exists"
    else
        print_error "Screenshot helper module missing"
    fi
    
    if [ -f "e2e_tests/cpq_screenshot_e2e_test.py" ]; then
        print_success "E2E screenshot tests exist"
    else
        print_error "E2E screenshot tests missing"
    fi
else
    print_error "E2E tests directory missing"
fi

# Check documentation
if [ -f "SCREENSHOT_TESTING.md" ]; then
    print_success "Screenshot testing documentation exists"
else
    print_error "Screenshot testing documentation missing"
fi

# Check local testing script
if [ -f "run-screenshot-tests.sh" ]; then
    print_success "Local testing script exists"
    
    if [ -x "run-screenshot-tests.sh" ]; then
        print_success "Local testing script is executable"
    else
        print_warning "Local testing script is not executable (run: chmod +x run-screenshot-tests.sh)"
    fi
else
    print_error "Local testing script missing"
fi

# Check .gitignore
if [ -f ".gitignore" ]; then
    print_success ".gitignore exists"
    
    if grep -q "screenshots/" .gitignore; then
        print_success "Screenshot artifacts ignored in .gitignore"
    else
        print_warning "Screenshot artifacts not ignored in .gitignore"
    fi
else
    print_warning ".gitignore missing"
fi

echo
echo "🐳 Checking Docker setup..."

# Check if Docker is available
if command -v docker &> /dev/null; then
    print_success "Docker is available"
    
    # Check if Docker is running
    if docker ps &> /dev/null; then
        print_success "Docker is running"
    else
        print_warning "Docker is not running"
    fi
else
    print_error "Docker is not installed"
fi

# Check if network exists
if docker network ls | grep -q "traefik-network"; then
    print_success "Traefik network exists"
else
    print_warning "Traefik network not found (will be created when needed)"
fi

echo
echo "📋 Validation Summary:"
echo "   - Errors: $ERRORS"
echo "   - Warnings: $WARNINGS"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    print_success "All screenshot setup validation checks passed!"
elif [ $ERRORS -eq 0 ]; then
    print_warning "Screenshot setup validation passed with $WARNINGS warnings"
else
    print_error "Screenshot setup validation failed with $ERRORS errors and $WARNINGS warnings"
    exit 1
fi

echo
echo "🚀 Next steps:"
echo "   1. Run './run-screenshot-tests.sh' to test locally"
echo "   2. Push changes to trigger GitHub Actions workflows"
echo "   3. Check 'Actions' tab in GitHub for workflow results"
echo "   4. View PR comments for screenshot reports"

exit 0