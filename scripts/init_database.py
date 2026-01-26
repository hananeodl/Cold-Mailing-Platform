# scripts/init_database.py
# !/usr/bin/env python3
"""
Database initialization script
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.database import db
from app.models import AccountManager, Customer, Search, Listing, Mailing, Appointment
from sqlalchemy import inspect, text


def init_database():
    """Initialize the database with test data"""
    app = create_app()

    with app.app_context():
        try:
            print("Checking the database connection...")
            db.session.execute(text('SELECT 1'))
            print(" Connection successful!")

            # Check which tables have been created
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"\n Tables in the database ({len(tables)}):")
            for table in sorted(tables):
                columns = inspector.get_columns(table)
                print(f"  - {table} ({len(columns)} columns)")

            # Count existing records
            print(f"\n Current statistics:")
            print(f"   - Account Managers: {AccountManager.query.count()}")
            print(f"   - Customers: {Customer.query.count()}")
            print(f"   - Listings: {Listing.query.count()}")
            print(f"   - Mailings: {Mailing.query.count()}")
            print(f"   - Appointments: {Appointment.query.count()}")

            print("\n" + "=" * 60)
            print(" VERIFICATION SUCCESSFULLY COMPLETED!")

        except Exception as e:
            print(f"\n ERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    print(" EXTRA IMMOBILIEN DATABASE VERIFICATION")
    print("=" * 60)
    init_database()