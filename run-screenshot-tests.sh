#!/bin/bash

# Local Screenshot Testing Script
# This script sets up and runs screenshot tests locally

set -e

echo "🚀 Starting CPQ Screenshot Testing..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_step "Creating .env file..."
    cat > .env << 'EOF'
POSTGRES_USER=cpq_user
POSTGRES_PASSWORD=cpq_password
POSTGRES_DB=cpq_db
POSTGRES_PORT=5432
BACKEND_PORT=8000
FRONTEND_PORT=3000
NC_PORT=8080
NC_AUTH_JWT_SECRET=local_jwt_secret
NC_PUBLIC_URL=nocodb.localhost
NC_ADMIN_EMAIL=admin@local.com
NC_ADMIN_PASSWORD=admin_password
CPQ_PUBLIC_DOMAIN=cpq.localhost
BASE_TITLE=Base1
SOURCE_TITLE=Base1 PG Source
TRAEFIK_REPLICAS=0
TRAEFIK_LOG_LEVEL=INFO
EOF
fi

# Create network if it doesn't exist
print_step "Creating Docker network..."
docker network create traefik-network 2>/dev/null || print_warning "Network already exists"

# Clean up any existing containers
print_step "Cleaning up existing containers..."
docker compose -f docker-compose.yml -f docker-compose.ci.yml down -v 2>/dev/null || true

# Create screenshots directory
print_step "Creating screenshots directory..."
mkdir -p screenshots

# Build and start services
print_step "Building and starting services..."
docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d cpq_db backend frontend

# Wait for services to be ready
print_step "Waiting for services to be ready..."
sleep 30

# Check backend health
print_step "Checking backend health..."
timeout 60 bash -c 'until curl -f http://localhost:8000/health > /dev/null 2>&1; do echo "Waiting for backend..."; sleep 2; done' || {
    print_error "Backend health check failed"
    docker compose -f docker-compose.yml -f docker-compose.ci.yml logs backend
    exit 1
}

# Check frontend availability
print_step "Checking frontend availability..."
timeout 60 bash -c 'until curl -f http://localhost:3000 > /dev/null 2>&1; do echo "Waiting for frontend..."; sleep 2; done' || {
    print_error "Frontend availability check failed"
    docker compose -f docker-compose.yml -f docker-compose.ci.yml logs frontend
    exit 1
}

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    print_step "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Install Playwright if needed
if [ ! -d "frontend/node_modules/@playwright" ]; then
    print_step "Installing Playwright..."
    cd frontend
    npm install @playwright/test
    npx playwright install --with-deps
    cd ..
fi

# Run E2E tests with screenshots
print_step "Running E2E tests with screenshots..."
docker compose -f docker-compose.yml -f docker-compose.ci.yml up --build e2e_tests || {
    print_warning "E2E tests completed (may have failures)"
}

# Run Playwright screenshot tests
print_step "Running Playwright screenshot tests..."
cd frontend
npm run test:screenshots || {
    print_warning "Playwright tests completed (may have failures)"
}
cd ..

# Display results
print_step "Screenshot testing completed!"
echo
echo "📸 Screenshots generated:"
echo "   - E2E screenshots: screenshots/"
echo "   - Playwright screenshots: frontend/screenshots/"
echo "   - Test results: frontend/test-results/"
echo "   - Playwright report: frontend/playwright-report/"

# Count screenshots
e2e_count=$(find screenshots -name "*.png" 2>/dev/null | wc -l)
playwright_count=$(find frontend/screenshots -name "*.png" 2>/dev/null | wc -l)

echo
echo "📊 Summary:"
echo "   - E2E screenshots: $e2e_count"
echo "   - Playwright screenshots: $playwright_count"

# Cleanup option
read -p "🧹 Do you want to stop the services? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Stopping services..."
    docker compose -f docker-compose.yml -f docker-compose.ci.yml down -v
    docker network rm traefik-network 2>/dev/null || true
    print_step "Cleanup completed!"
else
    print_step "Services are still running. Use 'docker compose down' to stop them."
fi

echo
echo "✅ Screenshot testing script completed!"
echo "   View screenshots in the directories listed above."
echo "   For the Playwright HTML report, open frontend/playwright-report/index.html"