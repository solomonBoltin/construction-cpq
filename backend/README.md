# Backend Service for CPQ Application

## Overview

This backend service handles the core logic for the Configure, Price, Quote (CPQ) application. It provides APIs for managing products, materials, quotes, and performs quote calculations. The application is built using Python with FastAPI and SQLModel.

## Project Structure

```
backend/
├── app/                  # Main application code
│   ├── api/              # API endpoint definitions
│   ├── services/         # Business logic (e.g., quote_calculator.py)
│   ├── __init__.py
│   ├── api_setup.py      # Main api router 
│   ├── config.py         # Application configuration
│   ├── database.py       # Database connection and session management
│   └── models.py         # SQLModel definitions for database tables
├── Dockerfile            # Dockerfile for building the backend service
├── main.py               # Entry point for running the application (uvicorn)
├── requirements.txt      # Python dependencies
├── seed.json             # Seed data for initial database setup
└── seed.py               # Script to populate the database with seed data
├── tests/                # Backend tests
│   ├── services/         # Tests for service layer logic
│   └── output/           # Output files from test runs (e.g., summaries)
```

## Conventions

### Running the Application (Docker)

The application is designed to be run using Docker and Docker Compose. The following conventions are used:

*   **Reset Environment**: To stop and remove all containers, networks, and volumes.
    ```bash
    docker-compose down -v
    ```
*   **Run Application & Tests**: To build and start all services (including the backend) in detached mode. This typically includes running end-to-end tests.
    ```bash
    docker-compose up --build -d
    ```
*   **Check Logs**: To view the logs for a specific service (e.g., the backend service, which might be named `backend` or `api` in `docker-compose.yml`).
    ```bash
    docker-compose logs <service_name_in_docker_compose_yml>
    ```
    For example, if the backend service is named `backend`:
    ```bash
    docker-compose logs backend
    ```
*   **Rerun End-to-End Tests**: To specifically rebuild and run the end-to-end test service.
    ```bash
    docker-compose up --build -d e2e
    ```

### Development

*   **Dependencies**: Python dependencies are managed in `requirements.txt`.
*   **Database Migrations**: Alembic is typically used for database migrations (though not explicitly shown in the provided structure, it's a common practice with FastAPI/SQLModel).
*   **Linting/Formatting**: Tools like Black and Flake8 are recommended for code formatting and linting.
*   **Testing**: Backend unit and integration tests are located in the `tests/` directory. Pytest is used as the test runner. Test summary outputs can be found in `tests/output/`.

### API

*   The API is documented using OpenAPI (Swagger), and the schema can usually be accessed at `/docs` or `/redoc` when the application is running.
*   API endpoints are organized into routers within the `app/api/` directory.

### Seeding Data

*   The `seed.py` script, along with `seed.json`, is used to populate the database with initial data. This is often run as part of the application startup or a separate setup step.

