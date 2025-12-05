# Architecture Documentation

## System Overview

The Construction CPQ (Configure, Price, Quote) system is a full-stack web application designed to streamline the quote generation process for construction projects, specifically fence installations.

## Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **ORM:** SQLModel (built on SQLAlchemy + Pydantic)
- **Database:** PostgreSQL 15
- **Validation:** Pydantic v2
- **Testing:** pytest, httpx
- **Server:** Uvicorn (ASGI)

### Frontend
- **Framework:** React 19
- **Language:** TypeScript 5.7
- **Build Tool:** Vite 6
- **State:** Zustand
- **Data Fetching:** TanStack Query v5
- **Routing:** React Router v7

### Infrastructure
- **Containerization:** Docker, Docker Compose
- **Reverse Proxy:** Traefik (optional)
- **Database Admin:** NocoDB

---

Last Updated: 2025-12-05
