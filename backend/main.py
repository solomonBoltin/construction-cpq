from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from sqlmodel import Session

from app.database import create_db_and_tables, engine 
# Import your API routers here when they are created, e.g.:
from app.api_setup import router as api_router
from app.config import settings
from seeders.seeder import run_all_seeders, should_seed


# Set up logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

# Add a test log message to verify logging
logger.debug("Logging configuration in main.py is working correctly.")

origins = [
    "http://localhost:3000",  # Allow your frontend origin
    "http://localhost:8080",  # Add other origins if needed
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Creating database and tables...")
    create_db_and_tables()
    print("Database and tables created.")

    if should_seed():
        print("Seeding database...")
        with Session(engine) as session:
            run_all_seeders(session)
            # No explicit commit here, as individual seeders commit after each type
            # or _get_or_create handles commit/rollback.
            # A final commit in seed.py's main is for script-based execution.
        print("Database seeding completed.")
    else:
        print("Skipping database seeding based on environment variables.")
    
    yield
    # Code to run on shutdown (if any)
    print("Application shutting down...")

app = FastAPI(
    title="Construction CPQ API",
    description="API for managing construction quotes, products, materials, and variations.",
    version="0.1.0",
    lifespan=lifespan
)

async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        # you probably want some kind of logging here
        return Response("Internal server error", status_code=500)


app.middleware('http')(catch_exceptions_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins for CORS todo - restrict this in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

# Include your API routers here
app.include_router(api_router, prefix="/api/v1") # Prefix all these routes with /api/v1

# For running directly with uvicorn for development (though Docker is preferred for deployment)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_PORT)
