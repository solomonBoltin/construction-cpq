from sqlmodel import create_engine, Session, SQLModel # Ensure SQLModel is imported
from .config import settings

# The database URL is loaded from the .env file via settings
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True) # echo=True for logging SQL queries, can be removed in production

def get_session():
    with Session(engine) as session:
        yield session

# Function to create database tables (if they don't exist)
# This should be called once at application startup
# For a more robust solution, consider using Alembic for migrations
def create_db_and_tables():
    # Import all models here before calling SQLModel.metadata.create_all
    # This ensures they are registered with SQLModel
    from . import models # noqa
    SQLModel.metadata.create_all(engine)
