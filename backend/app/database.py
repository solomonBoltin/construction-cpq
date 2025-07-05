from sqlmodel import create_engine, Session, SQLModel # Ensure SQLModel is imported
from .config import settings
from sqlalchemy import text

# The database URL is loaded from the .env file via settings
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True) # echo=True for logging SQL queries, can be removed in production

def get_session():
    with Session(engine) as session:
        yield session

# Function to run basic migrations
def run_migrations():
    """Run basic database migrations."""
    with Session(engine) as session:
        try:
            # Migration 1: Make material.unit_type_id optional (nullable) and set default
            # Check if the column exists and is not nullable
            result = session.exec(text("""
                SELECT column_name, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'material' AND column_name = 'unit_type_id'
            """)).first()
            
            if result and result.is_nullable == 'NO':
                print("Running migration: Making material.unit_type_id nullable...")
                session.exec(text("ALTER TABLE material ALTER COLUMN unit_type_id DROP NOT NULL"))
                session.commit()
                print("Migration completed: material.unit_type_id is now nullable")
            elif result:
                print("Migration already applied: material.unit_type_id is already nullable")
            else:
                print("No migration needed: material.unit_type_id column does not exist yet")
            
            # Migration 2: Set default value for unit_type_id
            if result and (result.column_default is None or '1' not in str(result.column_default)):
                print("Running migration: Setting default value for material.unit_type_id...")
                session.exec(text("ALTER TABLE material ALTER COLUMN unit_type_id SET DEFAULT 1"))
                session.commit()
                print("Migration completed: material.unit_type_id default set to 1")
            elif result and result.column_default:
                print("Migration already applied: material.unit_type_id already has a default value")
                
        except Exception as e:
            print(f"Migration error: {e}")
            session.rollback()

# Function to create database tables (if they don't exist)
# This should be called once at application startup
# For a more robust solution, consider using Alembic for migrations
def create_db_and_tables():
    # Import all models here before calling SQLModel.metadata.create_all
    # This ensures they are registered with SQLModel
    from . import models # noqa
    
    # Run migrations first
    run_migrations()
    
    # Create tables
    SQLModel.metadata.create_all(engine)
