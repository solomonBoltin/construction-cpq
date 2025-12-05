# Contributing to Construction CPQ

Thank you for your interest in contributing to the Construction CPQ project! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/YOUR_USERNAME/construction-cpq.git
   cd construction-cpq
   ```
3. **Set up the development environment** (see [Development Setup](#development-setup))
4. **Create a branch** for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📋 Development Setup

### Prerequisites
- Docker and Docker Compose
- Git
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Local Environment

1. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

2. **Start development environment**
   ```bash
   docker compose down -v
   docker compose up --build -d
   ```

3. **Verify setup**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Database: localhost:5432

## 💻 Development Workflow

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run linting
black app/ tests/
flake8 app/ tests/

# Run type checking
mypy app/ --ignore-missing-imports
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

# Type checking
npx tsc --noEmit
```

## 🧪 Testing

### Running Tests

**Backend Tests:**
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/services/test_quote_calculator.py -v

# With coverage
pytest tests/ --cov=app --cov-report=term
```

**E2E Tests:**
```bash
docker compose up --build e2e_tests
docker compose logs e2e_tests
```

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage
- Follow existing test patterns
- Use descriptive test names

## 📝 Code Style

### Python (Backend)

- Follow [PEP 8](https://pep8.org/) guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [Flake8](https://flake8.pycqa.org/) for linting
- Use type hints where applicable
- Maximum line length: 127 characters

**Example:**
```python
from typing import Optional
from fastapi import APIRouter, HTTPException

def calculate_quote(
    product_id: int,
    quantity: float,
    variations: Optional[dict] = None
) -> dict:
    """Calculate quote for a product.
    
    Args:
        product_id: The ID of the product
        quantity: Quantity to quote
        variations: Optional product variations
        
    Returns:
        Dictionary containing quote details
    """
    # Implementation
    pass
```

### TypeScript (Frontend)

- Use TypeScript for all new code
- Follow React best practices
- Use functional components with hooks
- Prefer named exports over default exports

**Example:**
```typescript
import { useState, useEffect } from 'react';
import type { Quote } from '../types';

interface QuoteItemProps {
  quote: Quote;
  onSelect: (id: number) => void;
}

export function QuoteItem({ quote, onSelect }: QuoteItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div onClick={() => onSelect(quote.id)}>
      {/* Component content */}
    </div>
  );
}
```

## 🔀 Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features
3. **Ensure all tests pass** locally
4. **Update the CHANGELOG** (if applicable)
5. **Create a Pull Request** with a clear description

### PR Title Format
Use conventional commit format:
```
type(scope): description

Examples:
feat(backend): add quote export functionality
fix(frontend): resolve quote calculation error
docs: update API documentation
test(e2e): add project creation tests
```

### PR Description Template
```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No new warnings generated
```

## 🐛 Bug Reports

### Before Submitting
- Check existing issues to avoid duplicates
- Verify the bug exists in the latest version
- Collect relevant information

### Bug Report Template
```markdown
**Description:**
Clear description of the bug

**To Reproduce:**
1. Step 1
2. Step 2
3. ...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]
- Version: [e.g., v1.0.0]

**Screenshots:**
If applicable

**Additional Context:**
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template
```markdown
**Problem Statement:**
Describe the problem this feature would solve

**Proposed Solution:**
Describe your proposed solution

**Alternatives Considered:**
Other solutions you've considered

**Additional Context:**
Any other relevant information
```

## 🏗️ Architecture Guidelines

### Backend
- Follow RESTful API design principles
- Use SQLModel for database models
- Implement business logic in service layer
- Keep controllers thin
- Use dependency injection

### Frontend
- Component-based architecture
- Zustand for state management
- TanStack Query for server state
- Separate concerns (UI, logic, data)

## 📊 Database Changes

### Migrations
If your changes require database modifications:

1. Create migration script
2. Test migration up and down
3. Document schema changes
4. Update seed data if needed

## 🔐 Security

- **Never commit secrets** or credentials
- **Use environment variables** for configuration
- **Validate all inputs** on backend
- **Sanitize user inputs** to prevent XSS
- **Report security issues** privately to maintainers

## 📞 Communication

- **GitHub Issues:** Bug reports and feature requests
- **Pull Requests:** Code contributions and discussions
- **Discussions:** General questions and ideas

## 🎯 Good First Issues

Look for issues labeled `good first issue` for beginner-friendly contributions.

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## 🙏 Recognition

Contributors will be recognized in the project README and release notes.

---

Thank you for contributing to Construction CPQ! 🎉
