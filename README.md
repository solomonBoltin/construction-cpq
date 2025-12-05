# Construction CPQ (Configure, Price, Quote)

A production-ready solution for instant quotes for construction projects, specifically designed for fence installation businesses.

## 🏗️ Project Overview

This application provides a complete Configure-Price-Quote (CPQ) system that enables construction businesses to:
- Create and manage project quotes
- Configure products with multiple variations
- Calculate detailed pricing including materials, labor, taxes, and margins
- Generate professional PDF quotes
- Manage the complete quote lifecycle from draft to finalization

## 🏛️ Architecture

The system consists of three main components:

### Backend (Python/FastAPI)
- **Framework**: FastAPI with SQLModel ORM
- **Database**: PostgreSQL
- **Features**: RESTful API, quote calculation engine, data seeding
- **Location**: `/backend`

### Frontend (React/TypeScript)
- **Framework**: React 19 with TypeScript
- **State Management**: Zustand
- **Routing**: React Router v7
- **Data Fetching**: TanStack Query
- **Location**: `/frontend`

### Database Management (NocoDB)
- **Tool**: NocoDB for visual database management
- **Purpose**: Admin interface for data management
- **Location**: Configured in `docker-compose.yml`

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/solomonBoltin/construction-cpq.git
   cd construction-cpq
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   # Reset environment (remove existing containers and volumes)
   docker-compose down -v
   
   # Build and start all services
   docker-compose up --build -d
   ```

4. **Access the services**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - NocoDB: http://localhost:8081

### Running Tests

#### Backend Tests
```bash
# Run all backend tests
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest tests/services/test_quote_calculator.py

# Run with coverage
docker-compose exec backend pytest --cov=app tests/
```

#### End-to-End Tests
```bash
# Run E2E tests
docker-compose up --build -d e2e_tests

# Check E2E test logs
docker-compose logs e2e_tests
```

#### Frontend Tests
```bash
cd frontend
npm install
npm test
```

## 📁 Project Structure

```
construction-cpq/
├── backend/                 # FastAPI backend service
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models.py       # Database models
│   │   └── config.py       # Configuration
│   ├── tests/              # Backend tests
│   ├── data/               # Seed data
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend application
│   ├── components/         # React components
│   ├── services/           # API client services
│   ├── stores/             # Zustand state stores
│   └── utils/              # Utility functions
├── e2e_tests/              # End-to-end tests
├── nocodb_base_setup/      # NocoDB configuration
└── docker-compose.yml      # Docker services configuration
```

## 🔧 Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Run development server
uvicorn main:app --reload --port 8000

# Run linting
black app/ tests/
flake8 app/ tests/

# Run tests
pytest tests/ -v
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🧪 Testing Strategy

### Backend Tests
- **Unit Tests**: Located in `backend/tests/`
- **Service Tests**: Quote calculation, business logic
- **Model Tests**: Database model validation
- **Coverage Goal**: >80%

### E2E Tests
- **Location**: `e2e_tests/`
- **Framework**: pytest with httpx
- **Scope**: Full API workflow testing

### Frontend Tests
- **Framework**: Vitest (recommended) or Jest
- **Component Tests**: React component testing
- **Integration Tests**: User workflow testing

## 📊 Database

### Schema
The application uses PostgreSQL with the following main entities:
- `Product`: Product catalog with categories
- `Variation`: Product variations and options
- `Material`: Materials used in products
- `Quote`: Customer quotes
- `QuoteItem`: Items in quotes with configurations

### Seeding Data
```bash
# Reset and seed database
docker-compose exec backend python seed.py
```

## 🔐 Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
POSTGRES_USER=cpq_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=cpq_db
POSTGRES_PORT=5432

# Backend
BACKEND_PORT=8000

# Frontend
FRONTEND_PORT=3000

# NocoDB
NC_PORT=8081
NC_AUTH_JWT_SECRET=your_jwt_secret
NC_ADMIN_EMAIL=admin@example.com
NC_ADMIN_PASSWORD=admin_password

# Domain Configuration
CPQ_PUBLIC_DOMAIN=cpq.example.com
```

## 🚢 Deployment

### Production Deployment

1. **Configure environment variables** for production
2. **Set up external Traefik** (set `TRAEFIK_REPLICAS=0` in `.env`)
3. **Configure SSL certificates** in `./certs` directory
4. **Run production build**:
   ```bash
   docker-compose up -d --build
   ```

### Docker Services
- **cpq_db**: PostgreSQL database
- **backend**: FastAPI application
- **frontend**: React application (nginx)
- **cpq_nocodb_app**: NocoDB admin interface
- **nocodb_base_setup**: NocoDB initialization
- **cpq_traefik**: Reverse proxy (optional)

## 📝 API Documentation

When the backend is running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- **Backend**: Follow PEP 8, use Black for formatting
- **Frontend**: Use Prettier and ESLint
- **Commits**: Use conventional commit messages

## 📋 Open Issues & Roadmap

See the [Issues](https://github.com/solomonBoltin/construction-cpq/issues) page for current bugs and feature requests.

### Current Open Items
- Issue #1: Make material unit type optional
- PR #3: CPQ document PDF generation
- PR #4: Frontend API connectivity fixes
- PR #5: Screenshot testing with Playwright
- PR #6: Comprehensive screenshot workflows

## 🐛 Troubleshooting

### Common Issues

**Database connection errors**
```bash
# Check database is running
docker-compose ps cpq_db

# Check database logs
docker-compose logs cpq_db

# Reset database
docker-compose down -v
docker-compose up -d cpq_db
```

**Backend not starting**
```bash
# Check backend logs
docker-compose logs backend

# Rebuild backend
docker-compose up --build backend
```

**Frontend not connecting to backend**
```bash
# Verify proxy configuration in frontend/vite.config.ts
# Ensure backend is accessible at http://localhost:8000
```

## 📄 License

This project is private and proprietary.

## 👥 Authors

- Solomon Boltin - Initial work

## 🙏 Acknowledgments

- FastAPI framework
- React and the React team
- NocoDB for database management
- PostgreSQL community
