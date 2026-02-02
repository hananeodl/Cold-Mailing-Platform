"""
Database Connection and Configuration
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()


def init_db():
    """
    Initialize database tables
    Call this once when the application starts
    NOTE: db.init_app(app) should be called BEFORE this function
    """
    try:
        # Import models to register them with SQLAlchemy
        from app.models import (
            AccountManager,
            Customer,
            Search,
            Listing,
            Mailing,
            Appointment
        )

        # Create all tables
        db.create_all()

        print(" Database tables created successfully")

        # Print table names
        tables = db.metadata.tables.keys()
        print(f" Tables: {', '.join(tables)}")

    except Exception as e:
        print(f" Database initialization failed: {e}")
        raise


def get_db_session():
    """
    Get database session
    Returns the current SQLAlchemy session
    """
    return db.session


def drop_all_tables():
    """
    Drop all database tables
    WARNING: This will delete all data!
    """
    print("  WARNING: Dropping all tables...")
    db.drop_all()
    print(" All tables dropped")