from sqlmodel import Session
from app.database import engine, create_db_and_tables
from seeders.seeder import run_all_seeders

def main():
    print("Starting database seeding process...")
    print("Ensuring database and tables are created...")
    create_db_and_tables()
    print("Database and tables ready.")

    with Session(engine) as session:
        run_all_seeders(session)
        session.commit() # Final commit for any pending changes from seeders

    print("Database seeding completed successfully!")

if __name__ == "__main__":
    main()
