from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_database(app):
    """Initialize database with app"""
    db.init_app(app)

    # Create all tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            print(" Database tables created successfully!")

            # Check what tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f" Tables in database: {tables}")

        except Exception as e:
            print(f" Error creating tables: {e}")
            raise