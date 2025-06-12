from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Add this import
from contextlib import asynccontextmanager
import logging

from app.database import create_db_and_tables
# Import your API routers here when they are created, e.g.:
from app.api_setup import router as api_router # Import the router from api.py
from app.config import settings  # Import settings for configuration


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
    # if want to seed here, should make seed seed only if not exists
    # from seed import main
    # main()  # Call the seed function to populate initial data
    yield
    # Code to run on shutdown (if any)
    print("Application shutting down...")

app = FastAPI(
    title="Construction CPQ API",
    description="API for managing construction quotes, products, materials, and variations.",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
